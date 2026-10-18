# AI Root Cause Analysis on DataHub

Trace quality regressions in LLM applications back to their source.

A modular reference application for AI root-cause analysis on top of
[DataHub](https://datahub.com). It connects the systems behind a typical RAG
application and uses DataHub's metadata graph to trace a quality issue end to end:

| Step | System | What it contributes |
| --- | --- | --- |
| 1. Detect | **Langfuse** | Traces, prompt versions and quality scores |
| 2. Retrieve | **Pinecone** | The index and namespace answers were drawn from |
| 3. Trace | **DataHub** | Lineage, ownership and change history across systems |
| 4. Explain | **Claude** | An agent that walks the graph and explains the cause |

Pinecone and Langfuse metadata reach DataHub through the DataHub ingestion
connectors for those platforms.

## Status

- [x] Connections — configure and test credentials for any Pinecone, Langfuse,
      DataHub and Anthropic account from the UI
- [ ] Investigate — the root-cause agent
- [ ] AI lineage view

## Architecture

```
frontend/  React + Vite + TypeScript, DataHub design tokens
  src/api/          typed API client
  src/components/   ConnectionCard, FieldInput, StatusPill, …
  src/pages/        Overview, Connections, (Investigate, Lineage)

backend/   FastAPI
  app/connectors/   one module per system; each declares its fields + a test()
  app/routers/      REST API (generated from the connector declarations)
  app/store.py      local JSON store for settings (owner-only file permissions)
```

Adding a system means adding one connector class and registering it in
`app/connectors/registry.py`; the API and the UI form are generated from its
field declarations.

**Secrets** are stored only in `backend/.data/connections.json` (gitignored,
`chmod 600`). The API never returns them: secret fields come back blank, with a
`secrets_set` list so the UI can show "saved".

## Run it

Requirements: Python 3.11+, Node 20+.

```bash
make setup     # once
make dev       # backend on :8000, frontend on :5173
```

| URL | What |
| --- | --- |
| http://localhost:5173 | The app |
| http://localhost:5173/docs (or :8000/docs) | Interactive API docs (Swagger) |

Running on a remote machine? Forward port **5173** — the frontend proxies `/api`
and `/docs` to the backend, so one port is enough.

```bash
make test        # backend tests
make typecheck   # frontend type check
```

## API

| Method | Path | |
| --- | --- | --- |
| `GET` | `/api/connections` | All connections, their fields and status |
| `PUT` | `/api/connections/{id}` | Save settings (blank secret = keep saved) |
| `POST` | `/api/connections/{id}/test` | Test saved settings, or unsaved edits in the body |
| `DELETE` | `/api/connections/{id}` | Forget saved settings |
| `GET` | `/api/health` | Liveness |

`{id}` is one of `pinecone`, `langfuse`, `datahub`, `anthropic`.
