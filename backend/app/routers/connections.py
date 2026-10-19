from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.connectors.base import CheckResult, Connector, FieldSpec
from app.connectors.registry import CONNECTORS
from app.deps import get_store
from app.services.datahub_api import DataHubError, create_access_token
from app.store import ConnectionStore, public_values

router = APIRouter(prefix="/api/connections", tags=["connections"])


class ConnectionView(BaseModel):
    id: str
    name: str
    role: str
    description: str
    docs_url: str
    fields: list[FieldSpec]
    values: dict[str, str] = Field(description="Effective values. Secrets are always blank.")
    secrets_set: list[str] = Field(description="Secret fields that have a value.")
    from_env: list[str] = Field(description="Fields whose value comes from .env.")
    configured: bool
    last_check: CheckResult | None


class ValuesPayload(BaseModel):
    values: dict[str, str] = Field(
        default_factory=dict,
        description="Field values. Leave a secret blank to keep the current one.",
    )


class TokenRequest(BaseModel):
    username: str = "datahub"
    password: str = "datahub"


def get_connector(connector_id: str) -> Connector:
    connector = CONNECTORS.get(connector_id)
    if connector is None:
        raise HTTPException(404, f"Unknown connection '{connector_id}'.")
    return connector


def _view(connector: Connector, store: ConnectionStore) -> ConnectionView:
    stored = store.get(connector.id)
    env_values = store.env_values(connector)
    effective = store.resolve(connector, {})
    return ConnectionView(
        id=connector.id,
        name=connector.name,
        role=connector.role,
        description=connector.description,
        docs_url=connector.docs_url,
        fields=connector.fields,
        values=public_values(connector, effective),
        secrets_set=sorted(k for k in connector.secret_keys if effective.get(k)),
        from_env=sorted(k for k in env_values if k not in stored.values),
        configured=not connector.missing_required(effective),
        last_check=stored.last_check,
    )


def _validate_keys(connector: Connector, values: dict[str, str]) -> None:
    unknown = set(values) - connector.field_keys
    if unknown:
        raise HTTPException(422, f"Unknown field(s): {', '.join(sorted(unknown))}.")


@router.get("", response_model=list[ConnectionView])
def list_connections(store: ConnectionStore = Depends(get_store)) -> list[ConnectionView]:
    return [_view(c, store) for c in CONNECTORS.values()]


@router.get("/{connector_id}", response_model=ConnectionView)
def get_connection(
    connector: Connector = Depends(get_connector),
    store: ConnectionStore = Depends(get_store),
) -> ConnectionView:
    return _view(connector, store)


@router.put("/{connector_id}", response_model=ConnectionView)
def save_connection(
    payload: ValuesPayload,
    connector: Connector = Depends(get_connector),
    store: ConnectionStore = Depends(get_store),
) -> ConnectionView:
    _validate_keys(connector, payload.values)
    store.save(connector, payload.values)
    return _view(connector, store)


@router.post("/{connector_id}/test", response_model=CheckResult)
async def test_connection(
    payload: ValuesPayload | None = None,
    connector: Connector = Depends(get_connector),
    store: ConnectionStore = Depends(get_store),
) -> CheckResult:
    """Test the current settings, or unsaved edits sent in the body (merged over the current
    ones). Only a test of the current settings is remembered."""
    overrides = payload.values if payload else {}
    _validate_keys(connector, overrides)
    values = store.resolve(connector, overrides)
    result = await connector.test(values)
    if values == store.resolve(connector, {}):
        store.record_check(connector.id, result)
    return result


@router.delete("/{connector_id}", status_code=204)
def delete_connection(
    connector: Connector = Depends(get_connector),
    store: ConnectionStore = Depends(get_store),
) -> None:
    store.delete(connector.id)


@router.post("/datahub/token", response_model=ConnectionView)
async def create_datahub_token(
    payload: TokenRequest,
    store: ConnectionStore = Depends(get_store),
) -> ConnectionView:
    """Log in to the DataHub UI (default quickstart login: datahub / datahub), create a personal
    access token, save it, and test the connection."""
    connector = CONNECTORS["datahub"]
    ui_url = store.resolve(connector, {})["ui_url"]
    try:
        token = await create_access_token(ui_url, payload.username, payload.password)
    except DataHubError as e:
        raise HTTPException(400, str(e)) from e
    store.save(connector, {"token": token})
    store.record_check(connector.id, await connector.test(store.resolve(connector, {})))
    return _view(connector, store)
