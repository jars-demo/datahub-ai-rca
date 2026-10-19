"""A provider-neutral tool-use loop. Works with any LLMClient: Claude, OpenAI, Gemini, Groq,
Ollama and the rest, because it only speaks the neutral types in app.llm.types."""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import Any

from app.agent.tools import TOOLS, ToolContext
from app.llm.types import LLMClient, LLMError, ToolCall, ToolResult, Turn
from app.scenario import scenario

MAX_STEPS = 14
MAX_RESULT_CHARS = 12_000

SYSTEM_PROMPT = f"""You are a reliability analyst for {scenario()["company"]}'s customer support assistant, a RAG application.

The assistant answers with a prompt managed in Langfuse, retrieves help-center articles from a Pinecone index, and is scored in Langfuse. DataHub holds the metadata graph that connects them: source datasets, Pinecone namespaces, Langfuse prompt versions and traces, with owners, deprecation status and lineage.

Investigate the user's question with the tools. Work from evidence: measure the change, find what changed at the same time, follow lineage in DataHub to the data behind it, and confirm with concrete examples. Prefer a few well-chosen tool calls over many.

Reply in Markdown with these sections:
### Summary
One or two sentences: what happened and why.
### Evidence
Bullets with numbers (scores before and after, dates, counts) and one or two concrete examples.
### Root cause chain
The path from source data to the user-facing symptom, as a short arrow chain with each step linked to DataHub.
### Owners
Who to contact, from DataHub ownership.
### Recommended fix
Specific, ordered actions.

Link entities with the `url` / `datahub_url` / `langfuse_url` values the tools return. Never invent URLs, names or numbers."""


def _summarize(name: str, result: Any) -> str:
    if isinstance(result, dict):
        if "error" in result:
            return str(result["error"])
        for key in ("results", "entities", "examples", "versions", "hits", "daily"):
            if key in result and isinstance(result[key], list):
                return f"{len(result[key])} {key}"
        if "name" in result:
            return str(result["name"])
    return "ok"


async def _execute(ctx: ToolContext, call: ToolCall) -> tuple[ToolResult, Any]:
    entry = TOOLS.get(call.name)
    if entry is None:
        return ToolResult(call.id, f"Unknown tool '{call.name}'.", is_error=True), None
    if "_invalid_json" in call.arguments:
        return ToolResult(call.id, "Arguments were not valid JSON. Retry the call.", is_error=True), None
    _, fn = entry
    try:
        result = await fn(ctx, call.arguments)
    except KeyError as e:
        return ToolResult(call.id, f"Missing argument: {e}", is_error=True), None
    except Exception as e:  # noqa: BLE001 - tool errors go back to the model as data
        return ToolResult(call.id, f"{type(e).__name__}: {e}", is_error=True), None
    content = json.dumps(result, default=str)
    if len(content) > MAX_RESULT_CHARS:
        content = content[:MAX_RESULT_CHARS] + "… (truncated)"
    return ToolResult(call.id, content), result


async def investigate(question: str, llm: LLMClient, ctx: ToolContext) -> AsyncIterator[dict[str, Any]]:
    tools = [spec for spec, _ in TOOLS.values()]
    turns = [Turn(role="user", text=question)]
    started = time.perf_counter()
    usage_in = usage_out = 0
    yield {"type": "start", "provider": llm.provider, "model": llm.model}

    for step in range(1, MAX_STEPS + 1):
        try:
            completion = await llm.complete(SYSTEM_PROMPT, turns, tools=tools, max_tokens=8000)
        except LLMError as e:
            yield {"type": "error", "message": str(e)}
            return
        usage_in += completion.usage.input_tokens
        usage_out += completion.usage.output_tokens

        if completion.stop_reason == "refusal":
            yield {"type": "error", "message": "The model declined this request."}
            return
        if not completion.tool_calls:
            yield {"type": "answer", "markdown": completion.text}
            yield {
                "type": "done",
                "steps": step,
                "seconds": round(time.perf_counter() - started, 1),
                "input_tokens": usage_in,
                "output_tokens": usage_out,
                "model": completion.model,
            }
            return

        if completion.text.strip():
            yield {"type": "note", "text": completion.text.strip()}
        turns.append(completion.as_turn(llm.provider))
        for call in completion.tool_calls:
            yield {"type": "tool_call", "id": call.id, "name": call.name, "arguments": call.arguments}
        outcomes = await asyncio.gather(*(_execute(ctx, c) for c in completion.tool_calls))
        for call, (tool_result, data) in zip(completion.tool_calls, outcomes):
            yield {
                "type": "tool_result",
                "id": call.id,
                "name": call.name,
                "ok": not tool_result.is_error,
                "summary": tool_result.content if tool_result.is_error else _summarize(call.name, data),
                "data": data,
            }
        # All results for one assistant turn go back together in a single turn.
        turns.append(Turn(role="tool", tool_results=[r for r, _ in outcomes]))

    yield {"type": "error", "message": f"Stopped after {MAX_STEPS} steps without a final answer."}
