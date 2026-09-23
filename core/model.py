from dataclasses import dataclass, field as dc_field

import pandas as pd

# Agrupamento dos tipos do Epicollect5 pelo tratamento que recebem no dashboard
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
    system: bool = False  # campos do Epicollect (created_at, created_by...)
    question: str = ""    # texto original da pergunta (usado para casar colunas)

    @property
    def kind(self) -> str:
        """Categoria usada pela UI: categorical, multi, numeric, date, location, text, media ou other."""
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
        """Busca um campo por alias, ref (completo ou sufixo), coluna ou texto da pergunta."""
        found = self.find(key)
        if found is None:
            raise KeyError(f"Campo não encontrado: {key!r}")
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
                raise KeyError(f"Campo ambíguo: {key!r} ({', '.join(f.column for f in hits)})")
        return None

    def of_kind(self, *kinds) -> list:
        return [f for f in self.fields if f.kind in kinds]
