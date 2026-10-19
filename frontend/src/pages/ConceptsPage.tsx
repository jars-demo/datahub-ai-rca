import PageHeader from '../components/PageHeader';

const MODEL = [
    ['Pinecone index', 'Container', 'acme-support-kb'],
    ['Pinecone namespace', 'Dataset (with inferred schema)', 'acme-support-kb.help-center-2025'],
    ['Langfuse project', 'Container', 'your project'],
    ['Langfuse prompt version', 'Dataset, versioned', 'support-answer.v3'],
    ['Langfuse trace / generation', 'Data process instance (a run)', 'support-chat traces'],
    ['Langfuse score', 'Metric on the run', 'correctness, helpfulness'],
    ['Source documents', 'Dataset (added by the app)', 's3: acme-content/help-center/2025'],
];

const TOOLS = [
    ['quality_trend', 'Langfuse', 'Daily score averages, split by prompt version'],
    ['prompt_versions', 'Langfuse', 'Labels, config and the namespace each version retrieves from'],
    ['low_scoring_examples', 'Langfuse', 'Concrete failing questions and answers'],
    ['datahub_search', 'DataHub', 'Find datasets across s3, Pinecone and Langfuse'],
    ['datahub_entity', 'DataHub', 'Owners, deprecation, tags and domain'],
    ['datahub_lineage', 'DataHub', 'Walk upstream from a prompt version to its source data'],
    ['knowledge_base_lookup', 'Pinecone', 'Compare what two namespaces actually say'],
];

export default function ConceptsPage() {
    return (
        <div className="page narrow">
            <PageHeader title="Concepts" subtitle="The ideas behind the workshop, in the order you will meet them." />

            <section className="card padded prose">
                <h3>1. Why AI regressions are hard to debug</h3>
                <p>
                    A RAG assistant is a chain: source documents are embedded into a vector store, a prompt decides how to
                    retrieve and answer, and an observability tool records what happened. Each tool sees its own link.
                    When answers get worse, the cause is usually upstream of where the symptom shows up, and nobody has the
                    whole chain in one place.
                </p>
                <div className="chain">
                    <span>Source documents</span>
                    <span>→</span>
                    <span>Vector namespace</span>
                    <span>→</span>
                    <span>Prompt version</span>
                    <span>→</span>
                    <span>Answers and scores</span>
                </div>
            </section>

            <section className="card padded prose">
                <h3>2. Metadata as the missing link</h3>
                <p>
                    DataHub stores metadata about every system as entities with aspects (ownership, deprecation, schema,
                    tags) and lineage edges between them. Connectors read each system and emit that metadata. This is how
                    the two connectors in this workshop model Pinecone and Langfuse:
                </p>
                <table className="table">
                    <thead>
                        <tr>
                            <th>In the source system</th>
                            <th>In DataHub</th>
                            <th>In this workshop</th>
                        </tr>
                    </thead>
                    <tbody>
                        {MODEL.map(([a, b, c]) => (
                            <tr key={a}>
                                <td>{a}</td>
                                <td>{b}</td>
                                <td>
                                    <code>{c}</code>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </section>

            <section className="card padded prose">
                <h3>3. The scenario</h3>
                <p>
                    Acme Cloud's support assistant answers from its help center. Three days ago, prompt version 3 shipped
                    with a friendlier tone. Its config also pointed retrieval at <code>help-center-2023-archive</code>, a
                    namespace embedded from a deprecated 2023 export. Since then the assistant has been confidently quoting
                    2023 prices, refund windows and SSO rules. The correctness score fell; nothing errored.
                </p>
            </section>

            <section className="card padded prose">
                <h3>4. How the agent works</h3>
                <p>
                    The agent is a tool-use loop: the model decides which tool to call, the backend runs it, and the result
                    goes back to the model until it can answer. Every tool is read-only and returns links, so each claim in
                    the answer can be checked.
                </p>
                <table className="table">
                    <thead>
                        <tr>
                            <th>Tool</th>
                            <th>Reads</th>
                            <th>What it answers</th>
                        </tr>
                    </thead>
                    <tbody>
                        {TOOLS.map(([a, b, c]) => (
                            <tr key={a}>
                                <td>
                                    <code>{a}</code>
                                </td>
                                <td>{b}</td>
                                <td>{c}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </section>

            <section className="card padded prose">
                <h3>5. Bring your own model</h3>
                <p>
                    The assistant and the agent talk to one neutral interface. Anthropic uses its native SDK; every other
                    provider (OpenAI, Gemini, Groq, OpenRouter, Mistral, Together, DeepSeek, Ollama or any
                    OpenAI-compatible endpoint) goes through one adapter. Switch providers on the Connections page and run
                    the same investigation again. Embeddings stay inside Pinecone, so changing the LLM never means
                    re-embedding.
                </p>
            </section>
        </div>
    );
}
