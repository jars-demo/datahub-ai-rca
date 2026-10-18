import json
import os
import threading
import time
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from app.connectors.base import CheckResult, Connector


class StoredConnection(BaseModel):
    values: dict[str, str] = Field(default_factory=dict)
    last_check: Optional[CheckResult] = None
    updated_at: Optional[float] = None


class ConnectionStore:
    """Persists connection settings to a local JSON file (owner-only permissions).

    Secrets never leave this class unmasked through `public_values`; the API
    layer only ever returns masked values.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
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

    def resolve(self, connector: Connector, overrides: dict[str, str]) -> dict[str, str]:
        """Effective values: defaults < saved < overrides. A blank secret in
        `overrides` means "keep the saved one", so the UI never needs to hold it."""
        saved = self.get(connector.id).values
        values = {f.key: f.default for f in connector.fields if f.default}
        values.update(saved)
        for key, value in overrides.items():
            if key in connector.secret_keys and not value:
                continue
            values[key] = value.strip()
        return values

    def save(self, connector: Connector, overrides: dict[str, str]) -> StoredConnection:
        values = self.resolve(connector, overrides)
        with self._lock:
            data = self._read()
            current = data.get(connector.id, StoredConnection())
            changed = current.values != values
            data[connector.id] = StoredConnection(
                values=values,
                # A check result is only meaningful for the values it tested.
                last_check=None if changed else current.last_check,
                updated_at=time.time(),
            )
            self._write(data)
            return data[connector.id]

    def record_check(self, connector_id: str, result: CheckResult) -> None:
        with self._lock:
            data = self._read()
            if connector_id in data:
                data[connector_id].last_check = result
                self._write(data)

    def delete(self, connector_id: str) -> None:
        with self._lock:
            data = self._read()
            if data.pop(connector_id, None) is not None:
                self._write(data)


def public_values(connector: Connector, values: dict[str, str]) -> dict[str, str]:
    return {k: ("" if k in connector.secret_keys else v) for k, v in values.items()}
