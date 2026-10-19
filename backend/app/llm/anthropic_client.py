from typing import Any

import anthropic

from app.llm.types import (
    Completion,
    LLMClient,
    LLMError,
    StopReason,
    ToolCall,
    ToolSpec,
    Turn,
    Usage,
)

# Models that accept server-side refusal fallbacks (`fallbacks: "default"`).
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}
_FALLBACK_BETA = "server-side-fallback-2026-07-01"

_STOP_REASONS: dict[str, StopReason] = {
    "end_turn": "end",
    "stop_sequence": "end",
    "tool_use": "tool_use",
    "max_tokens": "max_tokens",
    "refusal": "refusal",
}


class AnthropicClient(LLMClient):
    provider = "anthropic"

    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self.model = model
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key, base_url=base_url or None, timeout=120.0, max_retries=2
        )
        # Fallbacks are a first-party API feature; skip them behind proxies/gateways.
        self._fallbacks = base_url is None and model in _FALLBACK_MODELS

    def _messages(self, turns: list[Turn]) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        for turn in turns:
            if turn.role == "user":
                messages.append({"role": "user", "content": turn.text})
            elif turn.role == "assistant":
                if turn.raw is not None and turn.raw_provider == self.provider:
                    # Replay Claude's own content blocks unchanged (thinking, fallback, tool_use).
                    messages.append({"role": "assistant", "content": turn.raw})
                    continue
                content: list[dict[str, Any]] = []
                if turn.text:
                    content.append({"type": "text", "text": turn.text})
                content += [
                    {"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments}
                    for c in turn.tool_calls
                ]
                messages.append({"role": "assistant", "content": content})
            else:
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": r.call_id,
                                "content": r.content,
                                "is_error": r.is_error,
                            }
                            for r in turn.tool_results
                        ],
                    }
                )
        return messages

    async def complete(
        self,
        system: str,
        turns: list[Turn],
        tools: list[ToolSpec] | None = None,
        max_tokens: int = 16000,
    ) -> Completion:
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": self._messages(turns),
        }
        if tools:
            params["tools"] = [
                {"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools
            ]
        if self._fallbacks:
            params["betas"] = [_FALLBACK_BETA]
            params["fallbacks"] = "default"

        try:
            response = await self._client.beta.messages.create(**params)
        except anthropic.AuthenticationError as e:
            raise LLMError("Anthropic rejected the API key.") from e
        except anthropic.NotFoundError as e:
            raise LLMError(f"Model '{self.model}' was not found.") from e
        except anthropic.RateLimitError as e:
            raise LLMError("Anthropic rate limit reached. Try again shortly.", retryable=True) from e
        except anthropic.APIConnectionError as e:
            raise LLMError("Could not reach the Anthropic API.", retryable=True) from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"Anthropic API error ({e.status_code}).") from e

        text = "".join(b.text for b in response.content if b.type == "text")
        calls = [
            ToolCall(id=b.id, name=b.name, arguments=dict(b.input))
            for b in response.content
            if b.type == "tool_use"
        ]
        return Completion(
            text=text,
            tool_calls=calls,
            stop_reason=_STOP_REASONS.get(response.stop_reason or "", "other"),
            model=response.model,
            usage=Usage(response.usage.input_tokens, response.usage.output_tokens),
            raw=response.content,
        )

    async def list_models(self) -> list[str]:
        try:
            return [m.id async for m in self._client.models.list()]
        except anthropic.AuthenticationError as e:
            raise LLMError("Anthropic rejected the API key.") from e
        except anthropic.APIConnectionError as e:
            raise LLMError("Could not reach the Anthropic API.") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"Anthropic API error ({e.status_code}).") from e
