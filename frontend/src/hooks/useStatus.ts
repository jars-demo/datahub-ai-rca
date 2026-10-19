import { useCallback, useEffect, useState } from 'react';

import { api } from '../api/client';
import type { About, AppStatus } from '../api/types';

export function useStatus() {
    const [status, setStatus] = useState<AppStatus | null>(null);
    const [loading, setLoading] = useState(true);

    const refresh = useCallback(async () => {
        try {
            setStatus(await api.status());
        } catch {
            setStatus(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void refresh();
    }, [refresh]);

    return { status, loading, refresh };
}

export function useAbout() {
    const [about, setAbout] = useState<About | null>(null);
    useEffect(() => {
        api.about()
            .then(setAbout)
            .catch(() => setAbout(null));
    }, []);
    return about;
}
