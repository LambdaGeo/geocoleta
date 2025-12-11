import streamlit as st
import plotly.express as px

def render_auto_charts(df, profile):
    st.subheader("📊 Gráficos automáticos")

    if profile["categorical"] and profile["numeric"]:
        cat = profile["categorical"][0]
        num = profile["numeric"][0]

        fig = px.bar(df, x=cat, y=num, title=f"{num} por {cat}")
        st.plotly_chart(fig, use_container_width=True)

    if len(profile["numeric"]) >= 2:
        x = profile["numeric"][0]
        y = profile["numeric"][1]
        fig = px.scatter(df, x=x, y=y, title=f"{y} vs {x}")
        st.plotly_chart(fig, use_container_width=True)

    if profile["numeric"]:
        num = profile["numeric"][0]
        fig = px.histogram(df, x=num, title=f"Distribuição de {num}")
        st.plotly_chart(fig, use_container_width=True)
