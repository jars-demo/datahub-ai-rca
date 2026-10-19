import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi.responses import StreamingResponse


def event(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, default=str)}\n\n"


def stream(events: AsyncIterator[dict[str, Any]]) -> StreamingResponse:
    async def body() -> AsyncIterator[str]:
        async for e in events:
            yield event(e)

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
