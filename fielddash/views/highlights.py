import streamlit as st

from fielddash.core.context import PageContext
from fielddash.core.registry import page
from fielddash.ui.charts import render_field


@page("Highlights", order=20, available=lambda ctx: bool(ctx.config.highlights))
def render(ctx: PageContext):
    """Charts selected in config:

    highlights:
      - {field: waste_dest}
      - {field: collection_freq, by: neighborhood, title: "Collection frequency by neighborhood"}
    """
    ds, df = ctx.dataset, ctx.df
    if df.empty:
        st.warning("No responses with the current filters.")
        return

    items = ctx.config.highlights
    for i in range(0, len(items), 2):
        cols = st.columns(2)
        for col, item in zip(cols, items[i:i + 2]):
            with col, st.container(border=True):
                field_key = item.get("field") or item.get("campo")
                by_key = item.get("by") or item.get("por")
                title_key = item.get("title") or item.get("titulo")

                f = ds.find(field_key)
                by = ds.find(by_key) if by_key else None
                if f is None:
                    st.error(f"Highlight: field {field_key!r} not found")
                    continue
                title = title_key or (f"{f.label} × {by.label}" if by else f.label)
                st.markdown(f"**{title}**")
                render_field(ds, df, f, by=by, key=f"hl_{i}_{f.column}")
