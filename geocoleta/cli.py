"""Linha de comando do geocoleta.

    geocoleta run projeto.yaml [opções do streamlit, ex.: --server.port 8600]
    geocoleta run pasta/                 # escolhe o projeto na barra lateral
    geocoleta campos projeto.yaml        # lista os campos para escrever a config
"""
import argparse
import subprocess
import sys
from pathlib import Path

from geocoleta.core.config import load_config
from geocoleta.core.loader import bootstrap, load_dataset

APP = Path(__file__).resolve().parent / "app.py"


def run(target: str, streamlit_args: list) -> int:
    path = Path(target).resolve()
    if not path.exists():
        sys.exit(f"Não encontrado: {path}")
    command = [sys.executable, "-m", "streamlit", "run", str(APP), *streamlit_args, "--", "--config", str(path)]
    return subprocess.call(command)


def fields(target: str) -> int:
    config = load_config(target)
    bootstrap(config)
    dataset = load_dataset(config)
    print(f"{dataset.title}: {len(dataset.df)} respostas\n")
    print(f"{'ref (final)':<14}{'apelido':<20}{'tipo':<12}{'coluna':<22}pergunta")
    for f in dataset.fields:
        ref = f.ref if f.system else f.ref[-6:]
        print(f"{ref:<14}{f.alias or '':<20}{f.type:<12}{f.column:<22}{f.label[:70]}")
    for warning in dataset.warnings:
        print(f"⚠ {warning}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="geocoleta", description="Dashboards para dados de coleta de campo.")
    commands = parser.add_subparsers(dest="command", required=True)

    run_parser = commands.add_parser("run", help="abre o dashboard de um projeto (.yaml) ou de uma pasta de projetos")
    run_parser.add_argument("projeto", nargs="?", default=".")
    fields_parser = commands.add_parser("campos", help="lista os campos do formulário de um projeto")
    fields_parser.add_argument("projeto")

    args, extra = parser.parse_known_args(argv)
    if args.command == "run":
        return run(args.projeto, extra)
    if extra:
        parser.error(f"argumentos não reconhecidos: {' '.join(extra)}")
    return fields(args.projeto)


if __name__ == "__main__":
    sys.exit(main())
