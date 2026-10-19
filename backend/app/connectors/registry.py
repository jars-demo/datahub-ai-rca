from app.connectors.base import Connector
from app.connectors.datahub import DataHubConnector
from app.connectors.langfuse import LangfuseConnector
from app.connectors.llm import LLMConnector
from app.connectors.pinecone import PineconeConnector

# Order here is the order shown in the UI.
CONNECTORS: dict[str, Connector] = {
    c.id: c
    for c in (
        PineconeConnector(),
        LangfuseConnector(),
        DataHubConnector(),
        LLMConnector(),
    )
}
