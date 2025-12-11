import streamlit as st
import pandas as pd

def render_filters(df, profile):
    """Cria filtros dinâmicos automaticamente com base no perfil."""
    
    st.sidebar.header("Filtros")

    filters = {}

    # Filtros numéricos → slider
    for col in profile["numeric"]:
        min_v = float(df[col].min())
        max_v = float(df[col].max())
        filters[col] = st.sidebar.slider(col, min_v, max_v, (min_v, max_v))

    # Filtros categóricos → multiselect
    for col in profile["categorical"]:
        options = sorted(df[col].dropna().unique())
        filters[col] = st.sidebar.multiselect(col, options, default=options)

    # Booleanos → select
    for col in profile["boolean"]:
        filters[col] = st.sidebar.selectbox(col, ["Todos", True, False])

    # Datas → intervalo
    for col in profile["datetime"]:
        min_d = df[col].min()
        max_d = df[col].max()
        filters[col] = st.sidebar.date_input(col, (min_d, max_d))

    return filters


def apply_filters(df, filters):
    """Aplica os filtros retornando somente os registros válidos."""

    for col, val in filters.items():

        # Numéricos
        if isinstance(val, tuple) and len(val) == 2:
            df = df[df[col].between(val[0], val[1])]
            continue

        # Categóricos
        if isinstance(val, list):
            if val:
                df = df[df[col].isin(val)]
            continue

        # Booleanos
        if val in (True, False):
            df = df[df[col] == val]
            continue

        # Datas
        if isinstance(val, tuple) and hasattr(val[0], "year"):
            start, end = val
            df = df[(df[col] >= pd.to_datetime(start)) & (df[col] <= pd.to_datetime(end))]
            continue

    return df
