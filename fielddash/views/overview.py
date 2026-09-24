import streamlit as st

from fielddash.core.context import PageContext
from fielddash.core.registry import page
from fielddash.ui.charts import render_field, timeline
from fielddash.ui.maps import location_field, render_map


@page("Overview", order=10)
def render(ctx: PageContext):
    ds, df = ctx.dataset, ctx.df
    created = ds.find("created_at")
    collector = ds.find("created_by")
    place = location_field(ds, ctx.config.map)

    cols = st.columns(4)
    cols[0].metric("Responses", len(df), help=f"{len(ds.df)} total" if len(df) != len(ds.df) else None)
    if collector:
        cols[1].metric("Collectors", df[collector.column].nunique())
    if created is not None and not df.empty:
        cols[2].metric("Latest entry", df[created.column].max().strftime("%d/%m/%Y"))
    if place is not None and place.lat in df.columns and len(df):
        cols[3].metric("With location", f"{df[place.lat].notna().mean():.0%}")

    if df.empty:
        st.warning("No responses with the current filters.")
        return

    if place is not None:
        st.subheader("Survey locations")
        render_map(ds, df, ctx.config.map, key="overview_map")

    left, right = st.columns(2)
    if created is not None:
        with left:
            st.subheader("Submissions over time")
            timeline(df, created, key="overview_timeline")
    if collector:
        with right:
            st.subheader("Responses by collector")
            render_field(ds, df, collector, key="overview_collector")
