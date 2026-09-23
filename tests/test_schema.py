import json

import pytest

from geocoleta.core.config import load_config
from geocoleta.core.loader import bootstrap, load_dataset
from geocoleta.core.schema import export_column, parse_form, reconcile

from conftest import EXAMPLE

FORM = EXAMPLE / "formulario.json"
DATA = EXAMPLE / "dados.json"


@pytest.fixture(scope="module")
def schema():
    return json.loads(FORM.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def entries():
    return json.loads(DATA.read_text(encoding="utf-8"))["data"]


def test_export_column_rule():
    assert export_column(4, "Idade") == "4_Idade"
    assert export_column(6, "Gênero - Especifique:") == "6_Gnero__Especifique"
    assert export_column(11, "Bairro: ") == "11_Bairro"
    assert export_column(13, "Ocupação principal - Especifique:") == "13_Ocupao_principal_"


def test_every_data_column_has_a_field(schema, entries):
    fields, warnings = reconcile(parse_form(schema), entries[0].keys())
    assert warnings == []
    question_columns = [c for c in entries[0] if c[0].isdigit()]
    assert sorted(question_columns) == sorted(f.column for f in fields if not f.system)


def test_renumbered_form_still_matches(schema, entries):
    # Simula uma pergunta nova no início: todos os índices andam 1
    shifted = json.loads(json.dumps(schema))
    inputs = shifted["data"]["form"]["inputs"]
    inputs.insert(0, {"ref": "x_new", "type": "text", "question": "Pergunta nova", "possible_answers": []})
    fields, warnings = reconcile(parse_form(shifted), entries[0].keys())
    by_ref = {f.ref[-6:]: f.column for f in fields}
    assert by_ref["83aec3"] == "4_Idade"        # Idade continua na coluna certa
    assert by_ref["5401ce"] == "11_Bairro"
    assert any("Pergunta nova" in w for w in warnings)


def test_offline_dataset_types():
    config = load_config(EXAMPLE / "projeto.yaml")
    bootstrap(config)
    ds = load_dataset(config)
    assert len(ds.df) == 18
    assert str(ds.df[ds.field("idade").column].dtype) == "category"
    assert list(ds.df[ds.field("idade").column].cat.categories[:1]) == [ds.field("idade").options[0]]
    assert ds.df[ds.field("16_Beneficirio_de_qu").column].map(type).eq(list).all()
    assert ds.field("localizacao").lat in ds.df.columns
    assert ds.find("2da40f") is None  # ignorado na config


def test_env_next_to_config_is_loaded_before_expansion(tmp_path, monkeypatch):
    monkeypatch.delenv("GEOCOLETA_TESTE_SLUG", raising=False)
    (tmp_path / ".env").write_text("GEOCOLETA_TESTE_SLUG=meu-projeto\n")
    (tmp_path / "p.yaml").write_text("fonte:\n  tipo: epicollect\n  projeto: ${GEOCOLETA_TESTE_SLUG}\n")
    assert load_config(tmp_path / "p.yaml").fonte["projeto"] == "meu-projeto"
