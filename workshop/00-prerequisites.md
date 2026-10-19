# 00 · Prerequisites

Do this **before** the workshop: about 15 minutes, mostly downloads.

## 1. Tools

| Tool | Needed for | Get it |
|---|---|---|
| Docker | Running DataHub | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| Python 3.11+ | Backend and ingestion | [python.org](https://www.python.org/downloads/) |
| Node 20+ | Frontend | [nodejs.org](https://nodejs.org/) |
| Git | Cloning | [git-scm.com](https://git-scm.com/downloads) |

DataHub needs about 8 GB of free memory. On a small machine, add swap.

## 2. Accounts (all free)

| Account | What you need | Get it |
|---|---|---|
| Pinecone | An API key (Starter plan) | [app.pinecone.io](https://app.pinecone.io) |
| Langfuse | A new project and its public and secret key | [cloud.langfuse.com](https://cloud.langfuse.com) |
| An LLM provider | One API key: Anthropic, OpenAI, Gemini, Groq, OpenRouter, Mistral, Together, DeepSeek, or a local Ollama | see [10 · Bring your own model](./10-bring-your-own-model.md) |

Use a **new** Langfuse project so the seeded traffic is the only traffic.

## 3. Start DataHub

```bash
pip install 'acryl-datahub==1.7.0.14'
datahub docker quickstart
```

The UI runs at <http://localhost:9002> (login `datahub` / `datahub`) and GMS at
<http://localhost:8080>. Already developing DataHub? Run it from your checkout instead; the
app reads the exact version and commit from GMS and shows it under **About this build**.

## 4. Start the app

```bash
git clone https://github.com/jars-demo/datahub-ai-rca.git && cd datahub-ai-rca
make setup      # backend, ingestion and frontend dependencies; creates .env
make dev        # backend on :8300, app on :3300
```

Open <http://localhost:3300/workshop>.

Running on a remote machine? Forward ports **3300** (app), **8300** (API, optional) and
**9002** (DataHub UI).

Next: [01 · The incident](./01-the-incident.md)
