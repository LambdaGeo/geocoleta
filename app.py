"""Dashboard genérico para formulários Epicollect5.

    streamlit run myframework/app.py                                  # escolhe o projeto na barra lateral
    streamlit run myframework/app.py -- --config projetos/residuos.yaml
    DASH_CONFIG=projetos/residuos.yaml streamlit run myframework/app.py
"""
import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from core.config import load_config  # noqa: E402
from core.context import PageContext  # noqa: E402
from core.loader import bootstrap, load_dataset  # noqa: E402
from core.registry import ordered_pages  # noqa: E402
from ui.filters import render_filters  # noqa: E402

PROJECTS = ROOT / "projetos"


def _config_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    args, _ = parser.parse_known_args()
    return args.config or os.environ.get("DASH_CONFIG")


def _resolve(path):
    path = Path(path)
    return path if path.is_absolute() or path.exists() else ROOT / path


@st.cache_data(show_spinner="Carregando dados…")
def _cached_dataset(config_path: str, mtime: float, bucket: int):
    # mtime invalida o cache quando a config muda; bucket, a cada `cache_minutos`
    return load_dataset(load_config(config_path))


def main():
    st.set_page_config(page_title="Dashboard de campo", page_icon="📊", layout="wide")
    bootstrap()

    fixed = _config_arg()
    if fixed:
        config_path = _resolve(fixed)
    else:
        options = sorted(PROJECTS.glob("*.yaml"))
        if not options:
            st.error(f"Nenhum projeto em {PROJECTS}")
            return
        config_path = st.sidebar.selectbox("Projeto", options, format_func=lambda p: p.stem)

    try:
        config = load_config(config_path)
        bucket = int(time.time() // (max(config.cache_minutos, 1) * 60))
        dataset = _cached_dataset(str(config_path), config_path.stat().st_mtime, bucket)
    except Exception as error:  # a mensagem vai para a tela, não para o log do servidor
        st.error(f"Não foi possível carregar o projeto **{Path(config_path).stem}**: {error}")
        st.stop()

    base = PageContext(config=config, dataset=dataset, df=dataset.df, filters=[])
    pages = {name: func for name, func in ordered_pages().items() if func.page_available(base)}
    choice = st.sidebar.radio("Página", list(pages), key="page")

    if st.sidebar.button("↻ Atualizar dados", use_container_width=True):
        _cached_dataset.clear()
        st.rerun()

    st.sidebar.markdown("---")
    df, active = render_filters(dataset, config.filtros)
    ctx = PageContext(config=config, dataset=dataset, df=df, filters=active)

    st.title(config.titulo)
    caption = [config.subtitulo] if config.subtitulo else []
    if active:
        caption.append(f"Filtros: {', '.join(active)} ({len(df)} de {len(dataset.df)} respostas)")
    if caption:
        st.caption(" · ".join(caption))
    if dataset.warnings:
        with st.expander(f"⚠ {len(dataset.warnings)} aviso(s) sobre o formulário"):
            for warning in dataset.warnings:
                st.write(f"- {warning}")

    pages[choice](ctx)


main()
