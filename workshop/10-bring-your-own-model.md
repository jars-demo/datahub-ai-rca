# 10 · Bring your own model (5 min)

## Do it

On **Connections**, change the LLM provider and model, **Save & test**, and run the same
investigation again. Compare the answers, the number of tool calls and the tokens used.

| Provider | `LLM_PROVIDER` | Notes |
|---|---|---|
| Anthropic | `anthropic` | Native SDK. Default model `claude-opus-5-5`, with server-side refusal fallbacks |
| OpenAI | `openai` | |
| Google Gemini | `google` | Gemini's OpenAI-compatible endpoint |
| Groq | `groq` | |
| OpenRouter | `openrouter` | Any model OpenRouter serves |
| Mistral | `mistral` | |
| Together AI | `together` | |
| DeepSeek | `deepseek` | |
| Ollama | `ollama` | Local, no key. Pick a model with tool calling |
| Custom | `custom` | Any OpenAI-compatible endpoint: set `LLM_BASE_URL` |

The model must support tool calling for the agent. The test lists models when the one you
typed isn't available.

## How it works

The assistant and the agent only speak the neutral types in
[`llm/types.py`](../backend/app/llm/types.py): `Turn`, `ToolSpec`, `ToolCall`, `Completion`.
Two adapters translate them:

- [`anthropic_client.py`](../backend/app/llm/anthropic_client.py): the official Anthropic SDK.
  Claude's own content blocks (including thinking) are replayed unchanged between tool calls.
- [`openai_client.py`](../backend/app/llm/openai_client.py): the Chat Completions API, which
  every other provider implements.

Adding a provider is one entry in [`llm/providers.py`](../backend/app/llm/providers.py).

You have finished the workshop.
