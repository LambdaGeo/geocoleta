import streamlit as st
from core.df_profile import profile_df
from core.filters import render_filters, apply_filters
from core.charts_auto import render_auto_charts
from core.maps import render_map

from core.registry import page

@page("Gráficos da Pesquisa")
def render(df):

    st.title("📊 Dashboard Genérico")
    st.caption("Adaptável automaticamente a qualquer DataSource.")

    profile = profile_df(df)

    with st.sidebar:
        st.write("### 📁 Fonte de Dados")
        st.write(df.shape[0], "registros")

    #filters = render_filters(df, profile)
    #df_filtered = apply_filters(df, filters)
    df_filtered = df

    st.write("### 🔍 Dados filtrados")
    st.dataframe(df_filtered)

    render_auto_charts(df_filtered, profile)

    render_map(df_filtered, profile)
