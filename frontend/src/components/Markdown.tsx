import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function Markdown({ children }: { children: string }) {
    return (
        <div className="markdown">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    a: ({ href, children: label }) => (
                        <a href={href} target="_blank" rel="noreferrer">
                            {label}
                        </a>
                    ),
                }}
            >
                {children}
            </ReactMarkdown>
        </div>
    );
}
