# 05 · Bring it into DataHub (10 min)

## Do it

Click **Ingest into DataHub**, or run `make seed-datahub`.

## What just happened

Three ingestion runs, in a separate Python environment (`ingestion/`) with the released
`acryl-datahub` CLI:

### 1. Pinecone, with DataHub's Pinecone source

The Pinecone source ([datahub#16472](https://github.com/datahub-project/datahub/pull/16472),
merged and released) turns the index into a **container** and each namespace into a **dataset**
with a schema inferred from record metadata.

```yaml
# ingestion/recipes/pinecone.yml
source:
  type: pinecone
  config:
    api_key: ${PINECONE_API_KEY}
    index_pattern: { allow: ["^acme-support-kb$"] }
```

### 2. Langfuse, with the Langfuse source

The Langfuse source ([datahub#19923](https://github.com/datahub-project/datahub/pull/19923), in
review) turns each **prompt version** into a versioned dataset, each **trace and generation**
into a run linked to the prompt version it used, and each **score** into a metric on that run.
Until it is released it is bundled in
[`ingestion/rca_ingestion/langfuse_source/`](../ingestion/rca_ingestion/langfuse_source) and used
as a custom source:

```yaml
# ingestion/recipes/langfuse.yml
source:
  type: rca_ingestion.langfuse_source.langfuse.LangfuseSource
  config:
    connection: { host: ${LANGFUSE_HOST}, public_key: ..., secret_key: ... }
    window: { start_time: "-8 days" }
```

### 3. What no connector can know

[`ingestion/rca_ingestion/context.py`](../ingestion/rca_ingestion/context.py) adds the rest
with the DataHub Python SDK:

- the two source datasets in S3, with descriptions and tags
- owner groups: Support Content, Knowledge Platform, AI Assistants
- a **deprecation** on the 2023 archive, with a note
- the domain *Customer Support AI*
- **lineage**: source dataset → Pinecone namespace → Langfuse prompt version

```python
UpstreamLineageClass(upstreams=[UpstreamClass(dataset=namespace_urn(prompt.config["namespace"]), ...)])
```

## Run it by hand

```bash
cd ingestion
.venv/bin/datahub ingest -c recipes/pinecone.yml
.venv/bin/python -m rca_ingestion.run langfuse
.venv/bin/python -m rca_ingestion.run context
```

Next: [06 · Explore the AI lineage](./06-lineage.md)
