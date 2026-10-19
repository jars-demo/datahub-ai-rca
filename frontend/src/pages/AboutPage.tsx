import { ArrowSquareOut, GitPullRequest } from '@phosphor-icons/react';

import PageHeader from '../components/PageHeader';
import { useAbout } from '../hooks/useStatus';
import { REPO_URL } from '../site';

export default function AboutPage() {
    const about = useAbout();
    const server = about?.datahub_server;

    return (
        <div className="page narrow">
            <PageHeader
                title="About this build"
                subtitle="Exactly what this workshop runs on, read live from the DataHub server and from the app's own build info."
            />

            <section className="card">
                <div className="kv-title">DataHub server</div>
                <dl className="kv">
                    <dt>Status</dt>
                    <dd>{server ? (server.reachable ? 'Reachable' : `Not reachable: ${server.error ?? ''}`) : '…'}</dd>
                    <dt>Version</dt>
                    <dd>{server?.version ?? '—'}</dd>
                    <dt>Commit</dt>
                    <dd>
                        {server?.commit_url ? (
                            <a href={server.commit_url} target="_blank" rel="noreferrer">
                                <code>{server.commit?.slice(0, 10)}</code> <ArrowSquareOut size={12} />
                            </a>
                        ) : (
                            '—'
                        )}
                    </dd>
                    <dt>Build</dt>
                    <dd>{server?.server_type ? `${server.server_type} build of datahub-project/datahub master` : '—'}</dd>
                    <dt>GMS</dt>
                    <dd>
                        <code>{server?.gms_url ?? '—'}</code>
                    </dd>
                </dl>
            </section>

            <section className="card">
                <div className="kv-title">Ingestion</div>
                <dl className="kv">
                    <dt>DataHub CLI / SDK</dt>
                    <dd>
                        <code>acryl-datahub {about?.acryl_datahub ?? ''}</code>, in its own environment (
                        <code>ingestion/</code>)
                    </dd>
                    <dt>Pinecone source</dt>
                    <dd>
                        {about && (
                            <>
                                <a className="pr-link merged" href={about.pinecone_source.url} target="_blank" rel="noreferrer">
                                    <GitPullRequest size={14} /> #{about.pinecone_source.pr} · {about.pinecone_source.status}
                                </a>{' '}
                                {about.pinecone_source.shipped_in}
                            </>
                        )}
                    </dd>
                    <dt>Langfuse source</dt>
                    <dd>
                        {about && (
                            <>
                                <a className="pr-link open" href={about.langfuse_source.url} target="_blank" rel="noreferrer">
                                    <GitPullRequest size={14} /> #{about.langfuse_source.pr} · {about.langfuse_source.status}
                                </a>{' '}
                                {about.langfuse_source.shipped_in} at <code>{about.langfuse_source.commit}</code>
                            </>
                        )}
                    </dd>
                </dl>
            </section>

            <section className="card padded prose">
                <h3>How the two connectors are used</h3>
                <p>
                    <strong>Pinecone</strong> holds the assistant's knowledge: the index <code>acme-support-kb</code> with
                    one namespace per help-center version. DataHub's Pinecone source turns the index into a container and
                    each namespace into a dataset with an inferred schema.
                </p>
                <p>
                    <strong>Langfuse</strong> holds the assistant's behaviour: the prompt <code>support-answer</code> with
                    three versions, and a week of traces, generations and scores. The Langfuse source turns each prompt
                    version into a versioned dataset, each trace and generation into a run linked to the prompt version it
                    used, and each score into a metric on that run.
                </p>
                <p>
                    The app then adds what neither tool knows: the source documents behind each namespace, owners, a
                    deprecation, and lineage from source to namespace to prompt version. That one graph is what lets the
                    agent explain the regression.
                </p>
                <p>
                    Source: <a href={REPO_URL}>{REPO_URL.replace('https://', '')}</a>
                </p>
            </section>
        </div>
    );
}
