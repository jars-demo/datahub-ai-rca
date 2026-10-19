import { ArrowRight, GitPullRequest } from '@phosphor-icons/react';
import { Link } from 'react-router-dom';

import ConnectorLogo from '../components/ConnectorLogo';
import { LANGFUSE_PR, PINECONE_PR } from '../site';

const STEPS = [
    { id: 'langfuse', name: 'Langfuse', title: 'Detect', text: 'Answer quality drops in production. Which prompt version was live?' },
    { id: 'pinecone', name: 'Pinecone', title: 'Retrieve', text: 'Which index and namespace did those answers come from?' },
    { id: 'datahub', name: 'DataHub', title: 'Trace', text: 'Follow lineage to the source data, its owners and its status.' },
    { id: 'llm', name: 'Any LLM', title: 'Explain', text: 'An agent walks the graph and names the cause, the owner and the fix.' },
];

const OUTCOMES = [
    'Seed Pinecone, Langfuse and DataHub with one realistic incident',
    'Load vector stores and LLM observability into DataHub with two connectors',
    'See one lineage graph from source documents to production traces',
    'Let an agent find the root cause with any LLM provider you choose',
    'Fix it, verify it, and read every line of code that made it work',
];

export default function HomePage() {
    return (
        <div className="page">
            <section className="home-intro">
                <div className="eyebrow">Hands-on workshop · 60 minutes</div>
                <h1 className="home-title">Why did our AI assistant get worse?</h1>
                <p className="home-lede">
                    A support assistant built on Pinecone and Langfuse starts giving wrong answers. Nothing
                    crashed and no alert fired. In this workshop you bring both systems into DataHub, connect
                    them with lineage, and let an agent trace the regression to its source.
                </p>
                <div className="row">
                    <Link to="/workshop" className="btn btn-primary">
                        Start the workshop <ArrowRight size={16} weight="bold" />
                    </Link>
                    <Link to="/concepts" className="btn btn-secondary">
                        Read the concepts
                    </Link>
                </div>
            </section>

            <section>
                <h2 className="section-title">How it works</h2>
                <div className="card steps">
                    {STEPS.map((step, i) => (
                        <div key={step.id} className="step">
                            <div className="step-head">
                                <ConnectorLogo id={step.id} name={step.name} small />
                                <span className="step-num">Step {i + 1}</span>
                            </div>
                            <h3>{step.title}</h3>
                            <p>{step.text}</p>
                        </div>
                    ))}
                </div>
            </section>

            <div className="two-col">
                <section className="card padded">
                    <h2 className="section-title">What you will do</h2>
                    <ul className="check-list">
                        {OUTCOMES.map((o) => (
                            <li key={o}>{o}</li>
                        ))}
                    </ul>
                </section>
                <section className="card padded">
                    <h2 className="section-title">The connectors behind it</h2>
                    <div className="provenance">
                        <div className="provenance-row">
                            <ConnectorLogo id="pinecone" name="Pinecone" small />
                            <div>
                                <div className="table-name">Pinecone source</div>
                                <div className="table-meta">
                                    Indexes, namespaces and inferred schemas. Merged and released.
                                </div>
                            </div>
                            <a className="pr-link merged" href={PINECONE_PR} target="_blank" rel="noreferrer">
                                <GitPullRequest size={14} /> #16472
                            </a>
                        </div>
                        <div className="provenance-row">
                            <ConnectorLogo id="langfuse" name="Langfuse" small />
                            <div>
                                <div className="table-name">Langfuse source</div>
                                <div className="table-meta">
                                    Prompt versions, traces, generations and scores. In review, bundled here.
                                </div>
                            </div>
                            <a className="pr-link open" href={LANGFUSE_PR} target="_blank" rel="noreferrer">
                                <GitPullRequest size={14} /> #19923
                            </a>
                        </div>
                    </div>
                    <Link to="/about" className="subtle-link">
                        Exact DataHub build and versions →
                    </Link>
                </section>
            </div>

            <section className="card padded">
                <h2 className="section-title">You need</h2>
                <div className="needs">
                    <div>
                        <strong>DataHub</strong>
                        <span>Running locally (quickstart). The workshop creates the token for you.</span>
                    </div>
                    <div>
                        <strong>Pinecone</strong>
                        <span>A free Starter account and an API key.</span>
                    </div>
                    <div>
                        <strong>Langfuse</strong>
                        <span>A free Langfuse Cloud project and its key pair.</span>
                    </div>
                    <div>
                        <strong>Any LLM</strong>
                        <span>Anthropic, OpenAI, Gemini, Groq, OpenRouter, Mistral, Ollama or your own endpoint.</span>
                    </div>
                </div>
            </section>
        </div>
    );
}
