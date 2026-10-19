import time
from abc import ABC, abstractmethod
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

DetailValue = Union[str, int, float, bool, list[str]]


class FieldOption(BaseModel):
    value: str
    label: str


class FieldSpec(BaseModel):
    key: str
    label: str
    kind: Literal["text", "url", "secret", "select"] = "text"
    required: bool = True
    placeholder: str = ""
    help: str = ""
    default: Optional[str] = None
    env: Optional[str] = Field(default=None, description="Environment variable that can set it.")
    options: list[FieldOption] = Field(default_factory=list)


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

    def required_keys(self, values: dict[str, str]) -> set[str]:
        """Override when a field is only required for some values of another field."""
        return {f.key for f in self.fields if f.required}

    def missing_required(self, values: dict[str, str]) -> list[str]:
        required = self.required_keys(values)
        return [f.label for f in self.fields if f.key in required and not values.get(f.key)]

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
