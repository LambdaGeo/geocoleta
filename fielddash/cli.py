"""Command line interface for fielddash.

    fielddash run project.yaml [streamlit options, e.g. --server.port 8600]
    fielddash run dir/                   # select project in sidebar
    fielddash fields project.yaml        # inspect form fields to write config
"""
import argparse
import subprocess
import sys
from pathlib import Path

from fielddash.core.config import load_config
from fielddash.core.loader import bootstrap, load_dataset

APP = Path(__file__).resolve().parent / "app.py"


def run(target: str, streamlit_args: list) -> int:
    path = Path(target).resolve()
    if not path.exists():
        sys.exit(f"Not found: {path}")
    command = [sys.executable, "-m", "streamlit", "run", str(APP), *streamlit_args, "--", "--config", str(path)]
    return subprocess.call(command)


def fields(target: str) -> int:
    config = load_config(target)
    bootstrap(config)
    dataset = load_dataset(config)
    print(f"{dataset.title}: {len(dataset.df)} responses\n")
    print(f"{'ref (suffix)':<14}{'alias':<20}{'type':<12}{'column':<22}question")
    for f in dataset.fields:
        ref = f.ref if f.system else f.ref[-6:]
        print(f"{ref:<14}{f.alias or '':<20}{f.type:<12}{f.column:<22}{f.label[:70]}")
    for warning in dataset.warnings:
        print(f"⚠ {warning}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="fielddash", description="Schema-driven dashboards for field data collection.")
    commands = parser.add_subparsers(dest="command", required=True)

    run_parser = commands.add_parser("run", help="launch dashboard for a project (.yaml) or project directory")
    run_parser.add_argument("project", nargs="?", default=".")

    fields_parser = commands.add_parser("fields", aliases=["campos"], help="list form fields for a project")
    fields_parser.add_argument("project")

    args, extra = parser.parse_known_args(argv)
    if args.command == "run":
        return run(args.project, extra)
    if extra:
        parser.error(f"unrecognized arguments: {' '.join(extra)}")
    try:
        return fields(args.project)
    except (OSError, KeyError, ValueError, RuntimeError) as error:
        sys.exit(f"fielddash: {error}")


if __name__ == "__main__":
    sys.exit(main())
