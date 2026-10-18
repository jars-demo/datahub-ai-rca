import type { CheckResult, Connection } from './types';

export class ApiError extends Error {
    constructor(
        public readonly status: number,
        message: string,
    ) {
        super(message);
    }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(path, {
        ...init,
        headers: { 'Content-Type': 'application/json', ...init?.headers },
    });
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const detail = typeof body?.detail === 'string' ? body.detail : response.statusText;
        throw new ApiError(response.status, detail);
    }
    return response.status === 204 ? (undefined as T) : response.json();
}

export const api = {
    listConnections: () => request<Connection[]>('/api/connections'),

    saveConnection: (id: string, values: Record<string, string>) =>
        request<Connection>(`/api/connections/${id}`, {
            method: 'PUT',
            body: JSON.stringify({ values }),
        }),

    testConnection: (id: string, values?: Record<string, string>) =>
        request<CheckResult>(`/api/connections/${id}/test`, {
            method: 'POST',
            body: JSON.stringify({ values: values ?? {} }),
        }),

    deleteConnection: (id: string) =>
        request<void>(`/api/connections/${id}`, { method: 'DELETE' }),
};
