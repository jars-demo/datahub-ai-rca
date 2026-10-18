import { Link } from 'react-router-dom';

import { connectionStatus } from '../api/types';
import ConnectorLogo from '../components/ConnectorLogo';
import PageHeader from '../components/PageHeader';
import StatusPill from '../components/StatusPill';
import { useConnections } from '../hooks/useConnections';

const STEPS = [
    {
        id: 'langfuse',
        name: 'Langfuse',
        title: 'Detect',
        text: 'Quality scores on production traces drop. Identify the prompt version that was live.',
    },
    {
        id: 'pinecone',
        name: 'Pinecone',
        title: 'Retrieve',
        text: 'Determine which index and namespace the affected answers were retrieved from.',
    },
    {
        id: 'datahub',
        name: 'DataHub',
        title: 'Trace',
        text: 'Follow lineage to the upstream source data, its owners and recent changes.',
    },
    {
        id: 'anthropic',
        name: 'Claude',
        title: 'Explain',
        text: 'An agent summarizes the root cause with supporting evidence and next steps.',
    },
];

export default function OverviewPage() {
    const { connections } = useConnections();
    const connected = connections.filter((c) => connectionStatus(c) === 'connected').length;
    const total = connections.length;
    const ready = total > 0 && connected === total;

    return (
        <div className="page">
            <PageHeader
                title="AI Root Cause Analysis"
                subtitle="Trace quality regressions in LLM applications back to their source, using DataHub lineage across your observability, retrieval and data systems."
            />

            <section className="card summary">
                <div>
                    <div className="summary-label">Setup</div>
                    <div className="summary-value">
                        {ready
                            ? 'All systems connected'
                            : `${connected} of ${total || 4} systems connected`}
                    </div>
                </div>
                <div className="summary-actions">
                    <a className="btn btn-secondary" href="/docs" target="_blank" rel="noreferrer">
                        API reference
                    </a>
                    <Link to={ready ? '/investigate' : '/connections'} className="btn btn-primary">
                        {ready ? 'Start investigation' : 'Configure connections'}
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

            <section>
                <h2 className="section-title">Connections</h2>
                <div className="card">
                    {connections.map((c) => (
                        <div key={c.id} className="table-row">
                            <ConnectorLogo id={c.id} name={c.name} small />
                            <div>
                                <div className="table-name">{c.name}</div>
                                <div className="table-meta">{c.role}</div>
                            </div>
                            <StatusPill status={connectionStatus(c)} />
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
}
