"""Configuration variables: environment (.env) or Streamlit Secrets."""
import os


def getenv(name: str) -> str | None:
    """Retrieves value of `name` from environment (including .env) or `st.secrets`.

    `st.secrets` comes from `.streamlit/secrets.toml` or Streamlit Community Cloud
    dashboard Secrets, where there is no local .env file.
    """
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st

        value = st.secrets.get(name)
    except Exception:  # no secrets configured or outside of Streamlit runtime
        return None
    return str(value) if value is not None else None
