export type FieldKind = 'text' | 'url' | 'secret' | 'select';

export type FieldSpec = {
    key: string;
    label: string;
    kind: FieldKind;
    required: boolean;
    placeholder: string;
    help: string;
    default: string | null;
    env: string | null;
    options: { value: string; label: string }[];
};

export type DetailValue = string | number | boolean | string[];

export type CheckResult = {
    ok: boolean;
    message: string;
    details: Record<string, DetailValue>;
    latency_ms: number;
    tested_at: number;
};

export type Connection = {
    id: string;
    name: string;
    role: string;
    description: string;
    docs_url: string;
    fields: FieldSpec[];
    values: Record<string, string>;
    secrets_set: string[];
    from_env: string[];
    configured: boolean;
    last_check: CheckResult | null;
};

export type ConnectionStatus = 'connected' | 'failed' | 'untested' | 'not_configured';

export function connectionStatus(connection: Connection): ConnectionStatus {
    if (!connection.configured) return 'not_configured';
    if (!connection.last_check) return 'untested';
    return connection.last_check.ok ? 'connected' : 'failed';
}

export type SeedStepStatus = 'done' | 'pending' | 'blocked' | 'unknown';

export type AppStatus = {
    connections: Record<string, { configured: boolean; ok: boolean }>;
    seed: Record<string, SeedStepStatus>;
};

export type LogEvent =
    | { type: 'start'; step: string }
    | { type: 'log'; level: 'info' | 'success' | 'error' | 'detail'; message: string }
    | { type: 'end'; step: string; ok: boolean };

export type Source = { id: string; title: string; updated: string; score: number };

export type AssistantAnswer = {
    answer: string;
    prompt_version: number;
    namespace: string;
    sources: Source[];
    trace_id: string;
    trace_url: string;
    model: string;
    provider: string;
    latency_ms: number;
};

export type PromptState = {
    name: string;
    url: string | null;
    versions: { version: number; labels: string[]; commit_message: string | null; namespace: string | null }[];
};

export type AgentEvent =
    | { type: 'start'; provider: string; model: string }
    | { type: 'note'; text: string }
    | { type: 'tool_call'; id: string; name: string; arguments: Record<string, unknown> }
    | { type: 'tool_result'; id: string; name: string; ok: boolean; summary: string; data: unknown }
    | { type: 'answer'; markdown: string }
    | { type: 'done'; steps: number; seconds: number; input_tokens: number; output_tokens: number; model: string }
    | { type: 'error'; message: string };

export type LineageNode = {
    urn: string;
    name: string;
    platform: string | null;
    stage: 'source' | 'vector' | 'prompt';
    description: string;
    owners: string[];
    deprecated: boolean;
    deprecation_note: string;
    tags: string[];
    url: string;
    version?: number;
    production?: boolean;
    traffic?: number;
};

export type LineageGraph = {
    stages: string[];
    nodes: LineageNode[];
    edges: { source: string; target: string }[];
    domain: string;
};

export type About = {
    datahub_server: {
        gms_url: string;
        reachable: boolean;
        version?: string;
        commit?: string;
        commit_url?: string | null;
        server_type?: string;
        error?: string;
    };
    acryl_datahub: string;
    pinecone_source: ConnectorProvenance;
    langfuse_source: ConnectorProvenance & { commit: string };
};

export type ConnectorProvenance = {
    pr: number;
    status: string;
    url: string;
    shipped_in: string;
};
