import pytest

from geocoleta.sources import epicollect


class FakeResponse:
    def __init__(self, status, data):
        self.status_code, self._data, self.text = status, data, ""

    def json(self):
        return self._data


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(epicollect, "TOKEN_CACHE", tmp_path / "tokens.json")
    monkeypatch.setattr(epicollect, "_tokens", {})
    monkeypatch.setattr(epicollect, "_blocked_until", {})
    monkeypatch.setenv("TESTE_CLIENT_ID", "id")
    monkeypatch.setenv("TESTE_CLIENT_SECRET", "secret")
    calls = []

    def post(*args, **kwargs):
        calls.append(1)
        return FakeResponse(200, {"access_token": "tok", "expires_in": 7200})

    monkeypatch.setattr(epicollect.requests, "post", post)
    return calls


def test_token_is_reused_across_runs(isolated):
    assert epicollect.get_token("TESTE") == "tok"
    epicollect._tokens.clear()  # simula reiniciar o app
    assert epicollect.get_token("TESTE") == "tok"
    assert len(isolated) == 1
    assert "secret" not in epicollect.TOKEN_CACHE.read_text()
    assert oct(epicollect.TOKEN_CACHE.stat().st_mode)[-3:] == "600"


def test_rate_limit_backs_off(isolated, monkeypatch):
    calls = []
    monkeypatch.setattr(epicollect.requests, "post", lambda *a, **k: calls.append(1) or FakeResponse(429, {}))
    for _ in range(3):  # recargas da página não voltam a bater na API
        with pytest.raises(epicollect.EpicollectError, match="Aguarde"):
            epicollect.get_token("TESTE")
    assert len(calls) == 1
