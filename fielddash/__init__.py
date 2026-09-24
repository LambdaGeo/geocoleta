"""geocoleta: dashboards para dados de coleta de campo (Epicollect5)."""

__version__ = "0.1.0"


def dashboard(target=".", *, configure_page: bool = True):
    """Desenha o dashboard de um projeto (.yaml) ou pasta de projetos num script Streamlit."""
    from geocoleta.web import dashboard as _dashboard  # importa o Streamlit só quando usado

    return _dashboard(target, configure_page=configure_page)
