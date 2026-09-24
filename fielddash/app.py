"""Streamlit script used by `fielddash run`.

    fielddash run project.yaml        # single project
    fielddash run dir/                # choose between .yaml projects in sidebar

To deploy (e.g. Streamlit Community Cloud), use `fielddash.dashboard(...)`
in your project's script.
"""
import argparse
import os

from fielddash.web import dashboard

ENV_CONFIG = "FIELDDASH_CONFIG"


def _config_arg() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    args, _ = parser.parse_known_args()
    return args.config or os.environ.get(ENV_CONFIG) or os.environ.get("GEOCOLETA_CONFIG") or "."


dashboard(_config_arg())
