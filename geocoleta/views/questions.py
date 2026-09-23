import streamlit as st

from geocoleta.core.context import PageContext
from geocoleta.core.registry import page
from geocoleta.ui.charts import render_field

SKIP = ("location", "media", "other")


def _sections(ctx: PageContext):
    """Seções da config (`secoes`) ou, na falta delas, os grupos do formulário."""
    ds = ctx.dataset
    fields = [f for f in ds.fields if not f.system and f.kind not in SKIP]
    if ctx.config.secoes:
        sections = []
        for section in ctx.config.secoes:
            found = [ds.find(k) for k in section.get("campos", [])]
            sections.append((section["titulo"], [f for f in found if f in fields]))
        return sections

    sections = {}
    for f in fields:
        sections.setdefault(f.group or "Questionário", []).append(f)
    return list(sections.items())


@page("Perguntas", order=30)
def render(ctx: PageContext):
    ds, df = ctx.dataset, ctx.df
    if df.empty:
        st.warning("Nenhuma resposta com os filtros atuais.")
        return

    crossable = [f for f in ds.fields if f.kind == "categorical"]
    c1, c2, c3 = st.columns([2, 2, 1])
    labels = {f.column: f.label for f in crossable}
    by_column = c1.selectbox("Cruzar com", ["—"] + list(labels), format_func=lambda c: labels.get(c, c),
                      help="Mostra a distribuição de cada pergunta dentro dos grupos desta outra pergunta.",
                      key="cross_by")
    by = ds.find(by_column) if by_column != "—" else None
    search = c2.text_input("Buscar pergunta", placeholder="ex.: reciclagem")
    hide_text = c3.toggle("Ocultar abertas", value=True, help="Esconde perguntas de texto livre")

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
                st.caption("Nenhuma pergunta nesta seção com os critérios atuais.")
