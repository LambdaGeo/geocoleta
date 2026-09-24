import hashlib
import json
import os
import time
from pathlib import Path

import requests

from fielddash.core.env import getenv
from fielddash.core.registry import source
from fielddash.sources.base import DataSource

API = "https://five.epicollect.net/api"
PER_PAGE = 1000
TIMEOUT = 60

# Tokens are valid for ~2h and Epicollect limits token requests per IP (429 Retry-After).
# Tokens and active blocks are stored in a user-only file so app restarts don't spam the API.
_cache_dir = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "fielddash"
TOKEN_CACHE = _cache_dir / "tokens.json"
RATE_LIMIT_MSG = "Epicollect rate-limited authentication requests from this IP (too many attempts)"
DEFAULT_BACKOFF = 900  # when no Retry-After in response

_tokens = {}  # sha256(client_id)[:16] -> (token, expires_at)
_blocked = {"until": 0.0}


class EpicollectError(RuntimeError):
    pass


def _read_cache() -> dict:
    try:
        if not TOKEN_CACHE.exists():
            # Check legacy geocoleta cache location if present
            legacy = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "geocoleta" / "tokens.json"
            if legacy.exists():
                return json.loads(legacy.read_text())
        data = json.loads(TOKEN_CACHE.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_cache(update):
    try:
        cache = _read_cache()
        tokens = {k: v for k, v in cache.get("tokens", {}).items() if v[1] > time.time()}
        cache = update({"tokens": tokens, "blocked_until": cache.get("blocked_until") or cache.get("bloqueado_ate", 0)})
        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE.touch(mode=0o600, exist_ok=True)
        TOKEN_CACHE.write_text(json.dumps(cache))
    except OSError:
        pass


def _blocked_until() -> float:
    cache = _read_cache()
    cached_val = cache.get("blocked_until") or cache.get("bloqueado_ate", 0)
    return max(_blocked["until"], float(cached_val))


def _block(response):
    try:
        seconds = int(response.headers.get("Retry-After", DEFAULT_BACKOFF))
    except (TypeError, ValueError):
        seconds = DEFAULT_BACKOFF
    until = time.time() + seconds
    _blocked["until"] = until

    def update(cache):
        cache["blocked_until"] = until
        return cache

    _write_cache(update)
    return until


def _rate_limit_error(until: float) -> "EpicollectError":
    when = time.strftime("%H:%M", time.localtime(until))
    return EpicollectError(f"Authentication failed: {RATE_LIMIT_MSG}. Retry allowed at {when}; "
                           "fielddash will not attempt requests until then to avoid extending the block.")


def get_token(prefix: str) -> str | None:
    """OAuth client credentials token. Without credentials, accesses project as public."""
    if not prefix:
        return None
    client_id = getenv(f"{prefix}_CLIENT_ID")
    client_secret = getenv(f"{prefix}_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise EpicollectError(f"Set {prefix}_CLIENT_ID and {prefix}_CLIENT_SECRET in .env (or Streamlit secrets)")

    key = hashlib.sha256(client_id.encode()).hexdigest()[:16]
    for cached in (_tokens.get(key), _read_cache().get("tokens", {}).get(key)):
        if cached and time.time() < cached[1] - 60:
            _tokens[key] = tuple(cached)
            return cached[0]

    until = _blocked_until()
    if until > time.time():
        raise _rate_limit_error(until)

    response = requests.post(f"{API}/oauth/token", timeout=TIMEOUT, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })
    if response.status_code == 429:
        raise _rate_limit_error(_block(response))
    if response.status_code != 200:
        raise EpicollectError(f"Authentication failed ({response.status_code}): {_error_text(response)}")
    data = response.json()
    token, expires = data["access_token"], time.time() + data.get("expires_in", 7200)
    _tokens[key] = (token, expires)

    def update(cache):
        cache["tokens"][key] = [token, expires]
        return cache

    _write_cache(update)
    return token


def _error_text(response) -> str:
    try:
        errors = response.json().get("errors") or []
        if errors:
            e = errors[0]
            return f"{e.get('code', '')} {e.get('title', '')}".strip()
    except ValueError:
        pass
    return response.text[:200]


@source("epicollect")
class EpicollectSource(DataSource):
    """Data fetched directly from Epicollect5 API, updating schema on reload.

    source:
      type: epicollect
      project: ${PROJECT_RESIDUOS}     # project slug
      form_ref: ${FORM_RESIDUOS_REF}   # optional (default: first form)
      credentials: RESIDUOS            # uses RESIDUOS_CLIENT_ID / RESIDUOS_CLIENT_SECRET
      schema: ../form.json             # optional: local schema fallback if project API fails
    """

    @property
    def project(self) -> str:
        proj = self.options.get("project") or self.options.get("projeto")
        if not proj:
            raise KeyError("Epicollect source requires 'project' (or 'projeto')")
        return proj

    def _get(self, url, params=None, max_retries: int = 2):
        creds = self.options.get("credentials") or self.options.get("credenciais")
        token = get_token(creds)
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        for attempt in range(max_retries + 1):
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            if response.status_code == 429:
                try:
                    retry_after = int(response.headers.get("Retry-After", 20))
                except (TypeError, ValueError):
                    retry_after = 20

                if attempt < max_retries and retry_after <= 60:
                    time.sleep(retry_after + 1)
                    continue

                raise EpicollectError(
                    f"API error: Epicollect rate limit exceeded; retry later (Retry-After: {retry_after} s)"
                )
            if response.status_code != 200:
                raise EpicollectError(f"Epicollect API error ({response.status_code}): {_error_text(response)}")
            return response.json()

    def fetch_schema(self):
        try:
            return self._get(f"{API}/export/project/{self.project}")
        except (EpicollectError, requests.RequestException):
            if "schema" not in self.options:
                raise
            with open(self.config.resolve(self.options["schema"]), encoding="utf-8") as f:
                return json.load(f)

    def fetch_entries(self):
        params = {"per_page": PER_PAGE, "page": 1}
        if self.options.get("form_ref"):
            params["form_ref"] = self.options["form_ref"]

        entries = []
        while True:
            data = self._get(f"{API}/export/entries/{self.project}", params)
            entries.extend(data["data"]["entries"])
            meta = data.get("meta", {})
            if params["page"] >= int(meta.get("last_page") or 1):
                return entries
            params["page"] += 1
            time.sleep(0.3)  # brief pause between paginated requests to respect rate limits
