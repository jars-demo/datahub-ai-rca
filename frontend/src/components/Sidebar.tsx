import { House, MagnifyingGlass, Plugs, TreeStructure } from '@phosphor-icons/react';
import type { Icon } from '@phosphor-icons/react';
import { NavLink } from 'react-router-dom';

type NavItem = {
    to: string;
    label: string;
    icon: Icon;
    soon?: boolean;
};

const WORKSPACE: NavItem[] = [
    { to: '/', label: 'Overview', icon: House },
    { to: '/investigate', label: 'Investigate', icon: MagnifyingGlass, soon: true },
    { to: '/lineage', label: 'AI lineage', icon: TreeStructure, soon: true },
];

const SETTINGS: NavItem[] = [{ to: '/connections', label: 'Connections', icon: Plugs }];

function NavGroup({ title, items }: { title: string; items: NavItem[] }) {
    return (
        <>
            <div className="nav-section">{title}</div>
            {items.map(({ to, label, icon: ItemIcon, soon }) => (
                <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
                >
                    <ItemIcon size={18} weight="bold" />
                    {label}
                    {soon && <span className="soon">Soon</span>}
                </NavLink>
            ))}
        </>
    );
}

export default function Sidebar() {
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
                <NavGroup title="Workspace" items={WORKSPACE} />
                <NavGroup title="Settings" items={SETTINGS} />
            </nav>
            <div className="sidebar-footer">
                <a href="/docs" target="_blank" rel="noreferrer">
                    API reference
                </a>
            </div>
        </aside>
    );
}
