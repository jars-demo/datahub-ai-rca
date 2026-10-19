# 09 · Fix and verify (5 min)

## Do it

1. In the prompt switcher (Workshop step 9, or the Assistant page), click **v2** to move the
   `production` label back.
2. Ask the assistant the same question. The answer now comes from `help-center-2025`: $49.
3. Optional: run the investigation again and see how the agent describes the current state.
4. Click **v3** to reset the scenario for the next person (or re-run the Langfuse seed step).

## What just happened

Moving a label is one Langfuse API call:

```http
PATCH /api/public/v2/prompts/support-answer/versions/2
{"newLabels": ["production"]}
```

The assistant always fetches the `production` label, so the rollback takes effect on the next
question with no deploy.

## The real fix

A rollback stops the bleeding. The lasting fix is upstream, and DataHub tells you who to talk
to: point v3's config at `help-center-2025`, ask the Knowledge Platform team to delete or
restrict the archive namespace, and consider a check that blocks prompts from retrieving from
deprecated datasets.

Next: [10 · Bring your own model](./10-bring-your-own-model.md)
