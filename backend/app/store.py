import json
import os
import threading
import time
from pathlib import Path

from pydantic import BaseModel, Field

from app.connectors.base import CheckResult, Connector


class StoredConnection(BaseModel):
    values: dict[str, str] = Field(default_factory=dict)
    last_check: CheckResult | None = None
    updated_at: float | None = None


class ConnectionStore:
    """Persists connection settings to a local JSON file (owner-only permissions).

    Effective values are layered: field defaults < environment (.env) < saved in the UI <
    per-request overrides. The API layer only ever returns masked values.
    """

    def __init__(self, path: Path, env: dict[str, str] | None = None) -> None:
        self._path = path
        self._env = env or {}
        self._lock = threading.Lock()

    def _read(self) -> dict[str, StoredConnection]:
        if not self._path.exists():
            return {}
        raw = json.loads(self._path.read_text())
        return {k: StoredConnection.model_validate(v) for k, v in raw.items()}

    def _write(self, data: dict[str, StoredConnection]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        payload = json.dumps({k: v.model_dump() for k, v in data.items()}, indent=2)
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(payload)
        tmp.replace(self._path)

    def get(self, connector_id: str) -> StoredConnection:
        with self._lock:
            return self._read().get(connector_id, StoredConnection())

    def env_values(self, connector: Connector) -> dict[str, str]:
        return {f.key: self._env[f.env] for f in connector.fields if f.env and self._env.get(f.env)}

    def resolve(self, connector: Connector, overrides: dict[str, str]) -> dict[str, str]:
        """Effective values. A blank secret in `overrides` means "keep the current one", so
        the UI never needs to hold it."""
        values = {f.key: f.default for f in connector.fields if f.default}
        values.update(self.env_values(connector))
        values.update(self.get(connector.id).values)
        for key, value in overrides.items():
            if key in connector.secret_keys and not value:
                continue
            values[key] = value.strip()
        return values

    def save(self, connector: Connector, overrides: dict[str, str]) -> StoredConnection:
        base = self.resolve(connector, {})
        values = self.resolve(connector, overrides)
        # Only persist what differs from defaults + environment, so .env stays authoritative
        # for anything the user did not change in the UI.
        inherited = {f.key: f.default for f in connector.fields if f.default}
        inherited.update(self.env_values(connector))
        to_store = {k: v for k, v in values.items() if inherited.get(k) != v}
        with self._lock:
            data = self._read()
            current = data.get(connector.id, StoredConnection())
            data[connector.id] = StoredConnection(
                values=to_store,
                # A check result is only meaningful for the values it tested.
                last_check=current.last_check if base == values else None,
                updated_at=time.time(),
            )
            self._write(data)
            return data[connector.id]

    def record_check(self, connector_id: str, result: CheckResult) -> None:
        with self._lock:
            data = self._read()
            data.setdefault(connector_id, StoredConnection()).last_check = result
            self._write(data)

    def delete(self, connector_id: str) -> None:
        with self._lock:
            data = self._read()
            if data.pop(connector_id, None) is not None:
                self._write(data)


def public_values(connector: Connector, values: dict[str, str]) -> dict[str, str]:
    return {k: ("" if k in connector.secret_keys else v) for k, v in values.items()}
