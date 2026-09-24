"""fielddash: schema-driven dashboards for field data collection (Epicollect5)."""

__version__ = "0.1.0"


def dashboard(target=".", *, configure_page: bool = True):
    """Renders the dashboard for a project (.yaml) or directory of projects in a Streamlit script."""
    from fielddash.web import dashboard as _dashboard  # imports streamlit only when called

    return _dashboard(target, configure_page=configure_page)
