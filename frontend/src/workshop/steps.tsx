// The workshop steps shown on the Workshop page. Keep in sync with workshop/*.md.

import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import type { AppStatus } from '../api/types';
import CodeBlock from '../components/CodeBlock';
import PromptSwitcher from '../components/PromptSwitcher';
import SeedRunner from '../components/SeedRunner';
import { LANGFUSE_PR, PINECONE_PR } from '../site';

export type StepContext = {
    status: AppStatus | null;
    refresh: () => void;
    datahubUi: string;
};

export type WorkshopStep = {
    id: string;
    title: string;
    minutes: number;
    doc: string;
    body: (ctx: StepContext) => ReactNode;
    isDone?: (status: AppStatus | null) => boolean;
};

const allConfigured = (s: AppStatus | null) =>
    !!s && Object.values(s.connections).every((c) => c.configured);

export const STEPS: WorkshopStep[] = [
    {
        id: 'story',
        title: 'The incident',
        minutes: 5,
        doc: '01-the-incident.md',
        body: () => (
            <>
                <p>
                    Acme Cloud's support assistant answers customers from the help center. It is a classic RAG app:
                    articles are embedded into <strong>Pinecone</strong>, a prompt managed in <strong>Langfuse</strong>{' '}
                    decides how to retrieve and answer, and every conversation is traced and scored in Langfuse.
                </p>
                <p>
                    Three days ago, answer quality dropped. Customers are being told the wrong prices and refund rules.
                    No error, no alert. Your job: find out why, prove it, and fix it.
                </p>
                <div className="callout">
                    Each tool only sees its own piece. Langfuse sees scores fall, Pinecone sees vectors, and neither knows
                    where the documents came from or who owns them. <strong>DataHub</strong> is where the pieces meet.
                </div>
            </>
        ),
    },
    {
        id: 'connect',
        title: 'Connect your systems',
        minutes: 10,
        doc: '02-connect.md',
        isDone: allConfigured,
        body: ({ status }) => (
            <>
                <p>
                    Open <Link to="/connections">Connections</Link> and fill in four cards. Or put the same values in{' '}
                    <code>.env</code> (see <code>.env.example</code>) and restart the backend.
                </p>
                <ol>
                    <li>
                        <strong>Pinecone</strong>: your API key. The index is created for you.
                    </li>
                    <li>
                        <strong>Langfuse</strong>: host, public key and secret key of a fresh project.
                    </li>
                    <li>
                        <strong>DataHub</strong>: click <em>Create token with the default login</em>.
                    </li>
                    <li>
                        <strong>LLM provider</strong>: pick any provider and paste its key. Anthropic, OpenAI, Gemini,
                        Groq, OpenRouter, Mistral, Ollama and custom endpoints all work.
                    </li>
                </ol>
                <ConnectionChecklist status={status} />
            </>
        ),
    },
    {
        id: 'pinecone',
        title: 'Seed the knowledge base',
        minutes: 5,
        doc: '03-seed-pinecone.md',
        isDone: (s) => s?.seed.pinecone === 'done',
        body: ({ status, refresh }) => (
            <>
                <p>
                    Create the index <code>acme-support-kb</code> with Pinecone's integrated embedding model, and embed
                    two versions of the help center into two namespaces:
                </p>
                <ul>
                    <li>
                        <code>help-center-2025</code>: the current, correct articles
                    </li>
                    <li>
                        <code>help-center-2023-archive</code>: a frozen 2023 export with outdated prices and policies
                    </li>
                </ul>
                <SeedRunner step="pinecone" label="Seed Pinecone" status={status?.seed.pinecone} onFinished={refresh} />
                <CodeBlock label="Or from a terminal" code="make seed-pinecone" />
            </>
        ),
    },
    {
        id: 'langfuse',
        title: 'Seed a week of traffic',
        minutes: 5,
        doc: '04-seed-langfuse.md',
        isDone: (s) => s?.seed.langfuse === 'done',
        body: ({ status, refresh }) => (
            <>
                <p>
                    Create the prompt <code>support-answer</code> with three versions, then send seven days of traces,
                    generations and scores. Version 3 went live three days ago with a friendlier tone, and its config
                    quietly points retrieval at the archive namespace.
                </p>
                <SeedRunner step="langfuse" label="Seed Langfuse" status={status?.seed.langfuse} onFinished={refresh} />
                <p className="muted">
                    Open your Langfuse project and look at the traces and the correctness score. You can see the drop,
                    but not the cause.
                </p>
            </>
        ),
    },
    {
        id: 'datahub',
        title: 'Bring it into DataHub',
        minutes: 10,
        doc: '05-ingest.md',
        isDone: (s) => s?.seed.datahub === 'done',
        body: ({ status, refresh }) => (
            <>
                <p>Three ingestion runs, each a few seconds:</p>
                <ol>
                    <li>
                        The <a href={PINECONE_PR}>Pinecone source</a> (merged, in <code>acryl-datahub</code>) turns the
                        index into a container and each namespace into a dataset with an inferred schema.
                    </li>
                    <li>
                        The <a href={LANGFUSE_PR}>Langfuse source</a> (merged, bundled in this repo until it is released) turns prompt
                        versions into versioned datasets, traces and generations into runs linked to the prompt version
                        they used, and scores into metrics.
                    </li>
                    <li>
                        The app adds what no connector can know: the source documents, their owners, the deprecation of
                        the 2023 archive, and lineage from source to namespace to prompt.
                    </li>
                </ol>
                <SeedRunner step="datahub" label="Ingest into DataHub" status={status?.seed.datahub} onFinished={refresh} />
                <CodeBlock label="The same recipes run from a terminal" code={'cd ingestion\n.venv/bin/datahub ingest -c recipes/pinecone.yml\n.venv/bin/python -m rca_ingestion.run langfuse'} />
            </>
        ),
    },
    {
        id: 'lineage',
        title: 'Explore the AI lineage',
        minutes: 5,
        doc: '06-lineage.md',
        body: ({ datahubUi }) => (
            <>
                <p>
                    Open <Link to="/lineage">AI lineage</Link>. Follow the highlighted path back from the production
                    prompt. Then open the same entities in DataHub and look at the lineage tab, the owners and the
                    deprecation banner.
                </p>
                <div className="row">
                    <Link to="/lineage" className="btn btn-primary">
                        Open AI lineage
                    </Link>
                    <a className="btn btn-secondary" href={`${datahubUi}/search?query=support-answer`} target="_blank" rel="noreferrer">
                        Search DataHub
                    </a>
                </div>
            </>
        ),
    },
    {
        id: 'assistant',
        title: 'See the symptom',
        minutes: 5,
        doc: '07-assistant.md',
        body: () => (
            <>
                <p>
                    Open the <Link to="/assistant">Assistant</Link> and ask “How much does the Pro plan cost?”. Note the
                    prompt version and the namespace on the answer, then open the trace in Langfuse. This is a real call
                    to your LLM, logged as a new trace.
                </p>
                <Link to="/assistant" className="btn btn-primary">
                    Open the assistant
                </Link>
            </>
        ),
    },
    {
        id: 'investigate',
        title: 'Find the root cause',
        minutes: 10,
        doc: '08-investigate.md',
        body: () => (
            <>
                <p>
                    Open <Link to="/investigate">Investigate</Link> and ask why quality dropped. Watch the agent's tool
                    calls: scores from Langfuse, prompt config, lineage and ownership from DataHub, then a direct
                    comparison of the two Pinecone namespaces.
                </p>
                <Link to="/investigate" className="btn btn-primary">
                    Start the investigation
                </Link>
            </>
        ),
    },
    {
        id: 'fix',
        title: 'Fix and verify',
        minutes: 5,
        doc: '09-fix.md',
        body: () => (
            <>
                <p>
                    Roll back: move the <code>production</code> label to v2. Then ask the assistant the same question and
                    compare. Move it back to v3 to reset the scenario for the next person.
                </p>
                <PromptSwitcher />
            </>
        ),
    },
    {
        id: 'byom',
        title: 'Swap the model',
        minutes: 5,
        doc: '10-bring-your-own-model.md',
        body: () => (
            <>
                <p>
                    On <Link to="/connections">Connections</Link>, switch the LLM provider (for example to Groq, Gemini or
                    a local Ollama model) and run the same investigation. The tools, the data and the lineage stay the
                    same; only the reasoning engine changes.
                </p>
                <p className="muted">Compare the answers, the number of tool calls and the tokens used.</p>
            </>
        ),
    },
];

function ConnectionChecklist({ status }: { status: AppStatus | null }) {
    if (!status) return null;
    const names: Record<string, string> = { pinecone: 'Pinecone', langfuse: 'Langfuse', datahub: 'DataHub', llm: 'LLM provider' };
    return (
        <div className="checklist">
            {Object.entries(status.connections).map(([id, c]) => (
                <span key={id} className={`status ${c.configured ? 'status-connected' : 'status-not_configured'}`}>
                    <span className="status-dot" />
                    {names[id] ?? id}
                </span>
            ))}
        </div>
    );
}
