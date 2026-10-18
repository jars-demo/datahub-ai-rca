import { CheckCircle, Eye, EyeSlash } from '@phosphor-icons/react';
import { useState } from 'react';

import type { FieldSpec } from '../api/types';

type Props = {
    connectionId: string;
    field: FieldSpec;
    value: string;
    secretSaved: boolean;
    onChange: (value: string) => void;
};

export default function FieldInput({ connectionId, field, value, secretSaved, onChange }: Props) {
    const [revealed, setRevealed] = useState(false);
    const isSecret = field.kind === 'secret';
    const inputId = `${connectionId}-${field.key}`;
    const placeholder = isSecret && secretSaved ? '••••••••••••' : field.placeholder;

    return (
        <div className="field">
            <label htmlFor={inputId}>
                {field.label}
                {!field.required && <span className="optional">Optional</span>}
            </label>
            <div className="input-wrap">
                <input
                    id={inputId}
                    className={isSecret ? 'input has-toggle' : 'input'}
                    type={isSecret && !revealed ? 'password' : field.kind === 'url' ? 'url' : 'text'}
                    value={value}
                    placeholder={placeholder}
                    autoComplete="off"
                    spellCheck={false}
                    onChange={(e) => onChange(e.target.value)}
                />
                {isSecret && (
                    <button
                        type="button"
                        className="input-toggle"
                        onClick={() => setRevealed((r) => !r)}
                        aria-label={revealed ? `Hide ${field.label}` : `Show ${field.label}`}
                    >
                        {revealed ? <EyeSlash size={18} /> : <Eye size={18} />}
                    </button>
                )}
            </div>
            {isSecret && secretSaved && !value ? (
                <div className="field-help saved">
                    <CheckCircle size={14} weight="fill" />
                    Saved. Leave blank to keep the current value.
                </div>
            ) : (
                field.help && <div className="field-help">{field.help}</div>
            )}
        </div>
    );
}
