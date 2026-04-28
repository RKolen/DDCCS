import React from 'react';
import { Navigation } from '../organisms/Navigation';
import type { NavLink } from '../organisms/Navigation';

interface BaseTemplateProps {
  currentPath?: string;
  campaignTitle?: string;
  children: React.ReactNode;
}

const NAV_LINKS: Omit<NavLink, 'active'>[] = [
  { label: 'Dashboard',  path: '/' },
  { label: 'Characters', path: '/characters' },
  { label: 'Stories',    path: '/stories' },
  { label: 'Search',     path: '/search' },
  { label: 'NPCs',       path: '/npcs' },
];

export function BaseTemplate({
  currentPath = '/',
  campaignTitle,
  children,
}: BaseTemplateProps): React.ReactElement {
  const links: NavLink[] = NAV_LINKS.map(l => ({
    ...l,
    active: l.path === currentPath || (l.path !== '/' && currentPath.startsWith(l.path)),
  }));

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--color-bg-base)' }}>
      <Navigation campaignTitle={campaignTitle} links={links} />
      <main style={{ flex: 1, overflowY: 'auto' }}>
        {children}
      </main>
    </div>
  );
}
