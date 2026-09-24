"""Exemplo de página específica de um projeto, carregada por `extensoes` na config."""
import streamlit as st

from fielddash.core.registry import page
from fielddash.ui.charts import render_field


@page("Reciclagem", order=40, available=lambda ctx: ctx.dataset.find("separa_reciclagem") is not None)
def render(ctx):
    ds, df = ctx.dataset, ctx.df
    answers = df[ds.field("separa_reciclagem").column].dropna()
    share = f"{(answers == 'Sim').mean():.0%}" if len(answers) else "—"
    st.metric("Separam o lixo para reciclagem", share, help=f"{len(answers)} respostas")
    st.markdown("**Separação por bairro**")
    render_field(ds, df, ds.field("separa_reciclagem"), by=ds.field("bairro"))
