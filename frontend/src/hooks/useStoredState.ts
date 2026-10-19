import { useEffect, useState } from 'react';

/** useState that survives reloads. Falls back to memory when storage is unavailable. */
export function useStoredState<T>(key: string, initial: T) {
    const [value, setValue] = useState<T>(() => {
        try {
            const raw = window.localStorage.getItem(key);
            return raw === null ? initial : (JSON.parse(raw) as T);
        } catch {
            return initial;
        }
    });

    useEffect(() => {
        try {
            window.localStorage.setItem(key, JSON.stringify(value));
        } catch {
            // Private mode or blocked storage: keep the in-memory value.
        }
    }, [key, value]);

    return [value, setValue] as const;
}
