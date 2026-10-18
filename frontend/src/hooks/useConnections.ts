import { useCallback, useEffect, useState } from 'react';

import { api } from '../api/client';
import type { Connection } from '../api/types';

export function useConnections() {
    const [connections, setConnections] = useState<Connection[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        try {
            setConnections(await api.listConnections());
            setError(null);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Could not reach the backend.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void refresh();
    }, [refresh]);

    const replace = useCallback((updated: Connection) => {
        setConnections((current) => current.map((c) => (c.id === updated.id ? updated : c)));
    }, []);

    return { connections, loading, error, refresh, replace };
}
