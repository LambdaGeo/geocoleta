"""Lista os campos de um projeto para ajudar a escrever a config.

Uso: python tools/listar_campos.py projetos/residuos.yaml
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import load_config  # noqa: E402
from core.loader import bootstrap, load_dataset  # noqa: E402


def main(path):
    bootstrap()
    dataset = load_dataset(load_config(path))
    print(f"{dataset.title}: {len(dataset.df)} respostas\n")
    print(f"{'ref (final)':<14}{'apelido':<20}{'tipo':<12}{'coluna':<22}pergunta")
    for f in dataset.fields:
        print(f"{f.ref[-6:]:<14}{f.alias or '':<20}{f.type:<12}{f.column:<22}{f.label[:70]}")
    for warning in dataset.warnings:
        print(f"⚠ {warning}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
