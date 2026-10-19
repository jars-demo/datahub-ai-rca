# AGENTS.md

Guidance for AI coding agents and developers working in this repo.

## What this is

A workshop app for DataHub: a RAG support assistant on Pinecone and Langfuse, its metadata in
DataHub, and an agent that traces a quality regression to its source with any LLM provider.
Attendees read the code as a reference, so prefer clear over clever.

## Map

```text
data/                       scenario data shared by backend and ingestion
backend/app/
├── connectors/             one class per system; fields drive the API, the form and .env
├── llm/                    types.py (neutral), anthropic_client.py, openai_client.py, providers.py
├── services/               knowledge_base.py (Pinecone), langfuse_api.py, datahub_api.py,
│                           assistant.py, lineage.py
├── agent/                  tools.py (read-only tools), runner.py (tool-use loop)
├── seed/                   traffic.py (deterministic), steps.py (streamed steps)
├── routers/                REST and SSE endpoints
├── store.py                connection settings: defaults < .env < UI
└── cli.py                  python -m app.cli seed|datahub-token|status
ingestion/                  separate venv, acryl-datahub 1.7.0.14
├── recipes/                pinecone.yml, langfuse.yml
└── rca_ingestion/          run.py, context.py, langfuse_source/ (from datahub PR #19923)
frontend/src/               pages/, components/, workshop/steps.tsx, api/
workshop/                   chapters 00–10 + troubleshooting
```

## Commands

```bash
make setup && make dev        # backend :8300, frontend :3300
make check                    # pytest, ruff, frontend build
make seed                     # real end-to-end seeding (needs keys)
```

## Rules

1. **Service calls live in `services/`.** Routers validate and stream; they don't call SDKs.
2. **The agent and assistant only use `app.llm.types`.** Never import a provider SDK outside
   `app/llm/`. A new provider is one entry in `providers.py`.
3. **Secrets never reach the browser or this process's environment.** `.env` is read into a
   dict; ingestion credentials go only into the child process environment.
4. **Seeding is idempotent and deterministic.** Stable ids; re-running updates, never duplicates.
5. **Agent tools are read-only** and return links for every entity they mention.
6. **The bundled Langfuse source stays a faithful copy** of datahub PR #19923 (imports and
   `subtypes.py` only). Delete it once the connector ships in `acryl-datahub`.
7. **Docs follow the app:** flow changes update `workshop/*.md` and `frontend/src/workshop/steps.tsx`.
8. **Never commit** `.env`, `backend/.data/`, virtualenvs, `node_modules/` or keys.

## Style

Python 3.11+, ruff (line length 110), type hints on public functions. TypeScript strict,
function components. Commits: Conventional Commits, no AI attribution lines.
