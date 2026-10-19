# Langfuse source (bundled)

This is the DataHub Langfuse ingestion source from
[datahub-project/datahub#19923](https://github.com/datahub-project/datahub/pull/19923),
copied unchanged except for two things:

- imports point at `rca_ingestion.langfuse_source` instead of `datahub.ingestion.source.langfuse`
- `subtypes.py` defines the four Langfuse subtypes that the PR adds to
  `datahub.ingestion.source.common.subtypes`

It runs on the released `acryl-datahub` package as a custom source:

```yaml
source:
  type: rca_ingestion.langfuse_source.langfuse.LangfuseSource
```

Once the PR is merged and released, delete this folder and use `type: langfuse` in
[`recipes/langfuse.yml`](../../recipes/langfuse.yml).
