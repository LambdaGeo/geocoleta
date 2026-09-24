import streamlit as st

from fielddash.core.context import PageContext
from fielddash.core.registry import page
from fielddash.ui.charts import render_field

SKIP = ("location", "media", "other")


def _sections(ctx: PageContext):
    """Sections from config (`sections` or `secoes`) or form input groups by default."""
    ds = ctx.dataset
    fields = [f for f in ds.fields if not f.system and f.kind not in SKIP]
    config_sections = ctx.config.sections
    if config_sections:
        sections = []
        for section in config_sections:
            f_keys = section.get("fields") or section.get("campos", [])
            s_title = section.get("title") or section.get("titulo", "Section")
            found = [ds.find(k) for k in f_keys]
            sections.append((s_title, [f for f in found if f in fields]))
        return sections

    sections = {}
    for f in fields:
        sections.setdefault(f.group or "Questionnaire", []).append(f)
    return list(sections.items())


@page("Questions", order=30)
def render(ctx: PageContext):
    ds, df = ctx.dataset, ctx.df
    if df.empty:
        st.warning("No responses with the current filters.")
        return

    crossable = [f for f in ds.fields if f.kind == "categorical"]
    c1, c2, c3 = st.columns([2, 2, 1])
    labels = {f.column: f.label for f in crossable}
    by_column = c1.selectbox("Cross with", ["—"] + list(labels), format_func=lambda c: labels.get(c, c),
                      help="Shows the distribution of each question within groups of this other question.",
                      key="cross_by")
    by = ds.find(by_column) if by_column != "—" else None
    search = c2.text_input("Search question", placeholder="e.g. recycling")
    hide_text = c3.toggle("Hide open-ended", value=True, help="Hide free-text questions")

    sections = _sections(ctx)
    tabs = st.tabs([title for title, _ in sections]) if len(sections) > 1 else [st.container()]
    for tab, (title, fields) in zip(tabs, sections):
        with tab:
            shown = 0
            for f in fields:
                if hide_text and f.kind == "text":
                    continue
                if search and search.lower() not in f.label.lower():
                    continue
                shown += 1
                with st.container(border=True):
                    st.markdown(f"**{f.label}**")
                    render_field(ds, df, f, by=by, key=f"q_{f.column}")
            if not shown:
                st.caption("No questions in this section match the current criteria.")
