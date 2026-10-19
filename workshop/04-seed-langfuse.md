# 04 · Seed a week of traffic (5 min)

## Do it

Click **Seed Langfuse**, or run `make seed-langfuse`.

## What just happened

**Prompts.** The prompt `support-answer` now has three versions
([`data/langfuse/prompts.json`](../data/langfuse/prompts.json)). Each version's **config** names
the Pinecone namespace the assistant retrieves from:

| Version | Commit message | `config.namespace` |
|---|---|---|
| v1 | Initial support assistant prompt | `help-center-2025` |
| v2 | Ground answers strictly in excerpts and cite article titles | `help-center-2025` |
| v3 · **production** | Friendlier tone; point retrieval at the consolidated help-center namespace | `help-center-2023-archive` |

The v3 change looks harmless in a prompt diff. The config change is the bug.

**Traffic.** Seven days of `support-chat` traces, ten a day, each with a generation linked to
the prompt version it used and two scores (`correctness`, `helpfulness`). v2 serves the first
four days; v3 serves the last three. Questions about anything that changed since 2023 get
confidently wrong answers on v3, and their correctness drops to around 0.2.

The traffic is deterministic ([`seed/traffic.py`](../backend/app/seed/traffic.py)) and every
event has a stable id, so re-running the step updates instead of duplicating. Events go through
Langfuse's public ingestion API ([`services/langfuse_api.py`](../backend/app/services/langfuse_api.py)).

## Try

In Langfuse, open **Traces** and the **correctness** score over time. You can see *that*
quality dropped and *which* prompt version was live. You cannot see *why*.

Next: [05 · Bring it into DataHub](./05-ingest.md)
