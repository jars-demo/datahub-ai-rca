import { ArrowSquareOut, CircleNotch } from '@phosphor-icons/react';
import { useCallback, useEffect, useState } from 'react';

import { api } from '../api/client';
import type { PromptState } from '../api/types';

/** Shows which Langfuse prompt version is in production and lets you move the label. */
export default function PromptSwitcher({ onChange }: { onChange?: (state: PromptState) => void }) {
    const [state, setState] = useState<PromptState | null>(null);
    const [busy, setBusy] = useState<number | null>(null);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        try {
            const s = await api.promptState();
            setState(s);
            setError(null);
            onChange?.(s);
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }, [onChange]);

    useEffect(() => {
        void load();
    }, [load]);

    const promote = async (version: number) => {
        setBusy(version);
        try {
            const s = await api.setProduction(version);
            setState(s);
            onChange?.(s);
        } catch (e) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setBusy(null);
        }
    };

    if (error) return <div className="banner-error">{error}</div>;
    if (!state) return null;
    if (state.versions.length === 0) {
        return <div className="banner-info">No prompt versions yet. Run the Langfuse seed step in the workshop.</div>;
    }

    return (
        <div className="card prompt-switcher">
            <div className="prompt-switcher-head">
                <div>
                    <div className="summary-label">Langfuse prompt</div>
                    <div className="summary-value">
                        <code>{state.name}</code>
                    </div>
                </div>
                {state.url && (
                    <a className="subtle-link" href={state.url} target="_blank" rel="noreferrer">
                        Open in Langfuse <ArrowSquareOut size={12} />
                    </a>
                )}
            </div>
            <div className="versions">
                {state.versions.map((v) => {
                    const live = v.labels.includes('production');
                    return (
                        <button
                            key={v.version}
                            type="button"
                            className={live ? 'version live' : 'version'}
                            onClick={() => !live && promote(v.version)}
                            disabled={busy !== null}
                            title={live ? 'In production' : `Move the production label to v${v.version}`}
                        >
                            <div className="version-top">
                                <strong>v{v.version}</strong>
                                {busy === v.version ? (
                                    <CircleNotch size={14} className="spin" />
                                ) : (
                                    live && <span className="tag tag-live">production</span>
                                )}
                            </div>
                            <div className="version-ns">
                                <code>{v.namespace}</code>
                            </div>
                            <div className="version-msg">{v.commit_message}</div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
