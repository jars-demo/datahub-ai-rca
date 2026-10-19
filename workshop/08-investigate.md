# 08 · Find the root cause (10 min)

## Do it

Open **Investigate** and ask: *Why did the support assistant's answer quality drop this week?*

Expand each step in the timeline to see exactly what the agent read.

## What a good investigation looks like

1. **quality_trend** (Langfuse): correctness around 0.9 on v2, far lower on v3, starting three
   days ago
2. **prompt_versions** (Langfuse): v3 is in production, and its config retrieves from
   `help-center-2023-archive`
3. **datahub_lineage** (DataHub): upstream of `support-answer.v3` is that namespace, and
   upstream of it is *Help Center Archive (2023)*
4. **datahub_entity** (DataHub): that dataset is **deprecated**, owned by Support Content
5. **knowledge_base_lookup** (Pinecone): the two namespaces disagree on price, refunds and SSO

The answer ends with the root-cause chain, the owners to contact and the fix, with links into
DataHub and Langfuse.

## What just happened

The agent is a provider-neutral tool-use loop
([`agent/runner.py`](../backend/app/agent/runner.py)): the model chooses a tool, the backend
runs it, the result goes back, until the model can answer. All seven tools are read-only and
return links ([`agent/tools.py`](../backend/app/agent/tools.py)), so every claim can be checked.

Try the other suggested questions too.

Next: [09 · Fix and verify](./09-fix.md)
