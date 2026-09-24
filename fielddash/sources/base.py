from abc import ABC, abstractmethod

import pandas as pd

from fielddash.core.config import Config
from fielddash.core.model import Dataset
from fielddash.core.normalize import normalize
from fielddash.core.schema import parse_form, reconcile


class DataSource(ABC):
    """A data source yields the form schema and raw entries; everything else is shared."""

    def __init__(self, config: Config):
        self.config = config
        self.options = config.source

    @abstractmethod
    def fetch_schema(self) -> dict:
        """JSON form schema or Epicollect project export."""

    @abstractmethod
    def fetch_entries(self) -> list:
        """List of responses (dicts matching Epicollect JSON export format)."""

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
    fields = parse_form(schema, config.source.get("form_ref"))
    df = pd.DataFrame(entries)
    fields, warnings = reconcile(fields, df.columns)

    dataset = Dataset(df=df, fields=fields, title=config.title, warnings=warnings)
    for alias, key in config.fields.items():
        found = dataset.find(key)
        if found is None:
            warnings.append(f"Alias '{alias}': field {key!r} not found")
        else:
            found.alias = alias

    for key, kind in config.types.items():
        found = dataset.find(key)
        if found is None:
            warnings.append(f"Type for '{key}': field not found")
        else:
            found.type = kind

    dataset.fields = [f for f in fields if not _matches(f, config.ignore)]
    dataset.df = normalize(df, dataset.fields, config.timezone)
    return dataset
