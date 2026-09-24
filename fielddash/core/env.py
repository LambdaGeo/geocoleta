"""Variáveis de configuração: ambiente (.env) ou Secrets do Streamlit."""
import os


def getenv(name: str) -> str | None:
    """Valor de `name` no ambiente (inclui o .env) ou em `st.secrets`.

    `st.secrets` vem de `.streamlit/secrets.toml` ou do painel *Secrets* do
    Streamlit Community Cloud, onde não há arquivo .env.
    """
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st

        value = st.secrets.get(name)
    except Exception:  # sem secrets configurados ou fora do Streamlit
        return None
    return str(value) if value is not None else None
