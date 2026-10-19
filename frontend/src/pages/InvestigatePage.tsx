import { CheckCircle, CircleNotch, MagnifyingGlass, WarningCircle } from '@phosphor-icons/react';
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import { api, streamEvents } from '../api/client';
import type { AgentEvent } from '../api/types';
import Markdown from '../components/Markdown';
import PageHeader from '../components/PageHeader';

const TOOL_LABELS: Record<string, string> = {
    quality_trend: 'Langfuse · quality trend',
    prompt_versions: 'Langfuse · prompt versions',
    low_scoring_examples: 'Langfuse · failing examples',
    datahub_search: 'DataHub · search',
    datahub_entity: 'DataHub · entity details',
    datahub_lineage: 'DataHub · lineage',
    knowledge_base_lookup: 'Pinecone · namespace lookup',
};

type Step =
    | { kind: 'note'; text: string }
    | {
          kind: 'tool';
          id: string;
          name: string;
          args: Record<string, unknown>;
          result?: { ok: boolean; summary: string; data: unknown };
      };

function argSummary(args: Record<string, unknown>): string {
    return Object.entries(args)
        .map(([k, v]) => `${k}: ${typeof v === 'string' ? v : JSON.stringify(v)}`)
        .join(' · ');
}

export default function InvestigatePage() {
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [question, setQuestion] = useState('');
    const [steps, setSteps] = useState<Step[]>([]);
    const [answer, setAnswer] = useState<string | null>(null);
    const [meta, setMeta] = useState<{ provider?: string; model?: string; done?: AgentEvent & { type: 'done' } }>({});
    const [error, setError] = useState<string | null>(null);
    const [running, setRunning] = useState(false);

    useEffect(() => {
        api.investigateSuggestions()
            .then((s) => {
                setSuggestions(s);
                setQuestion((q) => q || s[0] || '');
            })
            .catch(() => setSuggestions([]));
    }, []);

    const run = async (q: string) => {
        setQuestion(q);
        setRunning(true);
        setSteps([]);
        setAnswer(null);
        setError(null);
        setMeta({});
        try {
            await streamEvents<AgentEvent>('/api/investigate', { question: q }, (e) => {
                if (e.type === 'start') setMeta({ provider: e.provider, model: e.model });
                if (e.type === 'note') setSteps((s) => [...s, { kind: 'note', text: e.text }]);
                if (e.type === 'tool_call')
                    setSteps((s) => [...s, { kind: 'tool', id: e.id, name: e.name, args: e.arguments }]);
                if (e.type === 'tool_result')
                    setSteps((s) =>
                        s.map((step) =>
                            step.kind === 'tool' && step.id === e.id
                                ? { ...step, result: { ok: e.ok, summary: e.summary, data: e.data } }
                                : step,
                        ),
                    );
                if (e.type === 'answer') setAnswer(e.markdown);
                if (e.type === 'done') setMeta((m) => ({ ...m, done: e }));
                if (e.type === 'error') setError(e.message);
            });
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setRunning(false);
        }
    };

    const submit = (e: FormEvent) => {
        e.preventDefault();
        if (question.trim().length >= 5) void run(question.trim());
    };

    return (
        <div className="page">
            <PageHeader
                title="Investigate"
                subtitle="Ask a question. The agent reads Langfuse, Pinecone and DataHub with read-only tools and explains what it found, with links to the evidence."
            />

            <form className="card ask-box" onSubmit={submit}>
                <input
                    className="input ask-input"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Why did answer quality drop this week?"
                />
                <button type="submit" className="btn btn-primary" disabled={running}>
                    {running ? <CircleNotch size={16} className="spin" /> : <MagnifyingGlass size={16} />}
                    Investigate
                </button>
            </form>
            <div className="chips">
                {suggestions.map((s) => (
                    <button key={s} type="button" className="chip-btn" onClick={() => run(s)} disabled={running}>
                        {s}
                    </button>
                ))}
            </div>

            {(steps.length > 0 || running) && (
                <section className="card timeline">
                    <div className="timeline-head">
                        <span className="summary-label">Investigation</span>
                        {meta.provider && (
                            <span className="tag">
                                {meta.provider} · {meta.model}
                            </span>
                        )}
                    </div>
                    {steps.map((step, i) =>
                        step.kind === 'note' ? (
                            <div key={i} className="timeline-note">
                                {step.text}
                            </div>
                        ) : (
                            <details key={step.id} className="timeline-step">
                                <summary>
                                    {!step.result ? (
                                        <CircleNotch size={16} className="spin" />
                                    ) : step.result.ok ? (
                                        <CheckCircle size={16} weight="fill" className="ok" />
                                    ) : (
                                        <WarningCircle size={16} weight="fill" className="fail" />
                                    )}
                                    <span className="timeline-tool">{TOOL_LABELS[step.name] ?? step.name}</span>
                                    <span className="timeline-args">{argSummary(step.args)}</span>
                                    {step.result && <span className="timeline-summary">{step.result.summary}</span>}
                                </summary>
                                {step.result?.data != null && (
                                    <pre className="json">{JSON.stringify(step.result.data, null, 2)}</pre>
                                )}
                            </details>
                        ),
                    )}
                    {running && !answer && <div className="timeline-note muted">Thinking…</div>}
                </section>
            )}

            {error && <div className="banner-error">{error}</div>}

            {answer && (
                <section className="card padded">
                    <Markdown>{answer}</Markdown>
                    {meta.done && (
                        <div className="answer-footer muted">
                            {meta.done.steps} model turns · {meta.done.seconds} s ·{' '}
                            {(meta.done.input_tokens + meta.done.output_tokens).toLocaleString()} tokens ·{' '}
                            {meta.done.model}
                        </div>
                    )}
                </section>
            )}
        </div>
    );
}
