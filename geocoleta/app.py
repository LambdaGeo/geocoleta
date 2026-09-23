"""Script Streamlit usado por `geocoleta run`.

    geocoleta run projeto.yaml        # um projeto
    geocoleta run pasta/              # escolhe entre os .yaml da pasta na barra lateral

Para publicar (ex.: Streamlit Community Cloud), use `geocoleta.dashboard(...)`
num script do próprio projeto.
"""
import argparse
import os

from geocoleta.web import dashboard

ENV_CONFIG = "GEOCOLETA_CONFIG"


def _config_arg() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    args, _ = parser.parse_known_args()
    return args.config or os.environ.get(ENV_CONFIG) or "."


dashboard(_config_arg())
