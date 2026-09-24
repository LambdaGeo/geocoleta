import streamlit as st

from geocoleta.core.context import PageContext
from geocoleta.core.registry import page
from geocoleta.ui.charts import render_field


@page("Destaques", order=20, available=lambda ctx: bool(ctx.config.destaques))
def render(ctx: PageContext):
    """Gráficos escolhidos na config:

    destaques:
      - {campo: destino_lixo}
      - {campo: frequencia_coleta, por: bairro, titulo: "Frequência de coleta por bairro"}
    """
    ds, df = ctx.dataset, ctx.df
    if df.empty:
        st.warning("Nenhuma resposta com os filtros atuais.")
        return

    items = ctx.config.destaques
    for i in range(0, len(items), 2):
        cols = st.columns(2)
        for col, item in zip(cols, items[i:i + 2]):
            with col, st.container(border=True):
                f = ds.find(item["campo"])
                by = ds.find(item["por"]) if item.get("por") else None
                if f is None:
                    st.error(f"Destaque: campo {item['campo']!r} não encontrado")
                    continue
                title = item.get("titulo") or (f"{f.label} × {by.label}" if by else f.label)
                st.markdown(f"**{title}**")
                render_field(ds, df, f, by=by, key=f"hl_{i}_{f.column}")
