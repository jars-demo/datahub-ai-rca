import { Check, Copy } from '@phosphor-icons/react';
import { useState } from 'react';

export default function CodeBlock({ code, label }: { code: string; label?: string }) {
    const [copied, setCopied] = useState(false);

    const copy = async () => {
        try {
            await navigator.clipboard.writeText(code);
            setCopied(true);
            window.setTimeout(() => setCopied(false), 1500);
        } catch {
            // Clipboard can be blocked (http, permissions); the text is still selectable.
        }
    };

    return (
        <div className="code-block">
            {label && <div className="code-label">{label}</div>}
            <pre>
                <code>{code}</code>
            </pre>
            <button type="button" className="code-copy" onClick={copy} aria-label="Copy to clipboard">
                {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
        </div>
    );
}
