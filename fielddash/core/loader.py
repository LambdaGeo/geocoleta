import importlib
import importlib.util
import pkgutil
import sys
from pathlib import Path

from fielddash.core.config import Config
from fielddash.core.model import Dataset
from fielddash.core.registry import SOURCE_REGISTRY

_loaded_extensions = set()


def bootstrap(config: Config | None = None):
    """Registers sources and views from the package, and project extensions if config is given."""
    for package in ("fielddash.sources", "fielddash.views"):
        module = importlib.import_module(package)
        for info in pkgutil.iter_modules(module.__path__):
            importlib.import_module(f"{package}.{info.name}")

    if config is not None:
        for entry in config.extensions:
            path = config.resolve(entry)
            for file in (sorted(path.glob("*.py")) if path.is_dir() else [path]):
                _load_extension(file)


def _load_extension(file: Path):
    """Imports a project module (e.g. project-specific @page) once."""
    file = file.resolve()
    if file in _loaded_extensions or file.name.startswith("_"):
        return
    if not file.exists():
        raise FileNotFoundError(f"Extension not found: {file}")
    name = f"fielddash_ext.{file.stem}"
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _loaded_extensions.add(file)


def load_dataset(config: Config) -> Dataset:
    kind = config.source.get("type") or config.source.get("tipo")
    if kind not in SOURCE_REGISTRY:
        raise ValueError(f"Unknown data source: {kind!r} (available: {', '.join(SOURCE_REGISTRY)})")
    return SOURCE_REGISTRY[kind](config).load()
