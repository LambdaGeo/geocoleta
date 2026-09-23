from pathlib import Path

import pytest
import streamlit
from streamlit.testing.v1 import AppTest

import geocoleta
from conftest import EXAMPLE

APP = str(Path(geocoleta.__file__).resolve().parent / "app.py")
CONFIG = str(EXAMPLE / "projeto.yaml")


def _plotly_stub(fig, *args, **kwargs):
    # AppTest (Streamlit 1.39) não sabe interagir com páginas que têm plotly_chart;
    # serializar a figura ainda valida o gráfico montado.
    fig.to_json()


def run(monkeypatch, page=None):
    monkeypatch.setenv("GEOCOLETA_CONFIG", CONFIG)
    monkeypatch.setattr(streamlit, "plotly_chart", _plotly_stub)
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    if page:
        at.sidebar.radio(key="page").set_value(page).run()
    assert not at.exception, at.exception
    return at


@pytest.mark.parametrize("page", ["Visão geral", "Destaques", "Perguntas", "Reciclagem", "Dados"])
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


def test_dashboard_function_in_user_script(monkeypatch):
    monkeypatch.setattr(streamlit, "plotly_chart", _plotly_stub)
    script = Path(__file__).parent / "fixtures" / "streamlit_app.py"
    monkeypatch.setattr("sys.argv", [str(script)])  # como o `streamlit run` define
    at = AppTest.from_file(str(script), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    assert at.title[0].value == "Diagnóstico de Resíduos – Itaqui-Bacanga"
