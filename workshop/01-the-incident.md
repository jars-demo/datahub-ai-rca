# 01 · The incident (5 min)

Acme Cloud's support assistant answers customers from the help center. It is a standard RAG
application:

```text
help-center articles ──embed──▶ Pinecone namespace ──retrieve──▶ prompt (Langfuse) ──▶ answer
                                                                       │
                                                         traces + scores (Langfuse)
```

Three days ago, answer quality dropped. Customers are told the Pro plan costs $39 (it is $49),
that annual plans are non-refundable (they are refunded pro rata), and that SSO needs
Enterprise (it is on Pro). Nothing errored and no alert fired.

## Why this is hard

- **Langfuse** shows the correctness score falling and which prompt version was live, but not
  where that prompt's knowledge comes from.
- **Pinecone** stores vectors in namespaces, but knows nothing about where the documents came
  from, who owns them, or whether they are still valid.
- The **source documents** live somewhere else again, owned by a different team.

The cause sits upstream of the symptom, across three systems. **DataHub** is where those systems
meet: one metadata graph with lineage, ownership and status across all of them.

## What you will build

By the end you will have Pinecone and Langfuse metadata in DataHub, connected by lineage, and an
agent that walks that graph to explain the regression, with any LLM you choose.

Next: [02 · Connect your systems](./02-connect.md)
