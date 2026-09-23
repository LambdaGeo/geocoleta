from abc import ABC, abstractmethod

import pandas as pd

from core.config import Config
from core.model import Dataset
from core.normalize import normalize
from core.schema import parse_form, reconcile


class DataSource(ABC):
    """Uma fonte entrega o schema do formulário e as respostas; o resto é comum."""

    def __init__(self, config: Config):
        self.config = config
        self.options = config.fonte

    @abstractmethod
    def fetch_schema(self) -> dict:
        """JSON do formulário ou do projeto Epicollect."""

    @abstractmethod
    def fetch_entries(self) -> list:
        """Lista de respostas (dicts no formato do export JSON do Epicollect)."""

    def load(self) -> Dataset:
        return build_dataset(self.config, self.fetch_schema(), self.fetch_entries())


def _matches(field, keys) -> bool:
    for key in keys:
        key = str(key).strip()
        if key in (field.alias, field.ref, field.column) or field.label.lower() == key.lower():
            return True
        if len(key) >= 6 and field.ref.endswith(key):
            return True
    return False


def build_dataset(config: Config, schema: dict, entries: list) -> Dataset:
    fields = parse_form(schema, config.fonte.get("form_ref"))
    df = pd.DataFrame(entries)
    fields, warnings = reconcile(fields, df.columns)

    dataset = Dataset(df=df, fields=fields, title=config.titulo, warnings=warnings)
    for alias, key in config.campos.items():
        found = dataset.find(key)
        if found is None:
            warnings.append(f"Apelido '{alias}': campo {key!r} não encontrado")
        else:
            found.alias = alias

    for key, kind in config.tipos.items():
        found = dataset.find(key)
        if found is None:
            warnings.append(f"Tipo para '{key}': campo não encontrado")
        else:
            found.type = kind

    dataset.fields = [f for f in fields if not _matches(f, config.ignorar)]
    dataset.df = normalize(df, dataset.fields, config.fuso)
    return dataset
