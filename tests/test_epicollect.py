import pytest

from fielddash.sources import epicollect


class FakeResponse:
    def __init__(self, status, data, headers=None):
        self.status_code, self._data, self.text = status, data, ""
        self.headers = headers or {}

    def json(self):
        return self._data


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(epicollect, "TOKEN_CACHE", tmp_path / "tokens.json")
    monkeypatch.setattr(epicollect, "_tokens", {})
    monkeypatch.setattr(epicollect, "_blocked", {"until": 0.0})
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
    epicollect._tokens.clear()  # simulates restarting the app
    assert epicollect.get_token("TESTE") == "tok"
    assert len(isolated) == 1
    assert "secret" not in epicollect.TOKEN_CACHE.read_text()
    assert oct(epicollect.TOKEN_CACHE.stat().st_mode)[-3:] == "600"


def test_rate_limit_respects_retry_after_across_restarts(isolated, monkeypatch):
    calls = []
    blocked = FakeResponse(429, {}, {"Retry-After": "1305"})
    monkeypatch.setattr(epicollect.requests, "post", lambda *a, **k: calls.append(1) or blocked)
    for _ in range(3):  # page reloads should not hit the API again
        with pytest.raises(epicollect.EpicollectError, match="Retry allowed"):
            epicollect.get_token("TESTE")
    epicollect._blocked["until"] = 0.0  # simulates restarting app: block is loaded from disk
    with pytest.raises(epicollect.EpicollectError, match="Retry allowed"):
        epicollect.get_token("TESTE")
    assert len(calls) == 1
    assert epicollect._blocked_until() - epicollect.time.time() > 1200


def test_credentials_from_streamlit_secrets(isolated, monkeypatch):
    import streamlit

    monkeypatch.delenv("TESTE_CLIENT_ID")
    monkeypatch.delenv("TESTE_CLIENT_SECRET")
    monkeypatch.setattr(streamlit, "secrets", {"TESTE_CLIENT_ID": "id", "TESTE_CLIENT_SECRET": "secret"})
    assert epicollect.get_token("TESTE") == "tok"


def test_missing_credentials_message(isolated, monkeypatch):
    import streamlit

    monkeypatch.delenv("TESTE_CLIENT_ID")
    monkeypatch.setattr(streamlit, "secrets", {})
    with pytest.raises(epicollect.EpicollectError, match="TESTE_CLIENT_ID"):
        epicollect.get_token("TESTE")
