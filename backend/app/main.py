from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import connections
from app.settings import get_settings

app = FastAPI(
    title="DataHub AI Root Cause",
    version="0.1.0",
    description=(
        "Backend for the AI root-cause demo. Connects Pinecone (retrieval), "
        "Langfuse (LLM observability), DataHub (metadata graph) and Claude."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connections.router)


@app.get("/api/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
