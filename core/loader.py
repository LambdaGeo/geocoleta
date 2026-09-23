import importlib
import pkgutil
from pathlib import Path

from dotenv import load_dotenv

from core.config import Config
from core.model import Dataset
from core.registry import SOURCE_REGISTRY

ROOT = Path(__file__).resolve().parents[1]


def bootstrap():
    """Carrega o .env (pasta do framework ou do repositório) e registra fontes e páginas."""
    for env in (ROOT / ".env", ROOT.parent / ".env"):
        if env.exists():
            load_dotenv(env)
    for package in ("sources", "views"):
        module = importlib.import_module(package)
        for info in pkgutil.iter_modules(module.__path__):
            importlib.import_module(f"{package}.{info.name}")


def load_dataset(config: Config) -> Dataset:
    kind = config.fonte["tipo"]
    if kind not in SOURCE_REGISTRY:
        raise ValueError(f"Fonte desconhecida: {kind!r} (disponíveis: {', '.join(SOURCE_REGISTRY)})")
    return SOURCE_REGISTRY[kind](config).load()
