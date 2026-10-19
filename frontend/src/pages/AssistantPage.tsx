import { ArrowSquareOut, CircleNotch, PaperPlaneRight, ThumbsDown, ThumbsUp } from '@phosphor-icons/react';
import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import { api } from '../api/client';
import type { AssistantAnswer } from '../api/types';
import PageHeader from '../components/PageHeader';
import PromptSwitcher from '../components/PromptSwitcher';

export default function AssistantPage() {
    const [examples, setExamples] = useState<string[]>([]);
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState<AssistantAnswer | null>(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<boolean | null>(null);

    useEffect(() => {
        api.assistantExamples().then(setExamples).catch(() => setExamples([]));
    }, []);

    const ask = async (q: string) => {
        setQuestion(q);
        setBusy(true);
        setError(null);
        setFeedback(null);
        try {
            setAnswer(await api.ask(q));
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setBusy(false);
        }
    };

    const submit = (e: FormEvent) => {
        e.preventDefault();
        if (question.trim().length >= 3) void ask(question.trim());
    };

    const rate = async (helpful: boolean) => {
        if (!answer) return;
        setFeedback(helpful);
        await api.feedback(answer.trace_id, helpful).catch(() => setFeedback(null));
    };

    return (
        <div className="page">
            <PageHeader
                title="Support assistant"
                subtitle="The RAG app under investigation. Every answer uses the production prompt from Langfuse, retrieves from Pinecone, and is logged back to Langfuse as a trace."
            />

            <PromptSwitcher />

            <form className="card ask-box" onSubmit={submit}>
                <input
                    className="input ask-input"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask Acme Cloud support a question…"
                />
                <button type="submit" className="btn btn-primary" disabled={busy}>
                    {busy ? <CircleNotch size={16} className="spin" /> : <PaperPlaneRight size={16} />}
                    Ask
                </button>
            </form>
            <div className="chips">
                {examples.map((ex) => (
                    <button key={ex} type="button" className="chip-btn" onClick={() => ask(ex)} disabled={busy}>
                        {ex}
                    </button>
                ))}
            </div>

            {error && <div className="banner-error">{error}</div>}

            {answer && (
                <section className="card answer">
                    <div className="answer-meta">
                        <span className="tag">prompt v{answer.prompt_version}</span>
                        <span className="tag">
                            namespace <code>{answer.namespace}</code>
                        </span>
                        <span className="tag">
                            {answer.provider} · {answer.model}
                        </span>
                        <span className="muted">{(answer.latency_ms / 1000).toFixed(1)} s</span>
                    </div>
                    <p className="answer-text">{answer.answer}</p>
                    <div className="sources">
                        <div className="summary-label">Retrieved from Pinecone</div>
                        {answer.sources.map((s) => (
                            <div key={s.id} className="source">
                                <span>{s.title}</span>
                                <span className="muted">updated {s.updated}</span>
                                <span className="muted">score {s.score}</span>
                            </div>
                        ))}
                    </div>
                    <div className="answer-actions">
                        <a className="subtle-link" href={answer.trace_url} target="_blank" rel="noreferrer">
                            View trace in Langfuse <ArrowSquareOut size={12} />
                        </a>
                        <div className="row">
                            <span className="muted">Was this helpful?</span>
                            <button
                                type="button"
                                className={feedback === true ? 'icon-btn active' : 'icon-btn'}
                                onClick={() => rate(true)}
                                aria-label="Helpful"
                            >
                                <ThumbsUp size={16} />
                            </button>
                            <button
                                type="button"
                                className={feedback === false ? 'icon-btn active' : 'icon-btn'}
                                onClick={() => rate(false)}
                                aria-label="Not helpful"
                            >
                                <ThumbsDown size={16} />
                            </button>
                        </div>
                    </div>
                </section>
            )}
        </div>
    );
}
