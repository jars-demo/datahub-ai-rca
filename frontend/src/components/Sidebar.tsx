import {
    BookOpen,
    ChatCircleText,
    GraduationCap,
    House,
    Info,
    MagnifyingGlass,
    Plugs,
    TreeStructure,
} from '@phosphor-icons/react';
import type { Icon } from '@phosphor-icons/react';
import { NavLink } from 'react-router-dom';

import { useAbout } from '../hooks/useStatus';

type NavItem = { to: string; label: string; icon: Icon };

const GROUPS: { title: string; items: NavItem[] }[] = [
    {
        title: 'Workshop',
        items: [
            { to: '/', label: 'Home', icon: House },
            { to: '/workshop', label: 'Workshop', icon: GraduationCap },
            { to: '/concepts', label: 'Concepts', icon: BookOpen },
        ],
    },
    {
        title: 'App',
        items: [
            { to: '/assistant', label: 'Assistant', icon: ChatCircleText },
            { to: '/investigate', label: 'Investigate', icon: MagnifyingGlass },
            { to: '/lineage', label: 'AI lineage', icon: TreeStructure },
        ],
    },
    {
        title: 'Settings',
        items: [
            { to: '/connections', label: 'Connections', icon: Plugs },
            { to: '/about', label: 'About this build', icon: Info },
        ],
    },
];

export default function Sidebar() {
    const about = useAbout();
    const server = about?.datahub_server;

    return (
        <aside className="sidebar">
            <div className="brand">
                <img src="/logos/datahub.svg" alt="DataHub" />
                <div>
                    <div className="brand-name">AI Root Cause</div>
                    <div className="brand-sub">powered by DataHub</div>
                </div>
            </div>
            <nav className="nav">
                {GROUPS.map((group) => (
                    <div key={group.title} className="nav-group">
                        <div className="nav-section">{group.title}</div>
                        {group.items.map(({ to, label, icon: ItemIcon }) => (
                            <NavLink
                                key={to}
                                to={to}
                                end={to === '/'}
                                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
                            >
                                <ItemIcon size={18} weight="bold" />
                                {label}
                            </NavLink>
                        ))}
                    </div>
                ))}
            </nav>
            <NavLink to="/about" className="build-hint" title="DataHub server and connector provenance">
                <span className={server?.reachable ? 'dot ok' : 'dot'} />
                {server?.reachable ? (
                    <span>
                        DataHub {server.version} · <code>{server.commit?.slice(0, 7)}</code>
                    </span>
                ) : (
                    <span>DataHub not reachable</span>
                )}
            </NavLink>
        </aside>
    );
}
