"""Supported providers. Anthropic uses its native SDK; everything else speaks the
OpenAI-compatible Chat Completions API, so adding a provider is one entry here."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ProviderInfo:
    id: str
    label: str
    adapter: Literal["anthropic", "openai"]
    base_url: str | None
    default_model: str | None
    needs_key: bool
    key_url: str


PROVIDERS: dict[str, ProviderInfo] = {
    p.id: p
    for p in (
        ProviderInfo(
            "anthropic",
            "Anthropic (Claude)",
            "anthropic",
            None,
            "claude-opus-5-5",
            True,
            "https://console.anthropic.com/settings/keys",
        ),
        ProviderInfo(
            "openai",
            "OpenAI",
            "openai",
            "https://api.openai.com/v1",
            None,
            True,
            "https://platform.openai.com/api-keys",
        ),
        ProviderInfo(
            "google",
            "Google Gemini",
            "openai",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
            None,
            True,
            "https://aistudio.google.com/apikey",
        ),
        ProviderInfo(
            "groq",
            "Groq",
            "openai",
            "https://api.groq.com/openai/v1",
            None,
            True,
            "https://console.groq.com/keys",
        ),
        ProviderInfo(
            "openrouter",
            "OpenRouter",
            "openai",
            "https://openrouter.ai/api/v1",
            None,
            True,
            "https://openrouter.ai/keys",
        ),
        ProviderInfo(
            "mistral",
            "Mistral",
            "openai",
            "https://api.mistral.ai/v1",
            None,
            True,
            "https://console.mistral.ai/api-keys",
        ),
        ProviderInfo(
            "together",
            "Together AI",
            "openai",
            "https://api.together.xyz/v1",
            None,
            True,
            "https://api.together.ai/settings/api-keys",
        ),
        ProviderInfo(
            "deepseek",
            "DeepSeek",
            "openai",
            "https://api.deepseek.com/v1",
            None,
            True,
            "https://platform.deepseek.com/api_keys",
        ),
        ProviderInfo(
            "ollama",
            "Ollama (local)",
            "openai",
            "http://localhost:11434/v1",
            None,
            False,
            "https://ollama.com/library",
        ),
        ProviderInfo(
            "custom",
            "Custom (OpenAI-compatible)",
            "openai",
            None,
            None,
            False,
            "https://platform.openai.com/docs/api-reference/chat",
        ),
    )
}

DEFAULT_PROVIDER = "anthropic"
