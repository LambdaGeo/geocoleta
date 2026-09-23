import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_ENV = re.compile(r"\$\{([A-Za-z0-9_]+)\}")


def _expand(value):
    if isinstance(value, str):
        def replace(match):
            name = match.group(1)
            if name not in os.environ:
                raise KeyError(f"Variável de ambiente não definida: {name}")
            return os.environ[name]
        return _ENV.sub(replace, value)
    if isinstance(value, list):
        return [_expand(v) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    return value


@dataclass
class Config:
    path: Path
    titulo: str
    fonte: dict
    subtitulo: str = ""
    campos: dict = field(default_factory=dict)      # apelido -> ref / coluna / pergunta
    ignorar: list = field(default_factory=list)
    tipos: dict = field(default_factory=dict)       # campo -> tipo forçado (ex.: bairro: category)
    filtros: list = field(default_factory=list)
    destaques: list = field(default_factory=list)
    secoes: list = field(default_factory=list)
    mapa: dict = field(default_factory=dict)
    extensoes: list = field(default_factory=list)   # .py ou pastas com páginas/fontes do projeto
    fuso: str = "America/Fortaleza"
    cache_minutos: int = 5

    @property
    def base_dir(self) -> Path:
        return self.path.parent

    def resolve(self, relative: str) -> Path:
        return (self.base_dir / relative).resolve()


def load_config(path) -> Config:
    path = Path(path).resolve()
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # ${VAR} só é expandido na fonte, onde ficam credenciais e ids do projeto
    raw["fonte"] = _expand(raw.get("fonte") or {})
    if "tipo" not in raw["fonte"]:
        raise ValueError(f"{path.name}: 'fonte.tipo' é obrigatório")

    known = Config.__dataclass_fields__.keys() - {"path"}
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"{path.name}: chaves desconhecidas: {', '.join(sorted(unknown))}")

    raw.setdefault("titulo", path.stem)
    return Config(path=path, **{k: v for k, v in raw.items() if v is not None})
