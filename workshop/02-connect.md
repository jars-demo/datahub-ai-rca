# 02 · Connect your systems (10 min)

## Do it

Open **Connections** (<http://localhost:3300/connections>) and fill in four cards. Each one has
**Test** (try unsaved values) and **Save & test**.

| Card | What to enter |
|---|---|
| Pinecone | Your API key. The index `acme-support-kb` is created for you in step 3. |
| Langfuse | Host (`https://cloud.langfuse.com`, or `https://us.cloud.langfuse.com`), public key, secret key |
| DataHub | Click **Create token with the default login**. GMS and UI URLs default to localhost. |
| LLM provider | Pick a provider, paste its key, and choose a model (Anthropic defaults to `claude-opus-5-5`) |

Prefer files? Put the same values in `.env` (see [`.env.example`](../.env.example)) and restart
the backend. Fields set by `.env` show a small `.env` badge; anything you save in the UI wins.

```bash
make datahub-token    # the same token button, from a terminal
make status           # which connections are configured, which seed steps are done
```

## What just happened

Each card is generated from one Python class in
[`backend/app/connectors/`](../backend/app/connectors). A connector declares its fields once;
the API, the form and the `.env` binding all come from that declaration:

```python
class PineconeConnector(Connector):
    fields = [
        FieldSpec(key="api_key", label="API key", kind="secret", env="PINECONE_API_KEY"),
        ...
    ]

    async def _test(self, values): ...   # list indexes, describe the workshop index
```

Secrets are stored in `backend/.data/connections.json` (owner-only permissions, gitignored) and
are never returned by the API: secret fields always come back blank.

The DataHub token is created exactly as you would by hand: log in to the frontend, then call the
`createAccessToken` GraphQL mutation (see
[`services/datahub_api.py`](../backend/app/services/datahub_api.py)).

Next: [03 · Seed the knowledge base](./03-seed-pinecone.md)
