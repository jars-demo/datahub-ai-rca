import asyncio

from pinecone import Pinecone
from pinecone.exceptions import (
    ForbiddenException,
    NotFoundException,
    PineconeApiException,
    UnauthorizedException,
)

from app.connectors.base import CheckResult, Connector, DetailValue, FieldSpec


class PineconeConnector(Connector):
    id = "pinecone"
    name = "Pinecone"
    role = "Vector store"
    description = "Vector indexes and namespaces used for retrieval."
    docs_url = "https://docs.pinecone.io/guides/projects/manage-api-keys"
    fields = [
        FieldSpec(
            key="api_key",
            label="API key",
            kind="secret",
            placeholder="pcsk_…",
            help="Pinecone console → API Keys. The free Starter plan is enough.",
            env="PINECONE_API_KEY",
        ),
        FieldSpec(
            key="index_name",
            label="Index name",
            required=False,
            default="acme-support-kb",
            placeholder="acme-support-kb",
            help="The workshop creates and seeds this index. The test also reports its vector count.",
            env="PINECONE_INDEX",
        ),
    ]

    async def _test(self, values: dict[str, str]) -> CheckResult:
        # The Pinecone SDK is synchronous; keep it off the event loop.
        return await asyncio.to_thread(self._test_sync, values)

    def _test_sync(self, values: dict[str, str]) -> CheckResult:
        pc = Pinecone(api_key=values["api_key"], timeout=15.0)
        try:
            names = list(pc.list_indexes().names())
        except (UnauthorizedException, ForbiddenException):
            return CheckResult(ok=False, message="Pinecone rejected the API key.")
        except PineconeApiException as e:
            return CheckResult(ok=False, message=f"Pinecone API error ({e.status}).")
        except OSError as e:
            return CheckResult(ok=False, message=f"Could not reach Pinecone: {e}")

        details: dict[str, DetailValue] = {"indexes": names}
        index_name = values.get("index_name")
        if not index_name:
            return CheckResult(ok=True, message=f"Connected. {len(names)} index(es) found.", details=details)

        try:
            desc = pc.describe_index(index_name)
            stats = pc.Index(host=desc.host).describe_index_stats()
        except NotFoundException:
            return CheckResult(
                ok=True,
                message=f"Connected. Index '{index_name}' does not exist yet; seeding creates it.",
                details=details,
            )
        except PineconeApiException as e:
            return CheckResult(
                ok=False,
                message=f"Could not read index '{index_name}' ({e.status}).",
                details=details,
            )

        details.update(
            {
                "dimension": int(desc.dimension or 0),
                "metric": str(desc.metric),
                "vectors": int(stats.total_vector_count or 0),
                "namespaces": sorted(stats.namespaces or {}),
            }
        )
        return CheckResult(
            ok=True,
            message=f"Connected to '{index_name}' · {details['vectors']:,} vectors.",
            details=details,
        )
