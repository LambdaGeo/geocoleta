import streamlit as st

from geocoleta.core.context import PageContext
from geocoleta.core.registry import page
from geocoleta.ui.charts import render_field, timeline
from geocoleta.ui.maps import location_field, render_map


@page("Visão geral", order=10)
def render(ctx: PageContext):
    ds, df = ctx.dataset, ctx.df
    created = ds.find("created_at")
    collector = ds.find("created_by")
    place = location_field(ds, ctx.config.mapa)

    cols = st.columns(4)
    cols[0].metric("Respostas", len(df), help=f"{len(ds.df)} no total" if len(df) != len(ds.df) else None)
    if collector:
        cols[1].metric("Coletores", df[collector.column].nunique())
    if created is not None and not df.empty:
        cols[2].metric("Última coleta", df[created.column].max().strftime("%d/%m/%Y"))
    if place is not None and place.lat in df.columns and len(df):
        cols[3].metric("Com localização", f"{df[place.lat].notna().mean():.0%}")

    if df.empty:
        st.warning("Nenhuma resposta com os filtros atuais.")
        return

    if place is not None:
        st.subheader("Onde foram as entrevistas")
        render_map(ds, df, ctx.config.mapa, key="overview_map")

    left, right = st.columns(2)
    if created is not None:
        with left:
            st.subheader("Coletas ao longo do tempo")
            timeline(df, created, key="overview_timeline")
    if collector:
        with right:
            st.subheader("Respostas por coletor")
            render_field(ds, df, collector, key="overview_collector")
