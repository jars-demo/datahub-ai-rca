"""Provider-neutral types. The assistant and the agent only ever see these; each provider
adapter translates them to and from its own wire format."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

StopReason = Literal["end", "tool_use", "max_tokens", "refusal", "other"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    content: str
    is_error: bool = False


@dataclass
class Turn:
    """One conversation turn. `raw` holds the provider's own assistant content so it can be
    replayed unchanged (Claude requires thinking blocks to be passed back as-is)."""

    role: Literal["user", "assistant", "tool"]
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    raw: Any = None
    raw_provider: Optional[str] = None


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class Completion:
    text: str
    tool_calls: list[ToolCall]
    stop_reason: StopReason
    model: str
    usage: Usage = field(default_factory=Usage)
    raw: Any = None

    def as_turn(self, provider: str) -> Turn:
        return Turn(
            role="assistant",
            text=self.text,
            tool_calls=self.tool_calls,
            raw=self.raw,
            raw_provider=provider,
        )


class LLMError(Exception):
    """A provider error, with a message safe to show in the UI."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class LLMClient(ABC):
    provider: str
    model: str

    @abstractmethod
    async def complete(
        self,
        system: str,
        turns: list[Turn],
        tools: Optional[list[ToolSpec]] = None,
        max_tokens: int = 16000,
    ) -> Completion: ...

    @abstractmethod
    async def list_models(self) -> list[str]: ...
