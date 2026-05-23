/**
 * GlobalTopbar — site-wide header rendered on every page.
 *
 * Layout:
 *   [ DD brand ] [ nav links ]    |   [ Campaign chip ]   |   [ Search ]
 *
 * Search behaviour:
 *   - On /search/, the topbar search field is always empty — the query lives
 *     in the page's own SearchBar.
 *   - On other pages, typing and pressing Enter navigates to /search/?q=...
 */

import * as React from 'react';
import { Link, navigate } from 'gatsby';
interface GatsbyLocation { pathname: string; search: string; }
import { useTopbar } from './TopbarContext';
import { Icon, SearchField } from '../console/atoms';
import type { IconName } from '../console/menuData';

interface GlobalTopbarProps {
  location?: GatsbyLocation;
}

/* ── Nav items ── */

interface NavItem {
  label: string;
  path: string;
  icon: IconName;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Console',    path: '/',             icon: 'drawer'   },
  { label: 'Characters', path: '/characters/',  icon: 'char'     },
  { label: 'NPCs',       path: '/npcs/',        icon: 'npc'      },
  { label: 'Stories',    path: '/stories/',     icon: 'story'    },
  { label: 'Party',      path: '/party/',       icon: 'flag'     },
  { label: 'Search',     path: '/search/',      icon: 'search'   },
];

/* ── Campaign chip (reads TopbarContext) ── */

function TopbarCampaignChip(): React.ReactElement {
  const { campaigns, activeCampaignName, onSwitchCampaign } = useTopbar();
  const [open, setOpen] = React.useState(false);
  const active = campaigns.find(c => c.name === activeCampaignName) ?? campaigns[0] ?? null;
  const activeName = active?.name ?? null;

  if (!active) {
    return (
      <div className="topbar-chip topbar-chip--empty">
        <span className="chip-eyebrow">Active campaign</span>
        <span className="chip-name">—</span>
      </div>
    );
  }

  return (
    <div className="topbar-chip" style={{ position: 'relative' }}>
      <button
        type="button"
        className="topbar-chip-btn"
        onClick={() => campaigns.length > 1 && setOpen(o => !o)}
        style={{ cursor: campaigns.length > 1 ? 'pointer' : 'default' }}
      >
        <span className="chip-dot" />
        <span className="chip-meta">
          <span className="chip-eyebrow">Active campaign</span>
          <span className="chip-name">{active.name}</span>
        </span>
        <span className="chip-status">active</span>
        {campaigns.length > 1 && <Icon name="chevronDown" size={12} />}
      </button>
      {open && campaigns.length > 1 && (
        <div className="campaign-chip-pop">
          <div className="chip-pop-header">Switch campaign</div>
          {campaigns.map(c => (
            <button
              key={c.id}
              type="button"
              className={`chip-pop-item${c.name === activeName ? ' active' : ''}`}
              onClick={() => { onSwitchCampaign(c.name); setOpen(false); }}
            >
              <span className="chip-pop-name">{c.name}</span>
              {c.campaignStatus && (
                <span className="chip-pop-stats">{c.campaignStatus}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Topbar ── */

export function GlobalTopbar({ location }: GlobalTopbarProps): React.ReactElement {
  const onSearchPage = location?.pathname.startsWith('/search') ?? false;

  /* When on /search/, the topbar field stays empty — the page's own SearchBar
     is the primary input. On all other pages it acts as a "go to search" shortcut. */
  const syncValue = onSearchPage ? '' : undefined;

  return (
    <header className="global-topbar">
      <div className="global-topbar-left">
        <Link to="/" className="topbar-brand" aria-label="DDCCS home">
          <span className="brand-mark">DD</span>
        </Link>
        <nav className="topbar-nav" aria-label="Site navigation">
          {NAV_ITEMS.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className="topbar-nav-link"
              activeClassName="topbar-nav-link--active"
            >
              <Icon name={item.icon} size={13} />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </div>

      <div className="global-topbar-center">
        <TopbarCampaignChip />
      </div>

      <div className="global-topbar-right">
        <SearchField
          shortcut="Search"
          syncValue={syncValue}
          onSearch={q => void navigate(`/search/?q=${encodeURIComponent(q)}`)}
        />
      </div>
    </header>
  );
}
