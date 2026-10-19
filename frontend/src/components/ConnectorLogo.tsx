import { Cpu, Database } from '@phosphor-icons/react';

const LOGOS: Record<string, string> = {
    pinecone: '/logos/pinecone.png',
    langfuse: '/logos/langfuse.svg',
    datahub: '/logos/datahub.svg',
};

type Props = {
    id: string;
    name: string;
    small?: boolean;
};

export default function ConnectorLogo({ id, name, small = false }: Props) {
    const src = LOGOS[id];
    const size = small ? 16 : 22;
    return (
        <div className={small ? 'logo-tile small' : 'logo-tile'}>
            {src ? (
                <img src={src} alt={`${name} logo`} />
            ) : id === 'llm' ? (
                <Cpu size={size} aria-label={name} />
            ) : (
                <Database size={size} aria-label={name} />
            )}
        </div>
    );
}
