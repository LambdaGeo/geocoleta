import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path

from dotenv import load_dotenv

from geocoleta.core.config import Config
from geocoleta.core.model import Dataset
from geocoleta.core.registry import SOURCE_REGISTRY

_loaded_extensions = set()


def bootstrap(config: Config | None = None):
    """Registra fontes e páginas do pacote e carrega o .env.

    O .env é procurado no diretório atual e na pasta do arquivo de config;
    com config, também importa as `extensoes` do projeto (arquivos .py ou pastas).
    """
    load_dotenv(Path.cwd() / ".env")
    if config is not None:
        load_dotenv(config.base_dir / ".env")

    for package in ("geocoleta.sources", "geocoleta.views"):
        module = importlib.import_module(package)
        for info in pkgutil.iter_modules(module.__path__):
            importlib.import_module(f"{package}.{info.name}")

    if config is not None:
        for entry in config.extensoes:
            path = config.resolve(entry)
            for file in (sorted(path.glob("*.py")) if path.is_dir() else [path]):
                _load_extension(file)


def _load_extension(file: Path):
    """Importa um módulo do projeto (ex.: páginas @page específicas) uma única vez."""
    file = file.resolve()
    if file in _loaded_extensions or file.name.startswith("_"):
        return
    if not file.exists():
        raise FileNotFoundError(f"Extensão não encontrada: {file}")
    name = f"geocoleta_ext.{file.stem}"
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _loaded_extensions.add(file)


def load_dataset(config: Config) -> Dataset:
    kind = config.fonte["tipo"]
    if kind not in SOURCE_REGISTRY:
        raise ValueError(f"Fonte desconhecida: {kind!r} (disponíveis: {', '.join(SOURCE_REGISTRY)})")
    return SOURCE_REGISTRY[kind](config).load()
