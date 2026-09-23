"""Diferenças entre as versões do Streamlit suportadas (>= 1.39)."""
import inspect

import streamlit as st


def _accepts_stretch(func) -> bool:
    param = inspect.signature(func).parameters.get("width")
    return param is not None and (param.default == "stretch" or "stretch" in str(param.annotation))


# Versões novas trocaram `use_container_width=True` (obsoleto) por `width="stretch"`.
# A detecção usa st.dataframe (os testes substituem st.plotly_chart por um stub).
FULL_WIDTH = {"width": "stretch"} if _accepts_stretch(st.dataframe) else {"use_container_width": True}


def html_frame(html: str, height: int):
    """HTML completo (ex.: mapa folium) num iframe; `st.iframe` substituiu `components.html`."""
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        import streamlit.components.v1 as components
        components.html(html, height=height)
