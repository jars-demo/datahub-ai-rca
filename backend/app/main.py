from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import assistant, connections, investigate, lineage, seed, system
from app.settings import get_settings

app = FastAPI(
    title="DataHub AI Root Cause",
    version="0.2.0",
    description=(
        "Workshop backend: a RAG support assistant on Pinecone and Langfuse, its metadata in "
        "DataHub, and an agent that traces quality regressions to their source. Works with any "
        "LLM provider."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (system, connections, seed, assistant, investigate, lineage):
    app.include_router(module.router)
