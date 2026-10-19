# 03 · Seed the knowledge base (5 min)

## Do it

On the Workshop page, click **Seed Pinecone**, or run `make seed-pinecone`.

## What just happened

The app created the index `acme-support-kb` with Pinecone's **integrated embedding model**
(`llama-text-embed-v2`), so text goes in and text comes out. No separate embedding provider is
needed, which is why changing your LLM later never means re-embedding.

It then embedded two versions of the help center into two namespaces:

| Namespace | Source | Content |
|---|---|---|
| `help-center-2025` | [`data/kb/help-center-2025.json`](../data/kb/help-center-2025.json) | Current and correct |
| `help-center-2023-archive` | [`data/kb/help-center-2023-archive.json`](../data/kb/help-center-2023-archive.json) | A frozen 2023 export: old prices, 14-day refunds, Enterprise-only SSO |

```python
pc.create_index_for_model(
    name="acme-support-kb", cloud="aws", region="us-east-1",
    embed={"model": "llama-text-embed-v2", "field_map": {"text": "chunk_text"}},
)
index.upsert_records(namespace="help-center-2025", records=[{"_id": "pricing", "chunk_text": "...", ...}])
index.search(namespace="help-center-2025", query={"inputs": {"text": question}, "top_k": 3})
```

Every Pinecone call is in [`services/knowledge_base.py`](../backend/app/services/knowledge_base.py).

## Try

Open the index in the Pinecone console and compare the `pricing` record in both namespaces.

Next: [04 · Seed a week of traffic](./04-seed-langfuse.md)
