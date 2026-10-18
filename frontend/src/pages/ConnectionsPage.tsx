import { WarningCircle } from '@phosphor-icons/react';

import { connectionStatus } from '../api/types';
import ConnectionCard from '../components/ConnectionCard';
import PageHeader from '../components/PageHeader';
import { useConnections } from '../hooks/useConnections';

export default function ConnectionsPage() {
    const { connections, loading, error, refresh } = useConnections();
    const connected = connections.filter((c) => connectionStatus(c) === 'connected').length;
    const total = connections.length;

    return (
        <div className="page">
            <PageHeader
                title="Connections"
                subtitle="Configure the systems used for analysis. Credentials are stored server-side and are never returned to the browser."
                actions={
                    total > 0 && (
                        <div className="progress">
                            <div className="progress-bar">
                                <span style={{ width: `${(connected / total) * 100}%` }} />
                            </div>
                            {connected} of {total} connected
                        </div>
                    )
                }
            />

            {error && (
                <div className="banner-error">
                    <WarningCircle size={20} weight="fill" />
                    Backend unreachable: {error}
                </div>
            )}

            {!loading && (
                <div className="connections-grid">
                    {connections.map((connection) => (
                        <ConnectionCard key={connection.id} connection={connection} onChanged={refresh} />
                    ))}
                </div>
            )}
        </div>
    );
}
