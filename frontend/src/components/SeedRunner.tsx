import { CheckCircle, CircleNotch, Play, WarningCircle } from '@phosphor-icons/react';
import { useEffect, useRef, useState } from 'react';

import { streamEvents } from '../api/client';
import type { LogEvent, SeedStepStatus } from '../api/types';

type Props = {
    step: string;
    label: string;
    status: SeedStepStatus | undefined;
    onFinished: () => void;
};

type Line = { level: string; message: string };

export default function SeedRunner({ step, label, status, onFinished }: Props) {
    const [running, setRunning] = useState(false);
    const [lines, setLines] = useState<Line[]>([]);
    const [result, setResult] = useState<boolean | null>(null);
    const consoleRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        consoleRef.current?.scrollTo({ top: consoleRef.current.scrollHeight });
    }, [lines]);

    const run = async () => {
        setRunning(true);
        setLines([]);
        setResult(null);
        try {
            await streamEvents<LogEvent>(`/api/seed/${step}`, {}, (e) => {
                if (e.type === 'log') setLines((l) => [...l, { level: e.level, message: e.message }]);
                if (e.type === 'end') setResult(e.ok);
            });
        } catch (e) {
            setLines((l) => [...l, { level: 'error', message: e instanceof Error ? e.message : String(e) }]);
            setResult(false);
        } finally {
            setRunning(false);
            onFinished();
        }
    };

    const blocked = status === 'blocked';
    return (
        <div className="card runner">
            <div className="runner-head">
                <div className="runner-status">
                    {status === 'done' && result !== false && (
                        <span className="status status-connected">
                            <span className="status-dot" />
                            Seeded
                        </span>
                    )}
                    {blocked && (
                        <span className="status status-not_configured">
                            <span className="status-dot" />
                            Configure the connections first
                        </span>
                    )}
                    {result === false && (
                        <span className="status status-failed">
                            <WarningCircle size={14} weight="fill" /> Failed, see the log
                        </span>
                    )}
                    {result === true && (
                        <span className="status status-connected">
                            <CheckCircle size={14} weight="fill" /> Done
                        </span>
                    )}
                </div>
                <button type="button" className="btn btn-primary" onClick={run} disabled={running || blocked}>
                    {running ? <CircleNotch size={16} className="spin" /> : <Play size={16} weight="fill" />}
                    {status === 'done' ? `Run again: ${label}` : label}
                </button>
            </div>
            {lines.length > 0 && (
                <div className="log-console" ref={consoleRef}>
                    {lines.map((line, i) => (
                        <div key={i} className={`log-line log-${line.level}`}>
                            {line.message}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
