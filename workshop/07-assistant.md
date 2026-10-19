# 07 · See the symptom (5 min)

## Do it

Open **Assistant** and ask: *How much does the Pro plan cost?*

The answer card shows the prompt version, the namespace it retrieved from, the model, and the
articles it used. Open **View trace in Langfuse**: this is a real call to your LLM, logged as a
new trace with the prompt version attached.

## What just happened

[`services/assistant.py`](../backend/app/services/assistant.py) is the whole RAG app:

1. fetch the prompt labelled `production` from Langfuse
2. search the Pinecone namespace named in that prompt's config
3. answer with the configured LLM through the neutral client interface
4. send a trace and a generation, linked to the prompt version, back to Langfuse

Use the thumbs to send a `user_feedback` score on the trace.

Next: [08 · Find the root cause](./08-investigate.md)
