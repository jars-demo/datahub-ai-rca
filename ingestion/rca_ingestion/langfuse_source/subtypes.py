"""Langfuse subtypes added to `datahub.ingestion.source.common.subtypes` by PR #19923.

The released `acryl-datahub` package does not include them yet, so they are defined here.
Remove this module once the connector ships in a DataHub release.
"""

from enum import Enum


class DatasetSubTypes(str, Enum):
    LANGFUSE_PROMPT = "Langfuse Prompt"


class MLAssetSubTypes(str, Enum):
    LANGFUSE_PROJECT = "Langfuse Project"
    LANGFUSE_TRACE = "Langfuse Trace"
    LANGFUSE_GENERATION = "Langfuse Generation"
