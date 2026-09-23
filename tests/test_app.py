import pytest
import streamlit
from streamlit.testing.v1 import AppTest

from conftest import ROOT

APP = str(ROOT / "app.py")
OFFLINE = str(ROOT / "projetos" / "residuos_offline.yaml")


def _plotly_stub(fig, *args, **kwargs):
    # AppTest (Streamlit 1.39) não sabe interagir com páginas que têm plotly_chart;
    # serializar a figura ainda valida o gráfico montado.
    fig.to_json()


def run(monkeypatch, page=None):
    monkeypatch.setenv("DASH_CONFIG", OFFLINE)
    monkeypatch.setattr(streamlit, "plotly_chart", _plotly_stub)
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    if page:
        at.sidebar.radio(key="page").set_value(page).run()
    assert not at.exception, at.exception
    return at


@pytest.mark.parametrize("page", ["Visão geral", "Destaques", "Perguntas", "Dados"])
def test_pages_render(monkeypatch, page):
    run(monkeypatch, page)


def test_cross_and_filter(monkeypatch):
    at = run(monkeypatch, "Perguntas")
    at.selectbox(key="cross_by").select_index(3).run()      # cruzar com uma pergunta
    assert not at.exception, at.exception
    bairro = next(m for m in at.sidebar.multiselect if m.label == "Bairro")
    bairro.select(bairro.options[0]).run()
    assert not at.exception, at.exception
    assert "Filtros: Bairro" in at.caption[0].value
