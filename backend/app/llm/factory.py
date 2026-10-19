from app.llm.anthropic_client import AnthropicClient
from app.llm.openai_client import OpenAICompatibleClient
from app.llm.providers import DEFAULT_PROVIDER, PROVIDERS
from app.llm.types import LLMClient, LLMError


def build_llm(values: dict[str, str]) -> LLMClient:
    """Build a client from the 'llm' connection values (provider, model, api_key, base_url)."""
    provider_id = values.get("provider") or DEFAULT_PROVIDER
    info = PROVIDERS.get(provider_id)
    if info is None:
        raise LLMError(f"Unknown LLM provider '{provider_id}'.")

    model = values.get("model") or info.default_model
    if not model:
        raise LLMError(f"Choose a model for {info.label}.")
    base_url = values.get("base_url") or info.base_url
    if info.adapter == "openai" and not base_url:
        raise LLMError("A base URL is required for a custom OpenAI-compatible provider.")
    api_key = values.get("api_key", "")
    if info.needs_key and not api_key:
        raise LLMError(f"An API key is required for {info.label}.")

    if info.adapter == "anthropic":
        return AnthropicClient(api_key=api_key, model=model, base_url=values.get("base_url"))
    return OpenAICompatibleClient(provider_id, api_key=api_key, model=model, base_url=base_url)
