import json
from typing import Any

import openai

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

_STOP_REASONS: dict[str, StopReason] = {
    "stop": "end",
    "tool_calls": "tool_use",
    "function_call": "tool_use",
    "length": "max_tokens",
    "content_filter": "refusal",
}


class OpenAICompatibleClient(LLMClient):
    """Any provider that implements the OpenAI Chat Completions API."""

    def __init__(self, provider: str, api_key: str, model: str, base_url: str | None) -> None:
        self.provider = provider
        self.model = model
        # Local servers such as Ollama ignore the key, but the SDK requires a value.
        self._client = openai.AsyncOpenAI(
            api_key=api_key or "not-needed", base_url=base_url, timeout=120.0, max_retries=2
        )

    @staticmethod
    def _messages(system: str, turns: list[Turn]) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
        for turn in turns:
            if turn.role == "user":
                messages.append({"role": "user", "content": turn.text})
            elif turn.role == "assistant":
                message: dict[str, Any] = {"role": "assistant", "content": turn.text or None}
                if turn.tool_calls:
                    message["tool_calls"] = [
                        {
                            "id": c.id,
                            "type": "function",
                            "function": {"name": c.name, "arguments": json.dumps(c.arguments)},
                        }
                        for c in turn.tool_calls
                    ]
                messages.append(message)
            else:
                messages += [
                    {"role": "tool", "tool_call_id": r.call_id, "content": r.content}
                    for r in turn.tool_results
                ]
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
            "messages": self._messages(system, turns),
        }
        # OpenAI's newer models only accept max_completion_tokens; most compatible
        # providers still expect max_tokens.
        params["max_completion_tokens" if self.provider == "openai" else "max_tokens"] = max_tokens
        if tools:
            params["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        try:
            response = await self._client.chat.completions.create(**params)
        except openai.AuthenticationError as e:
            raise LLMError(f"{self.provider} rejected the API key.") from e
        except openai.NotFoundError as e:
            raise LLMError(f"Model '{self.model}' was not found on {self.provider}.") from e
        except openai.RateLimitError as e:
            raise LLMError(f"{self.provider} rate limit reached.", retryable=True) from e
        except openai.APIConnectionError as e:
            raise LLMError(f"Could not reach {self.provider}.", retryable=True) from e
        except openai.APIStatusError as e:
            raise LLMError(f"{self.provider} API error ({e.status_code}).") from e

        if not response.choices:
            raise LLMError(f"{self.provider} returned no choices.")
        choice = response.choices[0]
        calls = []
        for c in choice.message.tool_calls or []:
            try:
                arguments = json.loads(c.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {"_invalid_json": c.function.arguments}
            calls.append(ToolCall(id=c.id, name=c.function.name, arguments=arguments))

        usage = response.usage
        return Completion(
            text=choice.message.content or "",
            tool_calls=calls,
            stop_reason=_STOP_REASONS.get(choice.finish_reason or "", "other"),
            model=response.model or self.model,
            usage=Usage(usage.prompt_tokens if usage else 0, usage.completion_tokens if usage else 0),
        )

    async def list_models(self) -> list[str]:
        try:
            return [m.id async for m in self._client.models.list()]
        except openai.AuthenticationError as e:
            raise LLMError(f"{self.provider} rejected the API key.") from e
        except openai.APIConnectionError as e:
            raise LLMError(f"Could not reach {self.provider}.") from e
        except openai.APIStatusError as e:
            raise LLMError(f"{self.provider} API error ({e.status_code}).") from e
