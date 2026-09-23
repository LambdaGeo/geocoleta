import hashlib
import json
import os
import time
from pathlib import Path

import requests

from geocoleta.core.registry import source
from geocoleta.sources.base import DataSource

API = "https://five.epicollect.net/api"
PER_PAGE = 1000
TIMEOUT = 60

# Tokens valem ~2h; o Epicollect limita pedidos de token (erro 429), então eles são
# reaproveitados entre execuções num arquivo só do usuário, indexado por hash do client_id.
TOKEN_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "geocoleta" / "tokens.json"
RATE_LIMIT_MSG = ("o Epicollect limitou as requisições (muitos acessos seguidos). "
                  "Aguarde alguns minutos antes de recarregar: novas tentativas prolongam o bloqueio")
BACKOFF_SECONDS = 300  # após um 429, não tenta de novo antes disso (cada recarga da página tentaria)

_tokens = {}         # hash do client_id -> (token, expira_em)
_blocked_until = {}  # hash do client_id -> instante em que pode tentar de novo


class EpicollectError(RuntimeError):
    pass


def _read_cache() -> dict:
    try:
        return json.loads(TOKEN_CACHE.read_text())
    except (OSError, ValueError):
        return {}


def _write_cache(key: str, token: str, expires: float):
    try:
        cache = {k: v for k, v in _read_cache().items() if v[1] > time.time()}
        cache[key] = [token, expires]
        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_CACHE.touch(mode=0o600, exist_ok=True)
        TOKEN_CACHE.write_text(json.dumps(cache))
    except OSError:
        pass  # sem cache em disco, o token continua valendo em memória


def get_token(prefix: str) -> str | None:
    """Token OAuth (client credentials). Sem credenciais, acessa como projeto público."""
    if not prefix:
        return None
    client_id = os.environ.get(f"{prefix}_CLIENT_ID")
    client_secret = os.environ.get(f"{prefix}_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise EpicollectError(f"Defina {prefix}_CLIENT_ID e {prefix}_CLIENT_SECRET no .env")

    key = hashlib.sha256(client_id.encode()).hexdigest()[:16]
    for cached in (_tokens.get(key), _read_cache().get(key)):
        if cached and time.time() < cached[1] - 60:
            _tokens[key] = tuple(cached)
            return cached[0]

    wait = _blocked_until.get(key, 0) - time.time()
    if wait > 0:
        raise EpicollectError(f"Falha na autenticação: {RATE_LIMIT_MSG} (nova tentativa em {wait / 60:.0f} min)")

    response = requests.post(f"{API}/oauth/token", timeout=TIMEOUT, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })
    if response.status_code == 429:
        _blocked_until[key] = time.time() + BACKOFF_SECONDS
        raise EpicollectError(f"Falha na autenticação: {RATE_LIMIT_MSG}")
    if response.status_code != 200:
        raise EpicollectError(f"Falha na autenticação ({response.status_code}): {_error_text(response)}")
    data = response.json()
    expires = time.time() + data.get("expires_in", 7200)
    _tokens[key] = (data["access_token"], expires)
    _write_cache(key, data["access_token"], expires)
    return data["access_token"]


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
            raise EpicollectError(f"Erro da API: {RATE_LIMIT_MSG}")
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
