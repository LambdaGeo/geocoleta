"""Differences across supported Streamlit versions (>= 1.39)."""
import inspect

import streamlit as st


def _accepts_stretch(func) -> bool:
    param = inspect.signature(func).parameters.get("width")
    return param is not None and (param.default == "stretch" or "stretch" in str(param.annotation))


# Newer versions replaced `use_container_width=True` (deprecated) with `width="stretch"`.
# Detection uses st.dataframe (tests replace st.plotly_chart with a stub).
FULL_WIDTH = {"width": "stretch"} if _accepts_stretch(st.dataframe) else {"use_container_width": True}


def html_frame(html: str, height: int):
    """Full HTML (e.g. Folium map) inside an iframe; `st.iframe` replaced `components.html`."""
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height)
