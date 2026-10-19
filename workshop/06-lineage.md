# 06 · Explore the AI lineage (5 min)

## Do it

Open **AI lineage** in the app. Three columns, read live from DataHub:

```text
Source documents        Pinecone namespaces                  Langfuse prompt versions
Help Center (2025) ───▶ acme-support-kb.help-center-2025 ──▶ support-answer.v1
                                                         └─▶ support-answer.v2
Help Center Archive ──▶ acme-support-kb.help-center-      ──▶ support-answer.v3  (production)
(2023, deprecated)      2023-archive
```

The highlighted path runs back from the production prompt. It ends at a dataset marked
**deprecated**.

Click any node to open it in DataHub, then look at:

- the **Lineage** tab of `support-answer.v3` (upstream and downstream, including the runs)
- the **deprecation banner** and owners on *Help Center Archive (2023)*
- the inferred **schema** of a Pinecone namespace
- the **domain** *Customer Support AI*, which groups everything in the scenario

## What just happened

[`services/lineage.py`](../backend/app/services/lineage.py) walks upstream from each prompt
version, one hop at a time, with DataHub's `searchAcrossLineage` GraphQL query, and returns
nodes and edges for the page to draw.

Next: [07 · See the symptom](./07-assistant.md)
