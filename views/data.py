import io

import pandas as pd
import streamlit as st

from core.context import PageContext
from core.normalize import flat_for_export
from core.registry import page


@page("Dados", order=90)
def render(ctx: PageContext):
    ds = ctx.dataset
    table = flat_for_export(ctx.df, ds.fields)

    st.caption(f"{len(table)} respostas · {len(table.columns)} colunas")
    st.dataframe(table, use_container_width=True, hide_index=True)

    slug = ctx.config.path.stem
    c1, c2 = st.columns(2)
    c1.download_button("Baixar CSV", table.to_csv(index=False).encode("utf-8-sig"),
                       f"{slug}.csv", "text/csv", use_container_width=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        table.to_excel(writer, index=False, sheet_name="respostas")
    c2.download_button("Baixar Excel", buffer.getvalue(), f"{slug}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)

    with st.expander("Campos do formulário"):
        st.dataframe(pd.DataFrame([
            {"apelido": f.alias, "pergunta": f.label, "tipo": f.type, "coluna": f.column,
             "grupo": f.group, "ref": f.ref}
            for f in ds.fields
        ]), use_container_width=True, hide_index=True)
