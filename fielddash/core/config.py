import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

from fielddash.core.env import getenv

_ENV = re.compile(r"\$\{([A-Za-z0-9_]+)\}")


def _expand(value):
    if isinstance(value, str):
        def replace(match):
            name = match.group(1)
            value = getenv(name)
            if value is None:
                raise KeyError(f"Variable not defined in .env or Streamlit secrets: {name}")
            return value
        return _ENV.sub(replace, value)
    if isinstance(value, list):
        return [_expand(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    return value


KEY_MAP = {
    "titulo": "title",
    "subtitulo": "subtitle",
    "fonte": "source",
    "campos": "fields",
    "ignorar": "ignore",
    "tipos": "types",
    "filtros": "filters",
    "destaques": "highlights",
    "secoes": "sections",
    "mapa": "map",
    "extensoes": "extensions",
    "fuso": "timezone",
    "cache_minutos": "cache_minutes",
}

SOURCE_KEY_MAP = {
    "tipo": "type",
    "projeto": "project",
    "credenciais": "credentials",
    "dados": "data",
}


@dataclass
class Config:
    path: Path
    title: str
    source: dict
    subtitle: str = ""
    fields: dict = field(default_factory=dict)       # alias -> ref / column / question
    ignore: list = field(default_factory=list)
    types: dict = field(default_factory=dict)        # field -> forced type (e.g. neighborhood: category)
    filters: list = field(default_factory=list)
    highlights: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    map: dict = field(default_factory=dict)
    extensions: list = field(default_factory=list)   # .py files or directories with project pages/sources
    timezone: str = "America/Fortaleza"
    cache_minutes: int = 5

    # Portuguese property aliases for backwards compatibility
    @property
    def titulo(self) -> str:
        return self.title

    @property
    def subtitulo(self) -> str:
        return self.subtitle

    @property
    def fonte(self) -> dict:
        return self.source

    @property
    def campos(self) -> dict:
        return self.fields

    @property
    def ignorar(self) -> list:
        return self.ignore

    @property
    def tipos(self) -> dict:
        return self.types

    @property
    def filtros(self) -> list:
        return self.filters

    @property
    def destaques(self) -> list:
        return self.highlights

    @property
    def secoes(self) -> list:
        return self.sections

    @property
    def mapa(self) -> dict:
        return self.map

    @property
    def extensoes(self) -> list:
        return self.extensions

    @property
    def fuso(self) -> str:
        return self.timezone

    @property
    def cache_minutos(self) -> int:
        return self.cache_minutes

    @property
    def base_dir(self) -> Path:
        return self.path.parent

    def resolve(self, relative: str) -> Path:
        return (self.base_dir / relative).resolve()


def load_config(path) -> Config:
    path = Path(path).resolve()
    # .env in current directory and in project directory
    load_dotenv(Path.cwd() / ".env")
    load_dotenv(path.parent / ".env")
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # Normalize Portuguese keys to English
    normalized = {}
    for k, v in raw.items():
        canonical = KEY_MAP.get(k, k)
        normalized[canonical] = v

    normalized["source"] = _expand(normalized.get("source") or {})
    src = {}
    for sk, sv in normalized["source"].items():
        src[SOURCE_KEY_MAP.get(sk, sk)] = sv
        src[sk] = sv
    normalized["source"] = src

    if "type" not in normalized["source"] and "tipo" not in normalized["source"]:
        raise ValueError(f"{path.name}: 'source.type' (or 'fonte.tipo') is required")

    known = Config.__dataclass_fields__.keys() - {"path"}
    unknown = set(normalized) - known
    if unknown:
        raise ValueError(f"{path.name}: unknown keys: {', '.join(sorted(unknown))}")

    normalized.setdefault("title", path.stem)
    return Config(path=path, **{k: v for k, v in normalized.items() if v is not None})
