from dataclasses import dataclass, field as dc_field

import pandas as pd

# Grouping of Epicollect5 types by how they are handled in the dashboard
CATEGORICAL = {"radio", "dropdown", "searchsingle", "category"}
MULTI = {"checkbox", "searchmultiple"}
NUMERIC = {"integer", "decimal"}
DATE = {"date", "datetime"}
LOCATION = {"location"}
TEXT = {"text", "textarea", "phone", "barcode", "time"}
MEDIA = {"photo", "audio", "video"}


@dataclass
class Field:
    ref: str
    column: str
    label: str
    type: str
    options: list = dc_field(default_factory=list)
    group: str | None = None
    alias: str | None = None
    system: bool = False  # Epicollect system fields (created_at, created_by...)
    question: str = ""    # original question text (used to match columns)

    @property
    def kind(self) -> str:
        """Category used by the UI: categorical, multi, numeric, date, location, text, media or other."""
        for kind, types in (
            ("categorical", CATEGORICAL),
            ("multi", MULTI),
            ("numeric", NUMERIC),
            ("date", DATE),
            ("location", LOCATION),
            ("text", TEXT),
            ("media", MEDIA),
        ):
            if self.type in types:
                return kind
        return "other"

    @property
    def lat(self) -> str:
        return f"{self.column}__lat"

    @property
    def lon(self) -> str:
        return f"{self.column}__lon"


@dataclass
class Dataset:
    df: pd.DataFrame
    fields: list
    title: str = ""
    warnings: list = dc_field(default_factory=list)

    def field(self, key: str) -> Field:
        """Looks up a field by alias, ref (full or suffix), column, or question text."""
        found = self.find(key)
        if found is None:
            raise KeyError(f"Field not found: {key!r}")
        return found

    def find(self, key: str) -> Field | None:
        key = str(key).strip()
        lowered = key.lower()
        matchers = (
            lambda f: f.alias == key,
            lambda f: f.ref == key or f.column == key,
            lambda f: f.label.strip().lower() == lowered,
            lambda f: len(key) >= 6 and f.ref.endswith(key),
        )
        for match in matchers:
            hits = [f for f in self.fields if match(f)]
            if len(hits) == 1:
                return hits[0]
            if len(hits) > 1:
                raise KeyError(f"Ambiguous field: {key!r} ({', '.join(f.column for f in hits)})")
        return None

    def of_kind(self, *kinds) -> list:
        return [f for f in self.fields if f.kind in kinds]
