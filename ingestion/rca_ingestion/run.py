"""Load the workshop metadata into DataHub.

    python -m rca_ingestion.run pinecone   # DataHub Pinecone source
    python -m rca_ingestion.run langfuse   # Langfuse source (PR #19923, bundled)
    python -m rca_ingestion.run context    # source datasets, owners, lineage

Credentials come from environment variables, the same ones the recipes reference:
DATAHUB_GMS_URL, DATAHUB_TOKEN, PINECONE_API_KEY, LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY,
LANGFUSE_SECRET_KEY.
"""

import argparse
import os
import sys
from pathlib import Path

from datahub.configuration.config_loader import load_config_file
from datahub.ingestion.run.pipeline import Pipeline

from rca_ingestion import context

RECIPES = Path(__file__).resolve().parent.parent / "recipes"


def run_recipe(name: str) -> int:
    config = load_config_file(RECIPES / f"{name}.yml")
    pipeline = Pipeline.create(config)
    pipeline.run()
    pipeline.pretty_print_summary()
    pipeline.raise_from_status()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=["pinecone", "langfuse", "context"])
    args = parser.parse_args()

    if args.step == "context":
        count = context.emit(os.environ["DATAHUB_GMS_URL"], os.environ.get("DATAHUB_TOKEN"))
        print(f"Emitted {count} metadata change proposals (sources, owners, lineage).")
        return 0
    return run_recipe(args.step)


if __name__ == "__main__":
    sys.exit(main())
