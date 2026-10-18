import { ArrowSquareOut, CircleNotch, Trash } from '@phosphor-icons/react';
import { useState } from 'react';
import type { FormEvent } from 'react';

import { api } from '../api/client';
import { connectionStatus } from '../api/types';
import type { CheckResult, Connection } from '../api/types';
import CheckResultPanel from './CheckResultPanel';
import ConnectorLogo from './ConnectorLogo';
import FieldInput from './FieldInput';
import StatusPill from './StatusPill';

type Props = {
    connection: Connection;
    onChanged: () => Promise<void>;
};

type Busy = 'save' | 'test' | 'remove' | null;

export default function ConnectionCard({ connection, onChanged }: Props) {
    const [values, setValues] = useState<Record<string, string>>(connection.values);
    const [busy, setBusy] = useState<Busy>(null);
    const [result, setResult] = useState<CheckResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    const shownResult = result ?? connection.last_check;

    const run = async (kind: Exclude<Busy, null>, action: () => Promise<void>) => {
        setBusy(kind);
        setError(null);
        try {
            await action();
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Something went wrong.');
        } finally {
            setBusy(null);
        }
    };

    const saveAndTest = (event: FormEvent) => {
        event.preventDefault();
        void run('save', async () => {
            const saved = await api.saveConnection(connection.id, values);
            setValues(saved.values);
            setResult(await api.testConnection(connection.id));
            await onChanged();
        });
    };

    const testOnly = () =>
        run('test', async () => {
            setResult(await api.testConnection(connection.id, values));
        });

    const remove = () => {
        if (!window.confirm(`Remove the saved ${connection.name} settings?`)) return;
        void run('remove', async () => {
            await api.deleteConnection(connection.id);
            setResult(null);
            await onChanged();
            const defaults = Object.fromEntries(
                connection.fields.map((f) => [f.key, f.kind === 'secret' ? '' : (f.default ?? '')]),
            );
            setValues(defaults);
        });
    };

    return (
        <form className="card conn-card" onSubmit={saveAndTest}>
            <div className="conn-head">
                <ConnectorLogo id={connection.id} name={connection.name} />
                <div>
                    <div className="conn-title">
                        <h2>{connection.name}</h2>
                        <span className="tag">{connection.role}</span>
                    </div>
                    <p className="conn-desc">{connection.description}</p>
                </div>
                <StatusPill status={connectionStatus(connection)} />
            </div>

            <div className="conn-form">
                {connection.fields.map((field) => (
                    <FieldInput
                        key={field.key}
                        connectionId={connection.id}
                        field={field}
                        value={values[field.key] ?? ''}
                        secretSaved={connection.secrets_set.includes(field.key)}
                        onChange={(value) => setValues((v) => ({ ...v, [field.key]: value }))}
                    />
                ))}
            </div>

            {error && <div className="check fail check-message">{error}</div>}
            {!error && shownResult && <CheckResultPanel result={shownResult} />}

            <div className="conn-actions">
                <a className="docs" href={connection.docs_url} target="_blank" rel="noreferrer">
                    Documentation <ArrowSquareOut size={14} />
                </a>
                {connection.configured && (
                    <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={remove}
                        disabled={busy !== null}
                        aria-label={`Remove ${connection.name} settings`}
                    >
                        <Trash size={16} />
                    </button>
                )}
                <button type="button" className="btn btn-secondary" onClick={testOnly} disabled={busy !== null}>
                    {busy === 'test' && <CircleNotch size={16} className="spin" />}
                    Test
                </button>
                <button type="submit" className="btn btn-primary" disabled={busy !== null}>
                    {busy === 'save' && <CircleNotch size={16} className="spin" />}
                    Save &amp; test
                </button>
            </div>
        </form>
    );
}
