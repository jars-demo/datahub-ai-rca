import { ArrowsClockwise, CircleNotch } from '@phosphor-icons/react';
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';

import { api } from '../api/client';
import type { LineageGraph, LineageNode } from '../api/types';
import ConnectorLogo from '../components/ConnectorLogo';
import PageHeader from '../components/PageHeader';

const STAGE_TITLES: Record<string, string> = {
    source: 'Source documents',
    vector: 'Pinecone namespaces',
    prompt: 'Langfuse prompt versions',
};

type Edge = { d: string; hot: boolean };

function NodeCard({ node }: { node: LineageNode }) {
    const classes = ['lineage-node'];
    if (node.deprecated) classes.push('deprecated');
    if (node.production) classes.push('production');
    return (
        <a className={classes.join(' ')} href={node.url} target="_blank" rel="noreferrer" data-urn={node.urn}>
            <div className="lineage-node-head">
                <ConnectorLogo id={node.platform ?? ''} name={node.platform ?? ''} small />
                <span className="lineage-node-name">{node.name}</span>
            </div>
            <div className="lineage-node-meta">
                {node.production && <span className="tag tag-live">production</span>}
                {node.deprecated && <span className="tag tag-warn">deprecated</span>}
                {node.owners[0] && <span className="muted">{node.owners[0]}</span>}
                {node.traffic != null && node.traffic > 0 && <span className="muted">{node.traffic} runs</span>}
            </div>
        </a>
    );
}

export default function LineagePage() {
    const [graph, setGraph] = useState<LineageGraph | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [edges, setEdges] = useState<Edge[]>([]);
    const boardRef = useRef<HTMLDivElement>(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            setGraph(await api.lineage());
            setError(null);
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void load();
    }, [load]);

    const layout = useCallback(() => {
        const board = boardRef.current;
        if (!board || !graph) return;
        const origin = board.getBoundingClientRect();
        const box = (urn: string) =>
            board.querySelector<HTMLElement>(`[data-urn="${CSS.escape(urn)}"]`)?.getBoundingClientRect();
        const live = new Set(graph.nodes.filter((n) => n.production).map((n) => n.urn));
        // Highlight everything upstream of the production prompt.
        const hot = new Set(live);
        for (let i = 0; i < 3; i++) graph.edges.forEach((e) => hot.has(e.target) && hot.add(e.source));
        setEdges(
            graph.edges.flatMap((e) => {
                const a = box(e.source);
                const b = box(e.target);
                if (!a || !b) return [];
                const x1 = a.right - origin.left;
                const y1 = a.top + a.height / 2 - origin.top;
                const x2 = b.left - origin.left;
                const y2 = b.top + b.height / 2 - origin.top;
                const mid = (x1 + x2) / 2;
                return [{ d: `M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}`, hot: hot.has(e.source) && hot.has(e.target) }];
            }),
        );
    }, [graph]);

    useLayoutEffect(() => {
        layout();
        window.addEventListener('resize', layout);
        return () => window.removeEventListener('resize', layout);
    }, [layout]);

    const empty = graph && graph.nodes.length === 0;

    return (
        <div className="page">
            <PageHeader
                title="AI lineage"
                subtitle="Read live from DataHub: which source data feeds which Pinecone namespace, and which Langfuse prompt version retrieves from it. Click any node to open it in DataHub."
                actions={
                    <button type="button" className="btn btn-secondary" onClick={load} disabled={loading}>
                        {loading ? <CircleNotch size={16} className="spin" /> : <ArrowsClockwise size={16} />}
                        Refresh
                    </button>
                }
            />

            {error && <div className="banner-error">{error}</div>}
            {empty && (
                <div className="banner-info">Nothing in DataHub yet. Run the “Load it all into DataHub” step in the workshop.</div>
            )}

            {graph && !empty && (
                <section className="card lineage">
                    <div className="lineage-board" ref={boardRef}>
                        <svg className="lineage-edges" aria-hidden="true">
                            {edges.map((e, i) => (
                                <path key={i} d={e.d} className={e.hot ? 'hot' : ''} />
                            ))}
                        </svg>
                        {graph.stages.map((stage) => (
                            <div key={stage} className="lineage-col">
                                <div className="summary-label">{STAGE_TITLES[stage] ?? stage}</div>
                                {graph.nodes
                                    .filter((n) => n.stage === stage)
                                    .map((n) => (
                                        <NodeCard key={n.urn} node={n} />
                                    ))}
                            </div>
                        ))}
                    </div>
                    <div className="lineage-legend muted">
                        <span>
                            <i className="legend-hot" /> path behind the production prompt
                        </span>
                        <span>Domain: {graph.domain}</span>
                    </div>
                </section>
            )}
        </div>
    );
}
