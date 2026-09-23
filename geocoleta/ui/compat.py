"""Diferenças entre as versões do Streamlit suportadas (>= 1.39)."""
import inspect

import streamlit as st


def _accepts_stretch(func) -> bool:
    param = inspect.signature(func).parameters.get("width")
    return param is not None and (param.default == "stretch" or "stretch" in str(param.annotation))


# Versões novas trocaram `use_container_width=True` (obsoleto) por `width="stretch"`
FULL_WIDTH = {"width": "stretch"} if _accepts_stretch(st.plotly_chart) else {"use_container_width": True}
