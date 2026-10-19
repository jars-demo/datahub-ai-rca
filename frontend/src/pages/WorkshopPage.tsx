import { ArrowLeft, ArrowRight, Check, FileText } from '@phosphor-icons/react';
import { useEffect, useState } from 'react';

import { api } from '../api/client';
import { useStatus } from '../hooks/useStatus';
import { useStoredState } from '../hooks/useStoredState';
import { REPO_URL } from '../site';
import { STEPS } from '../workshop/steps';

export default function WorkshopPage() {
    const { status, refresh } = useStatus();
    const [current, setCurrent] = useStoredState('workshop.current', 0);
    const [marked, setMarked] = useStoredState<string[]>('workshop.done', []);
    const [datahubUi, setDatahubUi] = useState('http://localhost:9002');

    useEffect(() => {
        api.listConnections()
            .then((cs) => setDatahubUi(cs.find((c) => c.id === 'datahub')?.values.ui_url || 'http://localhost:9002'))
            .catch(() => undefined);
    }, []);

    const index = Math.min(current, STEPS.length - 1);
    const step = STEPS[index];
    const isDone = (i: number) => STEPS[i].isDone?.(status) || marked.includes(STEPS[i].id);
    const doneCount = STEPS.filter((_, i) => isDone(i)).length;

    const go = (i: number) => {
        setCurrent(i);
        window.scrollTo({ top: 0 });
    };
    const completeAndNext = () => {
        setMarked((m) => (m.includes(step.id) ? m : [...m, step.id]));
        if (index < STEPS.length - 1) go(index + 1);
    };

    return (
        <div className="workshop">
            <aside className="workshop-steps card">
                <div className="workshop-progress">
                    <span className="summary-label">Progress</span>
                    <span className="muted">
                        {doneCount} / {STEPS.length}
                    </span>
                </div>
                <div className="progress-bar wide">
                    <span style={{ width: `${(doneCount / STEPS.length) * 100}%` }} />
                </div>
                <ol>
                    {STEPS.map((s, i) => (
                        <li key={s.id}>
                            <button type="button" className={i === index ? 'ws-step active' : 'ws-step'} onClick={() => go(i)}>
                                <span className={isDone(i) ? 'ws-num done' : 'ws-num'}>
                                    {isDone(i) ? <Check size={12} weight="bold" /> : i + 1}
                                </span>
                                <span className="ws-title">{s.title}</span>
                                <span className="ws-min">{s.minutes}m</span>
                            </button>
                        </li>
                    ))}
                </ol>
                <button
                    type="button"
                    className="btn btn-ghost reset-link"
                    onClick={() => {
                        setMarked([]);
                        go(0);
                    }}
                >
                    Reset progress
                </button>
            </aside>

            <article className="workshop-body">
                <div className="eyebrow">
                    Step {index + 1} of {STEPS.length} · {step.minutes} min
                </div>
                <h1 className="page-title">{step.title}</h1>
                <div className="card padded prose step-content">{step.body({ status, refresh, datahubUi })}</div>
                <div className="workshop-nav">
                    <button type="button" className="btn btn-secondary" onClick={() => go(index - 1)} disabled={index === 0}>
                        <ArrowLeft size={16} /> Previous
                    </button>
                    <a className="subtle-link" href={`${REPO_URL}/blob/main/workshop/${step.doc}`} target="_blank" rel="noreferrer">
                        <FileText size={14} /> Read this step on GitHub
                    </a>
                    <button type="button" className="btn btn-primary" onClick={completeAndNext}>
                        {index === STEPS.length - 1 ? 'Finish' : 'Done, next step'} <ArrowRight size={16} />
                    </button>
                </div>
            </article>
        </div>
    );
}
