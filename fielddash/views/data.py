import io

import pandas as pd
import streamlit as st

from fielddash.ui.compat import FULL_WIDTH
from fielddash.core.context import PageContext
from fielddash.core.normalize import flat_for_export
from fielddash.core.registry import page


@page("Data", order=90)
def render(ctx: PageContext):
    ds = ctx.dataset
    table = flat_for_export(ctx.df, ds.fields)

    st.caption(f"{len(table)} responses · {len(table.columns)} columns")
    st.dataframe(table, **FULL_WIDTH, hide_index=True)

    slug = ctx.config.path.stem
    c1, c2 = st.columns(2)
    c1.download_button("Download CSV", table.to_csv(index=False).encode("utf-8-sig"),
                       f"{slug}.csv", "text/csv", **FULL_WIDTH)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        table.to_excel(writer, index=False, sheet_name="responses")
    c2.download_button("Download Excel", buffer.getvalue(), f"{slug}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       **FULL_WIDTH)

    with st.expander("Form fields"):
        st.dataframe(pd.DataFrame([
            {"alias": f.alias, "question": f.label, "type": f.type, "column": f.column,
             "group": f.group, "ref": f.ref}
            for f in ds.fields
        ]), **FULL_WIDTH, hide_index=True)
