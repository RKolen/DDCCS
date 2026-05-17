/**
 * DDCCS Console — atoms
 * --------------------------------------------------------------
 * Typed port of `menu/menu-atoms.jsx`.
 *
 * What lives here:
 *   - <Icon>           Inline-SVG icon set used by the console chrome.
 *                      All icons are 16x16 stroke glyphs that use
 *                      `currentColor`, so size them with width/height
 *                      and color them with CSS color.
 *   - <AiTag>          Small "AI" sparkle pill inline indicator.
 *   - <SlowTag>        "slow" label for actions that take 10s+.
 *   - <Rivet>          Decorative brass nail/rivet.
 *   - <TabGlyph>       Brass tab insignia (single letter, ledger-style).
 *   - <ActivityRow>    A single activity-log entry.
 *   - <ActivityDrawer> Collapsible right rail.
 *   - <CampaignChip>   Persistent active-campaign chip in the top bar.
 *   - <SearchField>    Top-bar command-K search input.
 *
 * Game icons (those used inside character pages — class glyphs,
 * ability icons, spell schools, item types) live separately under
 * `components/atoms/GameIcon.tsx` and are sourced from `static/icons/game/`.
 * This file only owns the console chrome glyph set.
 *
 * Canonical reference: /menu/menu-atoms.jsx
 */

import * as React from 'react';
import type {
  IconName, ActivityItem, Campaign,
} from './menuData';

/* ────────────────────────────────────────────────────────────
   Icon
   ──────────────────────────────────────────────────────────── */

interface IconProps extends React.SVGAttributes<SVGSVGElement> {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 16, style, ...rest }: IconProps): React.ReactElement | null {
  const stroke: React.SVGAttributes<SVGGElement> = {
    stroke: 'currentColor',
    strokeWidth: 1.5,
    fill: 'none',
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
  };

  const paths: Record<IconName, React.ReactElement> = {
    char:        <g {...stroke}><circle cx="8" cy="6" r="3" /><path d="M2.5 14c.8-3 2.9-4.5 5.5-4.5s4.7 1.5 5.5 4.5" /></g>,
    story:       <g {...stroke}><path d="M3 3h7l3 3v10H3z" /><path d="M10 3v3h3" /><path d="M5.5 8h5M5.5 10.5h5M5.5 13h3" /></g>,
    read:        <g {...stroke}><path d="M2 4c2 0 4 .5 6 2v8c-2-1.5-4-2-6-2zM14 4c-2 0-4 .5-6 2v8c2-1.5 4-2 6-2z" /></g>,
    npc:         <g {...stroke}><path d="M8 2L3 5v3c0 3 2 5.5 5 6.5 3-1 5-3.5 5-6.5V5z" /></g>,
    gear:        <g {...stroke}><circle cx="8" cy="8" r="2" /><path d="M8 1.5v2M8 12.5v2M14.5 8h-2M3.5 8h-2M12.6 3.4l-1.4 1.4M4.8 11.2l-1.4 1.4M12.6 12.6l-1.4-1.4M4.8 4.8L3.4 3.4" /></g>,
    model:       <g {...stroke}><circle cx="8" cy="8" r="5" /><path d="M8 3v10M3 8h10M5 5l6 6M11 5l-6 6" /></g>,
    tools:       <g {...stroke}><path d="M3 13l5-5" /><circle cx="11.5" cy="4.5" r="2" /><path d="M10 6L8 8M3 13l-1 1" /></g>,
    sparkle:     <g {...stroke}><path d="M8 2v4M8 10v4M2 8h4M10 8h4M4.5 4.5l2.5 2.5M9 9l2.5 2.5M4.5 11.5l2.5-2.5M9 7l2.5-2.5" /></g>,
    chevron:     <g {...stroke}><path d="M6 4l4 4-4 4" /></g>,
    chevronDown: <g {...stroke}><path d="M4 6l4 4 4-4" /></g>,
    chevronLeft: <g {...stroke}><path d="M10 4l-4 4 4 4" /></g>,
    search:      <g {...stroke}><circle cx="7" cy="7" r="4.5" /><path d="M10.5 10.5L14 14" /></g>,
    plus:        <g {...stroke}><path d="M8 3v10M3 8h10" /></g>,
    close:       <g {...stroke}><path d="M4 4l8 8M12 4l-8 8" /></g>,
    play:        <g {...stroke} fill="currentColor"><path d="M4 3l9 5-9 5z" /></g>,
    pause:       <g {...stroke} fill="currentColor"><rect x="4" y="3" width="3" height="10" /><rect x="9" y="3" width="3" height="10" /></g>,
    speaker:     <g {...stroke}><path d="M3 6h2l3-3v10l-3-3H3z" /><path d="M11 6c.8.8 1.2 1.8 1.2 3s-.4 2.2-1.2 3" /></g>,
    image:       <g {...stroke}><rect x="2" y="3" width="12" height="10" /><circle cx="6" cy="7" r="1.2" /><path d="M2 11l3.5-3 4 3.5L12 9l2 2" /></g>,
    book:        <g {...stroke}><path d="M3 3h6c1 0 2 .8 2 2v9H5c-1 0-2-.8-2-2z" /><path d="M3 12c0-1 .8-2 2-2h6" /></g>,
    flag:        <g {...stroke}><path d="M4 2v12M4 3h7l-2 2.5L11 8H4" /></g>,
    scroll:      <g {...stroke}><path d="M4 3h6c1 0 2 1 2 2v8c0 1-1 1-1 1H5" /><path d="M5 14c-1 0-1.5-.5-1.5-1.5V4c0-.5.5-1 1-1" /><path d="M6 6h4M6 8h4M6 10h3" /></g>,
    timeline:    <g {...stroke}><circle cx="4" cy="4" r="1.5" /><circle cx="4" cy="12" r="1.5" /><circle cx="12" cy="8" r="1.5" /><path d="M4 5.5v5M5.5 4l5 4M5.5 12l5-4" /></g>,
    spell:       <g {...stroke}><path d="M8 2l1.8 4 4.2.4-3.2 2.8 1 4.2L8 11.5 4.2 13.4l1-4.2L2 6.4l4.2-.4z" /></g>,
    grid:        <g {...stroke}><rect x="2" y="2" width="5" height="5" /><rect x="9" y="2" width="5" height="5" /><rect x="2" y="9" width="5" height="5" /><rect x="9" y="9" width="5" height="5" /></g>,
    list:        <g {...stroke}><path d="M2 4h12M2 8h12M2 12h12" /></g>,
    drawer:      <g {...stroke}><rect x="2" y="2" width="12" height="12" /><path d="M2 6h12M5 9h6" /></g>,
  };

  return (
    <svg viewBox="0 0 16 16" width={size} height={size} style={{ flexShrink: 0, ...style }} {...rest}>
      {paths[name] ?? null}
    </svg>
  );
}

/* ────────────────────────────────────────────────────────────
   Small tags
   ──────────────────────────────────────────────────────────── */

export function AiTag({ size = 'sm', label = 'AI' }: { size?: 'sm' | 'md'; label?: string }): React.ReactElement {
  return (
    <span className={`ai-tag ai-tag-${size}`}>
      <Icon name="sparkle" size={size === 'sm' ? 9 : 11} />
      {label && <span>{label}</span>}
    </span>
  );
}

export function SlowTag(): React.ReactElement {
  return <span className="slow-tag" title="May take 10+ seconds">slow</span>;
}

export function Rivet({ size = 8 }: { size?: number }): React.ReactElement {
  return <span className="rivet" style={{ width: size, height: size }} />;
}

export function TabGlyph({ glyph, active }: { glyph: string; active?: boolean }): React.ReactElement {
  return <span className={`tab-glyph${active ? ' active' : ''}`}>{glyph}</span>;
}

/* ────────────────────────────────────────────────────────────
   Activity drawer (right rail)
   ──────────────────────────────────────────────────────────── */

export function ActivityRow({ item }: { item: ActivityItem }): React.ReactElement {
  return (
    <div className={`activity-row activity-${item.status}`}>
      <div className="activity-head">
        <span className={`dot dot-${item.status}`} />
        <span className="activity-label">
          {item.kind === 'ai' && <Icon name="sparkle" size={10} style={{ marginRight: 4 }} />}
          {item.label}
        </span>
        {item.elapsed && <span className="activity-elapsed">{item.elapsed}</span>}
      </div>
      <div className="activity-detail">{item.detail}</div>
      {item.progress != null && (
        <div className="activity-bar">
          <div className="activity-bar-fill" style={{ width: `${item.progress * 100}%` }} />
        </div>
      )}
    </div>
  );
}

interface ActivityDrawerProps {
  items: ActivityItem[];
  open: boolean;
  onToggle: () => void;
  compact?: boolean;
}

export function ActivityDrawer({ items, open, onToggle, compact }: ActivityDrawerProps): React.ReactElement {
  const runningCount = items.filter(i => i.status === 'running').length;
  return (
    <aside className={`activity-drawer${open ? ' open' : ''}${compact ? ' compact' : ''}`}>
      <button className="activity-toggle" onClick={onToggle} title={open ? 'Hide activity' : 'Show activity'}>
        <Icon name={open ? 'chevron' : 'chevronLeft'} size={14} />
        {!open && <span className="activity-toggle-tag">{runningCount || ''}</span>}
      </button>
      {open && (
        <div className="activity-body">
          <div className="activity-head-row">
            <h3>Activity</h3>
            <span className="activity-count">{items.length}</span>
          </div>
          <div className="activity-list">
            {items.map((item, i) => <ActivityRow key={i} item={item} />)}
          </div>
          <div className="activity-foot">
            <button className="activity-clear">Clear completed</button>
          </div>
        </div>
      )}
    </aside>
  );
}

/* ────────────────────────────────────────────────────────────
   Campaign chip (top bar)
   ──────────────────────────────────────────────────────────── */

interface CampaignChipProps {
  campaigns: Campaign[];
  onSwitch?: (campaignId: string) => void;
  variant?: 'default' | 'ledger';
}

export function CampaignChip({ campaigns, onSwitch, variant = 'default' }: CampaignChipProps): React.ReactElement {
  const [open, setOpen] = React.useState(false);
  const active = campaigns.find(c => c.active) ?? campaigns[0];
  return (
    <div className={`campaign-chip campaign-chip-${variant}`}>
      <button className="campaign-chip-btn" onClick={() => setOpen(!open)}>
        <span className="chip-pin" />
        <span className="chip-meta">
          <span className="chip-eyebrow">Active campaign</span>
          <span className="chip-name">{active.name}</span>
        </span>
        <span className="chip-stats">
          <span>{active.stories} stories</span>
          <span className="chip-sep">·</span>
          <span>{active.party} party</span>
        </span>
        <Icon name="chevronDown" size={12} />
      </button>
      {open && (
        <div className="campaign-chip-pop">
          <div className="chip-pop-header">Switch campaign</div>
          {campaigns.map(c => (
            <button
              key={c.id}
              className={`chip-pop-item${c.active ? ' active' : ''}`}
              onClick={() => { onSwitch?.(c.id); setOpen(false); }}
            >
              <span className="chip-pop-name">{c.name}</span>
              <span className="chip-pop-stats">{c.stories} stories · {c.party} party</span>
            </button>
          ))}
          <div className="chip-pop-foot">
            <button className="chip-pop-new"><Icon name="plus" size={11} /> New campaign</button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Search field (top bar)
   ──────────────────────────────────────────────────────────── */

interface SearchFieldProps {
  placeholder?: string;
  shortcut?: string;
}

export function SearchField({
  placeholder = 'Search characters, stories, NPCs...',
  shortcut = 'Cmd+K',
}: SearchFieldProps): React.ReactElement {
  return (
    <div className="search-field">
      <Icon name="search" size={14} />
      <input type="text" placeholder={placeholder} />
      <kbd>{shortcut}</kbd>
    </div>
  );
}
