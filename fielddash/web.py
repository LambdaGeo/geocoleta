"""The dashboard as a callable function for use inside any Streamlit script.

    # streamlit_app.py
    import fielddash
    fielddash.dashboard("projects/")          # directory: project selector in sidebar
    fielddash.dashboard("projects/waste.yaml")
"""
import sys
import time
from pathlib import Path

import streamlit as st

from fielddash.core.config import load_config
from fielddash.core.context import PageContext
from fielddash.core.loader import bootstrap, load_dataset
from fielddash.core.registry import ordered_pages
from fielddash.ui.compat import FULL_WIDTH
from fielddash.ui.filters import render_filters


@st.cache_data(show_spinner="Loading data…")
def _cached_dataset(config_path: str, mtime: float, bucket: int):
    # mtime invalidates cache when config changes; bucket invalidates every `cache_minutes`.
    # Cache is shared across all server sessions.
    config = load_config(config_path)
    bootstrap(config)
    return load_dataset(config)


def _resolve(target) -> Path:
    """Relative path from current directory or script directory."""
    path = Path(target)
    if path.is_absolute() or path.exists():
        return path.resolve()
    script_dir = Path(sys.argv[0]).resolve().parent if sys.argv and sys.argv[0] else Path.cwd()
    return (script_dir / path).resolve()


def dashboard(target=".", *, configure_page: bool = True):
    """Renders the dashboard for a project (.yaml) or a directory of projects.

    Set `configure_page=False` if the host script already called `st.set_page_config`.
    """
    if configure_page:
        st.set_page_config(page_title="fielddash", page_icon="📊", layout="wide")

    target = _resolve(target)
    if target.is_dir():
        options = sorted(target.glob("*.yaml")) + sorted(target.glob("*/*.yaml"))
        if not options:
            st.error(f"No project .yaml files found in {target}")
            st.stop()
        config_path = st.sidebar.selectbox("Project", options, format_func=lambda p: p.stem)
    elif target.exists():
        config_path = target
    else:
        st.error(f"Project not found: {target}")
        st.stop()

    try:
        config = load_config(config_path)
        bootstrap(config)
        bucket = int(time.time() // (max(config.cache_minutes, 1) * 60))
        dataset = _cached_dataset(str(config_path), config_path.stat().st_mtime, bucket)
    except Exception as error:
        st.error(f"Could not load project **{Path(config_path).stem}**: {error}")
        st.stop()

    base = PageContext(config=config, dataset=dataset, df=dataset.df, filters=[])
    pages = {name: func for name, func in ordered_pages().items() if func.page_available(base)}
    choice = st.sidebar.radio("Page", list(pages), key="page")

    if st.sidebar.button("↻ Refresh data", **FULL_WIDTH):
        _cached_dataset.clear()
        st.rerun()

    st.sidebar.markdown("---")
    df, active = render_filters(dataset, config.filters)
    ctx = PageContext(config=config, dataset=dataset, df=df, filters=active)

    st.title(config.title)
    caption = [config.subtitle] if config.subtitle else []
    if active:
        caption.append(f"Filters: {', '.join(active)} ({len(df)} of {len(dataset.df)} responses)")
    if caption:
        st.caption(" · ".join(caption))
    if dataset.warnings:
        with st.expander(f"⚠ {len(dataset.warnings)} warning(s) about the form schema"):
            for warning in dataset.warnings:
                st.write(f"- {warning}")

    pages[choice](ctx)
