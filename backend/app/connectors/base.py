import time
from abc import ABC, abstractmethod
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

DetailValue = Union[str, int, float, bool, list[str]]


class FieldSpec(BaseModel):
    key: str
    label: str
    kind: Literal["text", "url", "secret"] = "text"
    required: bool = True
    placeholder: str = ""
    help: str = ""
    default: Optional[str] = None


class CheckResult(BaseModel):
    ok: bool
    message: str
    details: dict[str, DetailValue] = Field(default_factory=dict)
    latency_ms: int = 0
    tested_at: float = Field(default_factory=time.time)


class Connector(ABC):
    """A system the app can connect to. Subclasses declare their fields once;
    the API and the UI form are both generated from that declaration."""

    id: str
    name: str
    role: str
    description: str
    docs_url: str
    fields: list[FieldSpec]

    @property
    def secret_keys(self) -> set[str]:
        return {f.key for f in self.fields if f.kind == "secret"}

    @property
    def field_keys(self) -> set[str]:
        return {f.key for f in self.fields}

    def missing_required(self, values: dict[str, str]) -> list[str]:
        return [f.label for f in self.fields if f.required and not values.get(f.key)]

    async def test(self, values: dict[str, str]) -> CheckResult:
        missing = self.missing_required(values)
        if missing:
            return CheckResult(ok=False, message=f"Missing: {', '.join(missing)}")
        started = time.perf_counter()
        result = await self._test(values)
        result.latency_ms = int((time.perf_counter() - started) * 1000)
        return result

    @abstractmethod
    async def _test(self, values: dict[str, str]) -> CheckResult: ...
