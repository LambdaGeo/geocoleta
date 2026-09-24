"""Filtros gerados pelo tipo do campo. Filtro vazio = sem restrição."""
import datetime as dt

import pandas as pd
import streamlit as st

from fielddash.core.model import Dataset, Field

FILTERABLE = ("categorical", "multi", "numeric", "date")


def _options(df, f: Field):
    if f.kind == "multi":
        seen = pd.Series([v for values in df[f.column] for v in values]).unique().tolist()
        return [o for o in f.options if o in seen] + [v for v in seen if v not in f.options]
    series = df[f.column]
    if isinstance(series.dtype, pd.CategoricalDtype):
        present = set(series.dropna())
        return [c for c in series.cat.categories if c in present]
    return sorted(series.dropna().unique())


def _widget(df, f: Field, key):
    label = f.label if len(f.label) <= 60 else f.label[:57] + "…"
    if f.kind in ("categorical", "multi"):
        return st.multiselect(label, _options(df, f), key=key, placeholder="Todos")
    if f.kind == "numeric":
        values = df[f.column].dropna()
        if values.empty or values.min() == values.max():
            return None
        low, high = float(values.min()), float(values.max())
        chosen = st.slider(label, low, high, (low, high), key=key)
        return None if chosen == (low, high) else chosen
    if f.kind == "date":
        values = df[f.column].dropna()
        if values.empty:
            return None
        low, high = values.min().date(), values.max().date()
        chosen = st.date_input(label, (low, high), min_value=low, max_value=high, key=key, format="DD/MM/YYYY")
        if not isinstance(chosen, (tuple, list)) or len(chosen) != 2 or tuple(chosen) == (low, high):
            return None
        return tuple(chosen)
    return None


def _apply(df, f: Field, value):
    col = df[f.column]
    if f.kind == "categorical":
        return df[col.isin(value)]
    if f.kind == "multi":
        wanted = set(value)
        return df[col.map(lambda values: bool(wanted.intersection(values)))]
    if f.kind == "numeric":
        return df[col.between(*value)]
    if f.kind == "date":
        start = pd.Timestamp(value[0])
        end = pd.Timestamp(value[1]) + dt.timedelta(days=1)
        return df[(col >= start) & (col < end)]
    return df


def render_filters(dataset: Dataset, preset: list) -> tuple:
    """Desenha os filtros na barra lateral e devolve (df_filtrado, descrição dos filtros ativos)."""
    df = dataset.df
    candidates = [f for f in dataset.fields if f.kind in FILTERABLE]
    default = []
    for key in preset:
        found = dataset.find(key)
        if found in candidates and found not in default:
            default.append(found)

    st.sidebar.markdown("### Filtros")
    labels = {f.column: f.label for f in candidates if f not in default}
    extra_columns = st.sidebar.multiselect(
        "Adicionar filtro",
        list(labels),
        format_func=lambda c: labels[c],
        key="filters_extra",
        placeholder="Escolha uma pergunta",
    )
    extra = [dataset.find(c) for c in extra_columns]

    active = []
    for f in default + extra:
        with st.sidebar:
            value = _widget(dataset.df, f, key=f"filter_{f.column}")
        if value:
            df = _apply(df, f, value)
            active.append(f.label)
    return df, active
