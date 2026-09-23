import json

from core.registry import source
from sources.base import DataSource


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@source("json")
class JsonFileSource(DataSource):
    """Dados e schema salvos em disco (útil offline e para testes).

    fonte:
      tipo: json
      dados: ../dados.json          # {"data": [...]} ou export da API {"data": {"entries": [...]}}
      schema: ../formulario.json
    """

    def fetch_schema(self):
        return _read(self.config.resolve(self.options["schema"]))

    def fetch_entries(self):
        data = _read(self.config.resolve(self.options["dados"]))
        data = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(data, dict):
            data = data.get("entries", [])
        return data
