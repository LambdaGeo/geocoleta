import hashlib
import json
import os
import time
from pathlib import Path

import requests

from geocoleta.core.env import getenv
from geocoleta.core.registry import source
from geocoleta.sources.base import DataSource

API = "https://five.epicollect.net/api"
PER_PAGE = 1000
TIMEOUT = 60

# Tokens valem ~2h e o Epicollect permite poucos pedidos de token por IP (erro 429 com
# Retry-After). Tokens e o fim de um bloqueio ficam num arquivo só do usuário, para que
# reiniciar o app ou recarregar a página não gere novos pedidos. Chaves: hash do client_id.
TOKEN_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "geocoleta" / "tokens.json"
RATE_LIMIT_MSG = "o Epicollect limitou os pedidos de acesso desta máquina (muitos acessos seguidos)"
DEFAULT_BACKOFF = 900  # sem Retry-After na resposta

_tokens = {}  # hash do client_id -> (token, expira_em)
_blocked = {"until": 0.0}


class EpicollectError(RuntimeError):
    pass


def _read_cache() -> dict:
    try:
        data = json.loads(TOKEN_CACHE.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_cache(update):
    try:
        cache = _read_cache()
        tokens = {k: v for k, v in cache.get("tokens", {}).items() if v[1] > time.time()}
        cache = update({"tokens": tokens, "bloqueado_ate": cache.get("bloqueado_ate", 0)})
        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE.touch(mode=0o600, exist_ok=True)
        TOKEN_CACHE.write_text(json.dumps(cache))
    except OSError:
        pass  # sem cache em disco, tudo continua valendo em memória


def _blocked_until() -> float:
    return max(_blocked["until"], float(_read_cache().get("bloqueado_ate", 0)))


def _block(response):
    try:
        seconds = int(response.headers.get("Retry-After", DEFAULT_BACKOFF))
    except (TypeError, ValueError):
        seconds = DEFAULT_BACKOFF
    until = time.time() + seconds
    _blocked["until"] = until

    def update(cache):
        cache["bloqueado_ate"] = until
        return cache

    _write_cache(update)
    return until


def _rate_limit_error(until: float) -> "EpicollectError":
    when = time.strftime("%H:%M", time.localtime(until))
    return EpicollectError(f"Falha na autenticação: {RATE_LIMIT_MSG}. Liberação prevista às {when}; "
                           "até lá o geocoleta não tenta de novo (novas tentativas prolongariam o bloqueio).")


def get_token(prefix: str) -> str | None:
    """Token OAuth (client credentials). Sem credenciais, acessa como projeto público."""
    if not prefix:
        return None
    client_id = getenv(f"{prefix}_CLIENT_ID")
    client_secret = getenv(f"{prefix}_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise EpicollectError(f"Defina {prefix}_CLIENT_ID e {prefix}_CLIENT_SECRET no .env (ou nos secrets do Streamlit)")

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
        raise EpicollectError(f"Falha na autenticação ({response.status_code}): {_error_text(response)}")
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
    """Dados direto da API do Epicollect5, com schema atualizado a cada carga.

    fonte:
      tipo: epicollect
      projeto: ${PROJECT_RESIDUOS}     # slug do projeto
      form_ref: ${FORM_RESIDUOS_REF}   # opcional (padrão: primeiro formulário)
      credenciais: RESIDUOS            # usa RESIDUOS_CLIENT_ID / RESIDUOS_CLIENT_SECRET
      schema: ../form.json             # opcional: schema local se a API do projeto falhar
    """

    def _get(self, url, params=None):
        token = get_token(self.options.get("credenciais"))
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
        if response.status_code == 429:
            raise EpicollectError(f"Erro da API: o Epicollect limitou as requisições; tente mais tarde "
                                  f"(Retry-After: {response.headers.get('Retry-After', '?')} s)")
        if response.status_code != 200:
            raise EpicollectError(f"Erro da API Epicollect ({response.status_code}): {_error_text(response)}")
        return response.json()

    def fetch_schema(self):
        try:
            return self._get(f"{API}/export/project/{self.options['projeto']}")
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
            data = self._get(f"{API}/export/entries/{self.options['projeto']}", params)
            entries.extend(data["data"]["entries"])
            meta = data.get("meta", {})
            if params["page"] >= int(meta.get("last_page") or 1):
                return entries
            params["page"] += 1
