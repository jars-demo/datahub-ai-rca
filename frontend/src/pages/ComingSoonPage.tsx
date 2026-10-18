import type { Icon } from '@phosphor-icons/react';

import PageHeader from '../components/PageHeader';

type Props = {
    title: string;
    subtitle: string;
    icon: Icon;
    description: string;
};

export default function ComingSoonPage({ title, subtitle, icon: PageIcon, description }: Props) {
    return (
        <div className="page">
            <PageHeader title={title} subtitle={subtitle} />
            <div className="card empty">
                <div className="empty-icon">
                    <PageIcon size={26} weight="bold" />
                </div>
                <h2>Coming next</h2>
                <p>{description}</p>
            </div>
        </div>
    );
}
