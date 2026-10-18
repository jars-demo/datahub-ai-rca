export type FieldKind = 'text' | 'url' | 'secret';

export type FieldSpec = {
    key: string;
    label: string;
    kind: FieldKind;
    required: boolean;
    placeholder: string;
    help: string;
    default: string | null;
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
    configured: boolean;
    last_check: CheckResult | null;
};

export type ConnectionStatus = 'connected' | 'failed' | 'untested' | 'not_configured';

export function connectionStatus(connection: Connection): ConnectionStatus {
    if (!connection.configured) return 'not_configured';
    if (!connection.last_check) return 'untested';
    return connection.last_check.ok ? 'connected' : 'failed';
}
