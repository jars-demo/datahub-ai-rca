import { CheckCircle, XCircle } from '@phosphor-icons/react';

import type { CheckResult, DetailValue } from '../api/types';

const MAX_LIST_ITEMS = 4;

function formatDetail(key: string, value: DetailValue): string {
    const label = key.replace(/_/g, ' ');
    if (Array.isArray(value)) {
        if (value.length === 0) return `${label}: none`;
        const shown = value.slice(0, MAX_LIST_ITEMS).join(', ');
        const more = value.length > MAX_LIST_ITEMS ? ` +${value.length - MAX_LIST_ITEMS}` : '';
        return `${label}: ${shown}${more}`;
    }
    return `${label}: ${typeof value === 'number' ? value.toLocaleString() : String(value)}`;
}

export default function CheckResultPanel({ result }: { result: CheckResult }) {
    const entries = Object.entries(result.details);
    return (
        <div className={result.ok ? 'check ok' : 'check fail'} role="status">
            <div className="check-message">
                {result.ok ? <CheckCircle size={18} weight="fill" /> : <XCircle size={18} weight="fill" />}
                {result.message}
                {result.latency_ms > 0 && <span className="latency">{result.latency_ms} ms</span>}
            </div>
            {entries.length > 0 && (
                <div className="check-details">
                    {entries.map(([key, value]) => (
                        <span key={key} className="tag">
                            {formatDetail(key, value)}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}
