from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.connectors.base import CheckResult
from app.connectors.registry import CONNECTORS
from app.main import app
from app.routers.connections import get_store
from app.store import ConnectionStore

LANGFUSE = CONNECTORS["langfuse"]


@pytest.fixture
def store(tmp_path) -> ConnectionStore:
    return ConnectionStore(tmp_path / "connections.json")


@pytest.fixture
def client(store: ConnectionStore, monkeypatch) -> Iterator[TestClient]:
    async def fake_test(values: dict[str, str]) -> CheckResult:
        ok = values.get("secret_key") == "sk-good"
        return CheckResult(ok=ok, message="ok" if ok else "rejected")

    monkeypatch.setattr(LANGFUSE, "_test", fake_test)
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def _langfuse(client: TestClient) -> dict:
    return client.get("/api/connections/langfuse").json()


def test_list_shows_defaults_and_is_unconfigured(client: TestClient) -> None:
    items = {c["id"]: c for c in client.get("/api/connections").json()}
    assert list(items) == ["pinecone", "langfuse", "datahub", "anthropic"]
    assert items["langfuse"]["values"]["host"] == "https://cloud.langfuse.com"
    assert items["langfuse"]["configured"] is False


def test_secrets_are_never_returned_and_blank_keeps_saved(
    client: TestClient, store: ConnectionStore
) -> None:
    client.put(
        "/api/connections/langfuse",
        json={"values": {"public_key": "pk-1", "secret_key": "sk-good"}},
    )
    view = _langfuse(client)
    assert view["values"]["secret_key"] == ""
    assert view["secrets_set"] == ["secret_key"]
    assert view["configured"] is True

    client.put(
        "/api/connections/langfuse",
        json={"values": {"public_key": "pk-2", "secret_key": ""}},
    )
    assert store.get("langfuse").values["secret_key"] == "sk-good"
    assert store.get("langfuse").values["public_key"] == "pk-2"


def test_saved_check_is_recorded_and_cleared_on_change(client: TestClient) -> None:
    client.put(
        "/api/connections/langfuse",
        json={"values": {"public_key": "pk-1", "secret_key": "sk-good"}},
    )
    assert client.post("/api/connections/langfuse/test").json()["ok"] is True
    assert _langfuse(client)["last_check"]["ok"] is True

    client.put("/api/connections/langfuse", json={"values": {"public_key": "pk-9"}})
    assert _langfuse(client)["last_check"] is None


def test_unsaved_values_are_tested_but_not_recorded(client: TestClient) -> None:
    client.put(
        "/api/connections/langfuse",
        json={"values": {"public_key": "pk-1", "secret_key": "sk-good"}},
    )
    result = client.post(
        "/api/connections/langfuse/test", json={"values": {"secret_key": "sk-bad"}}
    ).json()
    assert result["ok"] is False
    assert _langfuse(client)["last_check"] is None


def test_missing_required_fields_fail_without_calling_service(client: TestClient) -> None:
    result = client.post("/api/connections/langfuse/test").json()
    assert result["ok"] is False
    assert "Public key" in result["message"]


def test_rejects_unknown_connector_and_fields(client: TestClient) -> None:
    assert client.get("/api/connections/nope").status_code == 404
    resp = client.put("/api/connections/langfuse", json={"values": {"bogus": "x"}})
    assert resp.status_code == 422
