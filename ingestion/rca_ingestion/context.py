"""Adds what the connectors cannot know: where the knowledge came from, who owns it, and how the
pieces connect.

- the two help-center source datasets (one of them deprecated)
- owner groups and a domain
- lineage: source dataset -> Pinecone namespace -> Langfuse prompt version
"""

from collections.abc import Iterable

from datahub.emitter.mce_builder import (
    make_dataset_urn,
    make_domain_urn,
    make_group_urn,
    make_tag_urn,
)
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    CorpGroupInfoClass,
    DatasetLineageTypeClass,
    DatasetPropertiesClass,
    DeprecationClass,
    DomainPropertiesClass,
    DomainsClass,
    GlobalTagsClass,
    OwnerClass,
    OwnershipClass,
    OwnershipTypeClass,
    StatusClass,
    TagAssociationClass,
    UpstreamClass,
    UpstreamLineageClass,
)

from rca_ingestion.scenario import prompt_versions, scenario

DOMAIN_ID = "customer-support-ai"


def _ownership(group: str) -> OwnershipClass:
    return OwnershipClass(
        owners=[OwnerClass(owner=make_group_urn(group), type=OwnershipTypeClass.TECHNICAL_OWNER)]
    )


def namespace_urn(namespace: str) -> str:
    index = scenario()["pinecone"]["index"]
    return make_dataset_urn("pinecone", f"{index}.{namespace}")


def prompt_urn(version: int) -> str:
    name = scenario()["langfuse"]["prompt_name"]
    return make_dataset_urn("langfuse", f"{name}.v{version}")


def build_mcps() -> Iterable[MetadataChangeProposalWrapper]:
    s = scenario()
    dh = s["datahub"]
    namespaces = s["pinecone"]["namespaces"]
    domain_urn = make_domain_urn(DOMAIN_ID)
    in_domain = DomainsClass(domains=[domain_urn])

    yield MetadataChangeProposalWrapper(
        entityUrn=domain_urn,
        aspect=DomainPropertiesClass(
            name=dh["domain"],
            description="Assistants that answer Acme Cloud customers, and the data they depend on.",
        ),
    )

    for group_id, display_name in dh["groups"].items():
        yield MetadataChangeProposalWrapper(
            entityUrn=make_group_urn(group_id),
            aspect=CorpGroupInfoClass(
                displayName=display_name, admins=[], members=[], groups=[]
            ),
        )

    for source in dh["sources"].values():
        urn = make_dataset_urn(source["platform"], source["name"])
        yield from MetadataChangeProposalWrapper.construct_many(
            entityUrn=urn,
            aspects=[
                StatusClass(removed=False),
                DatasetPropertiesClass(
                    name=source["display_name"], description=source["description"]
                ),
                _ownership(source["owner_group"]),
                GlobalTagsClass(
                    tags=[TagAssociationClass(tag=make_tag_urn(t)) for t in source["tags"]]
                ),
                in_domain,
                DeprecationClass(
                    deprecated="deprecation_note" in source,
                    note=source.get("deprecation_note", ""),
                    actor=make_group_urn(source["owner_group"]),
                ),
            ],
        )
        # Each source dataset is embedded into its own Pinecone namespace.
        yield from MetadataChangeProposalWrapper.construct_many(
            entityUrn=namespace_urn(namespaces[source["namespace"]]),
            aspects=[
                UpstreamLineageClass(
                    upstreams=[UpstreamClass(dataset=urn, type=DatasetLineageTypeClass.TRANSFORMED)]
                ),
                _ownership(dh["pinecone_owner_group"]),
                in_domain,
            ],
        )

    # A prompt version retrieves from the namespace named in its Langfuse config.
    for prompt in prompt_versions():
        yield from MetadataChangeProposalWrapper.construct_many(
            entityUrn=prompt_urn(prompt["version"]),
            aspects=[
                UpstreamLineageClass(
                    upstreams=[
                        UpstreamClass(
                            dataset=namespace_urn(prompt["config"]["namespace"]),
                            type=DatasetLineageTypeClass.VIEW,
                        )
                    ]
                ),
                _ownership(dh["prompt_owner_group"]),
                in_domain,
            ],
        )


def emit(server: str, token: str | None) -> int:
    emitter = DatahubRestEmitter(gms_server=server, token=token or None)
    emitter.test_connection()
    count = 0
    for mcp in build_mcps():
        emitter.emit(mcp)
        count += 1
    return count
