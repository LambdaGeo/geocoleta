import io

import pandas as pd
import streamlit as st

from geocoleta.ui.compat import FULL_WIDTH
from geocoleta.core.context import PageContext
from geocoleta.core.normalize import flat_for_export
from geocoleta.core.registry import page


@page("Dados", order=90)
def render(ctx: PageContext):
    ds = ctx.dataset
    table = flat_for_export(ctx.df, ds.fields)

    st.caption(f"{len(table)} respostas · {len(table.columns)} colunas")
    st.dataframe(table, **FULL_WIDTH, hide_index=True)

    slug = ctx.config.path.stem
    c1, c2 = st.columns(2)
    c1.download_button("Baixar CSV", table.to_csv(index=False).encode("utf-8-sig"),
                       f"{slug}.csv", "text/csv", **FULL_WIDTH)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        table.to_excel(writer, index=False, sheet_name="respostas")
    c2.download_button("Baixar Excel", buffer.getvalue(), f"{slug}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       **FULL_WIDTH)

    with st.expander("Campos do formulário"):
        st.dataframe(pd.DataFrame([
            {"apelido": f.alias, "pergunta": f.label, "tipo": f.type, "coluna": f.column,
             "grupo": f.group, "ref": f.ref}
            for f in ds.fields
        ]), **FULL_WIDTH, hide_index=True)
