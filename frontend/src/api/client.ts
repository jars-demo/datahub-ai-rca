import type {
    About,
    AppStatus,
    AssistantAnswer,
    CheckResult,
    Connection,
    LineageGraph,
    PromptState,
} from './types';

export class ApiError extends Error {
    readonly status: number;

    constructor(status: number, message: string) {
        super(message);
        this.status = status;
    }
}

async function errorFrom(response: Response): Promise<ApiError> {
    const body = await response.json().catch(() => ({}));
    const detail = typeof body?.detail === 'string' ? body.detail : response.statusText;
    return new ApiError(response.status, detail);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(path, {
        ...init,
        headers: { 'Content-Type': 'application/json', ...init?.headers },
    });
    if (!response.ok) throw await errorFrom(response);
    return response.status === 204 ? (undefined as T) : response.json();
}

const post = <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) });

/** POST and read a server-sent event stream, calling onEvent for every `data:` message. */
export async function streamEvents<E>(path: string, body: unknown, onEvent: (event: E) => void): Promise<void> {
    const response = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body ?? {}),
    });
    if (!response.ok || !response.body) throw await errorFrom(response);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let boundary = buffer.indexOf('\n\n');
        while (boundary !== -1) {
            const chunk = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            const data = chunk
                .split('\n')
                .filter((line) => line.startsWith('data: '))
                .map((line) => line.slice(6))
                .join('\n');
            if (data) onEvent(JSON.parse(data) as E);
            boundary = buffer.indexOf('\n\n');
        }
    }
}

export const api = {
    status: () => request<AppStatus>('/api/status'),
    about: () => request<About>('/api/about'),

    listConnections: () => request<Connection[]>('/api/connections'),
    saveConnection: (id: string, values: Record<string, string>) =>
        request<Connection>(`/api/connections/${id}`, { method: 'PUT', body: JSON.stringify({ values }) }),
    testConnection: (id: string, values?: Record<string, string>) =>
        post<CheckResult>(`/api/connections/${id}/test`, { values: values ?? {} }),
    deleteConnection: (id: string) => request<void>(`/api/connections/${id}`, { method: 'DELETE' }),
    createDataHubToken: (username: string, password: string) =>
        post<Connection>('/api/connections/datahub/token', { username, password }),

    assistantExamples: () => request<string[]>('/api/assistant/examples'),
    ask: (question: string) => post<AssistantAnswer>('/api/assistant/ask', { question }),
    feedback: (traceId: string, helpful: boolean) =>
        post<void>('/api/assistant/feedback', { trace_id: traceId, helpful }),
    promptState: () => request<PromptState>('/api/assistant/prompt'),
    setProduction: (version: number) => post<PromptState>('/api/assistant/prompt/production', { version }),

    investigateSuggestions: () => request<string[]>('/api/investigate/suggestions'),
    lineage: () => request<LineageGraph>('/api/lineage'),
};
