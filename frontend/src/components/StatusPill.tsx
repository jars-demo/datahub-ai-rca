import type { ConnectionStatus } from '../api/types';

const LABELS: Record<ConnectionStatus, string> = {
    connected: 'Connected',
    failed: 'Failed',
    untested: 'Not tested',
    not_configured: 'Not set up',
};

export default function StatusPill({ status }: { status: ConnectionStatus }) {
    return (
        <span className={`status status-${status}`}>
            <span className="status-dot" />
            {LABELS[status]}
        </span>
    );
}
