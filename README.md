<div align="center">
  <img src="frontend/public/logos/datahub.svg" alt="DataHub" width="72">
</div>

<h1 align="center">datahub-ai-rca</h1>

<p align="center">
  <strong>Why did our AI assistant get worse?</strong><br>
  A hands-on workshop: bring Pinecone and Langfuse into <a href="https://datahub.com">DataHub</a>,
  connect them with lineage, and let an agent trace an AI quality regression to its source.
</p>

A support assistant built on Pinecone and Langfuse starts giving wrong answers. Nothing crashed
and no alert fired. You load both systems into DataHub with two connectors, see one lineage
graph from source documents to production traces, and watch an agent, running on **any LLM you
choose**, find the cause, the owner and the fix.

- **One realistic incident**, seeded into your own Pinecone, Langfuse and DataHub
- **Two connectors I contributed to DataHub itself**: Pinecone ([#16472](https://github.com/datahub-project/datahub/pull/16472), merged) and Langfuse ([#19923](https://github.com/datahub-project/datahub/pull/19923), in review, bundled here until it is released). They belong to DataHub, so every DataHub user can use them; this workshop shows what they make possible together
- **Bring your own model**: Anthropic, OpenAI, Gemini, Groq, OpenRouter, Mistral, Together, DeepSeek, Ollama or any OpenAI-compatible endpoint
- **60 minutes**, for data and AI engineers

```text
source docs ─▶ Pinecone namespace ─▶ Langfuse prompt version ─▶ traces + scores
     └───────────── one lineage graph in DataHub ─────────────┘   ◀── agent (any LLM)
```

## Get started

You need Docker, Python 3.11+, Node 20+, and free accounts for
[Pinecone](https://app.pinecone.io), [Langfuse](https://cloud.langfuse.com) and one LLM provider.

```bash
# 1. DataHub
pip install 'acryl-datahub==1.7.0.14' && datahub docker quickstart

# 2. The app
git clone https://github.com/jars-demo/datahub-ai-rca.git && cd datahub-ai-rca
make setup        # dependencies + .env
make dev          # backend :8300, app :3300
```

Open **<http://localhost:3300/workshop>** and follow the steps. Put your keys on the
Connections page or in `.env`; the DataHub token is created for you.

## The workshop

| Step | You will | Time |
|---|---|---|
| [00 · Prerequisites](workshop/00-prerequisites.md) | Install, start DataHub and the app | before |
| [01 · The incident](workshop/01-the-incident.md) | Understand what broke and why it is hard to see | 5 min |
| [02 · Connect your systems](workshop/02-connect.md) | Pinecone, Langfuse, DataHub and any LLM | 10 min |
| [03 · Seed the knowledge base](workshop/03-seed-pinecone.md) | Two help-center versions in two namespaces | 5 min |
| [04 · Seed a week of traffic](workshop/04-seed-langfuse.md) | Prompt v1–v3, 70 traces, scores | 5 min |
| [05 · Bring it into DataHub](workshop/05-ingest.md) | Run both connectors, add owners and lineage | 10 min |
| [06 · Explore the AI lineage](workshop/06-lineage.md) | Source → namespace → prompt, in DataHub | 5 min |
| [07 · See the symptom](workshop/07-assistant.md) | Ask the assistant, open the trace | 5 min |
| [08 · Find the root cause](workshop/08-investigate.md) | Watch the agent work through the graph | 10 min |
| [09 · Fix and verify](workshop/09-fix.md) | Roll back the prompt, confirm the answer | 5 min |
| [10 · Bring your own model](workshop/10-bring-your-own-model.md) | Switch providers, rerun, compare | 5 min |

Stuck? See [troubleshooting](workshop/troubleshooting.md).

## The app

| Page | What it does |
|---|---|
| **Workshop** | The steps above, with live seed buttons, logs and progress |
| **Assistant** | The RAG app under investigation: production prompt from Langfuse, retrieval from Pinecone, traced back to Langfuse |
| **Investigate** | The root-cause agent, with every tool call shown as it happens |
| **AI lineage** | The scenario's lineage graph, read live from DataHub |
| **Connections** | Plug in your own accounts; values from `.env` or the UI |
| **About this build** | The live DataHub version and commit, and where each connector comes from |

## How the connectors are used

| In the source system | In DataHub | Connector |
|---|---|---|
| Pinecone index · namespace | Container · dataset with inferred schema | Pinecone source (released in `acryl-datahub`) |
| Langfuse prompt version | Versioned dataset | Langfuse source (bundled from PR #19923) |
| Langfuse trace · generation | Run linked to its prompt version | Langfuse source |
| Langfuse score | Metric on the run | Langfuse source |
| Source documents, owners, deprecation, lineage | Datasets, ownership, deprecation, upstream lineage | [`ingestion/rca_ingestion/context.py`](ingestion/rca_ingestion/context.py) |

## Bring your own model

The assistant and the agent use one neutral interface ([`backend/app/llm/`](backend/app/llm)).
Anthropic uses its native SDK; every other provider uses one OpenAI-compatible adapter. Set
`LLM_PROVIDER`, `LLM_API_KEY` and `LLM_MODEL` (or use the Connections page). Embeddings stay in
Pinecone, so switching models never means re-embedding.

## What is inside

```text
datahub-ai-rca/
├── .env.example            every setting, explained
├── Makefile                setup, dev, seed, status, test, lint
├── data/                   the scenario: help-center versions, prompts, questions
├── backend/                FastAPI
│   └── app/
│       ├── connectors/     one class per system: fields + connection test
│       ├── llm/            neutral types, Anthropic adapter, OpenAI-compatible adapter
│       ├── services/       every Pinecone, Langfuse and DataHub call
│       ├── agent/          read-only tools and the tool-use loop
│       ├── seed/           deterministic seeding steps
│       └── routers/        REST + server-sent events
├── ingestion/              acryl-datahub 1.7.0.14 in its own environment
│   ├── recipes/            pinecone.yml, langfuse.yml
│   └── rca_ingestion/      run.py, context.py, langfuse_source/ (from PR #19923)
├── frontend/               React + TypeScript + Vite
└── workshop/               the step-by-step guide
```

`ingestion/` has its own environment because the Pinecone extra of `acryl-datahub` pins
`pinecone-client<6`, while the app uses the current `pinecone` SDK.

## Commands

```bash
make dev             # backend + frontend
make seed            # seed Pinecone, Langfuse and DataHub from the terminal
make datahub-token   # create a DataHub token with datahub / datahub
make status          # connections and seed state
make check           # tests, lint, frontend build (what CI runs)
```

| URL | What |
|---|---|
| <http://localhost:3300> | The app |
| <http://localhost:8300/docs> | Backend API (Swagger) |
| <http://localhost:9002> | DataHub UI |

This is a community workshop built on DataHub, not an official DataHub project. All company
names and data in the scenario are fictional.

## License

[Apache License 2.0](LICENSE), the same as DataHub. The bundled Langfuse source comes from
DataHub; see [NOTICE](NOTICE).
