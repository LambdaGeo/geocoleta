import json

from fielddash.core.registry import source
from fielddash.sources.base import DataSource


def _read(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@source("json")
class JsonFileSource(DataSource):
    """Data and schema saved on disk (useful offline and for testing).

    source:
      type: json
      data: ../dados.json          # {"data": [...]} or API export {"data": {"entries": [...]}}
      schema: ../formulario.json
    """

    def fetch_schema(self):
        return _read(self.config.resolve(self.options["schema"]))

    def fetch_entries(self):
        target = self.options.get("data") or self.options.get("dados")
        if not target:
            raise KeyError("JSON source requires 'data' (or 'dados') path")
        data = _read(self.config.resolve(target))
        data = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(data, dict):
            data = data.get("entries", [])
        return data
