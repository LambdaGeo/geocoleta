"""O dashboard como função, para usar dentro de qualquer script Streamlit.

    # streamlit_app.py
    import geocoleta
    geocoleta.dashboard("projetos/")          # pasta: seletor de projeto na barra lateral
    geocoleta.dashboard("projetos/residuos.yaml")
"""
import sys
import time
from pathlib import Path

import streamlit as st

from geocoleta.core.config import load_config
from geocoleta.core.context import PageContext
from geocoleta.core.loader import bootstrap, load_dataset
from geocoleta.core.registry import ordered_pages
from geocoleta.ui.compat import FULL_WIDTH
from geocoleta.ui.filters import render_filters


@st.cache_data(show_spinner="Carregando dados…")
def _cached_dataset(config_path: str, mtime: float, bucket: int):
    # mtime invalida o cache quando a config muda; bucket, a cada `cache_minutos`.
    # O cache é compartilhado entre todos os usuários do servidor.
    config = load_config(config_path)
    bootstrap(config)
    return load_dataset(config)


def _resolve(target) -> Path:
    """Caminho relativo ao diretório atual ou, se não existir, à pasta do script Streamlit."""
    path = Path(target)
    if path.is_absolute() or path.exists():
        return path.resolve()
    script_dir = Path(sys.argv[0]).resolve().parent if sys.argv and sys.argv[0] else Path.cwd()
    return (script_dir / path).resolve()


def dashboard(target=".", *, configure_page: bool = True):
    """Desenha o dashboard de um projeto (.yaml) ou de uma pasta de projetos.

    `configure_page=False` quando o script já chamou `st.set_page_config`.
    """
    if configure_page:
        st.set_page_config(page_title="geocoleta", page_icon="📊", layout="wide")

    target = _resolve(target)
    if target.is_dir():
        options = sorted(target.glob("*.yaml")) + sorted(target.glob("*/*.yaml"))
        if not options:
            st.error(f"Nenhum arquivo .yaml de projeto em {target}")
            st.stop()
        config_path = st.sidebar.selectbox("Projeto", options, format_func=lambda p: p.stem)
    elif target.exists():
        config_path = target
    else:
        st.error(f"Projeto não encontrado: {target}")
        st.stop()

    try:
        config = load_config(config_path)
        bootstrap(config)
        bucket = int(time.time() // (max(config.cache_minutos, 1) * 60))
        dataset = _cached_dataset(str(config_path), config_path.stat().st_mtime, bucket)
    except Exception as error:  # a mensagem vai para a tela, não para o log do servidor
        st.error(f"Não foi possível carregar o projeto **{Path(config_path).stem}**: {error}")
        st.stop()

    base = PageContext(config=config, dataset=dataset, df=dataset.df, filters=[])
    pages = {name: func for name, func in ordered_pages().items() if func.page_available(base)}
    choice = st.sidebar.radio("Página", list(pages), key="page")

    if st.sidebar.button("↻ Atualizar dados", **FULL_WIDTH):
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
