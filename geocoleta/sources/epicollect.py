import json
import os
import time

import requests

from geocoleta.core.registry import source
from geocoleta.sources.base import DataSource

API = "https://five.epicollect.net/api"
PER_PAGE = 1000
TIMEOUT = 60

_tokens = {}  # prefixo das credenciais -> (token, expira_em)


class EpicollectError(RuntimeError):
    pass


def get_token(prefix: str) -> str | None:
    """Token OAuth (client credentials). Sem credenciais, acessa como projeto público."""
    if not prefix:
        return None
    cached = _tokens.get(prefix)
    if cached and time.time() < cached[1] - 60:
        return cached[0]

    client_id = os.environ.get(f"{prefix}_CLIENT_ID")
    client_secret = os.environ.get(f"{prefix}_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise EpicollectError(f"Defina {prefix}_CLIENT_ID e {prefix}_CLIENT_SECRET no .env")

    response = requests.post(f"{API}/oauth/token", timeout=TIMEOUT, data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })
    if response.status_code != 200:
        raise EpicollectError(f"Falha na autenticação ({response.status_code}): {_error_text(response)}")
    data = response.json()
    _tokens[prefix] = (data["access_token"], time.time() + data.get("expires_in", 7200))
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
