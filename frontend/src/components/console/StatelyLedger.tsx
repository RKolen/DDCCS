/**
 * DDCCS Console — StatelyLedger
 *
 * Application shell rendered at `/`. Left brass-tab sidebar, master/detail
 * action column, right activity drawer. Never a top-nav site.
 *
 * Canonical reference: /menu/variant-ledger.jsx
 */

import * as React from 'react';
import { MENU_DATA, type MenuSection, type MenuItem } from './menuData';
import { Icon, AiTag, SlowTag, ActivityDrawer } from './atoms';
import { ScreenRouter, type ScreenContext } from './ScreenRouter';
import { ActivityFullScreen } from './ActivityFullScreen';
import {
  ConsoleContext, type ConsoleData,
  playerCharacters, npcCharacters,
} from './ConsoleContext';
import { useTopbar } from '../layout/TopbarContext';

/* ────────────────────────────────────────────────────────────
   Per-section default landing item
   ──────────────────────────────────────────────────────────── */

const SECTION_DEFAULTS: Record<MenuSection['id'], string> = {
  characters: 'list',
  stories: 'work-series',
  read: 'r-story',
  npcs: 'n-list',
  config: 'c-view',
  model: 'm-switch',
  tools: 't-recent',
};

interface StatelyLedgerProps {
  fullscreen?: boolean;
  initialSection?: MenuSection['id'];
  initialItem?: string;
  liveData?: ConsoleData;
}

export function StatelyLedger({
  fullscreen = false,
  initialSection = 'read',
  initialItem,
  liveData,
}: StatelyLedgerProps): React.ReactElement {
  const [activeSection, setActiveSection] = React.useState<MenuSection['id']>(initialSection);
  const [activeItem, setActiveItem] = React.useState<string>(
    initialItem
    ?? SECTION_DEFAULTS[initialSection]
    ?? MENU_DATA.sections.find(s => s.id === initialSection)?.items[0]?.id
    ?? ''
  );
  const [drawerOpen, setDrawerOpen]     = React.useState(true);
  const [activityFull, setActivityFull] = React.useState(false);
  /* Live activity items — populated via SSE/websocket once wired up */
  const [activityItems] = React.useState<import('./menuData').ActivityItem[]>([]);
  const [ctx, setCtxRaw] = React.useState<ScreenContext>({ storyIdx: 0, charIdx: 0 });

  const campaigns = liveData?.campaigns ?? [];

  /* Register campaigns with the global topbar. GlobalLayout owns
     activeCampaignName — we read it back via useTopbar(). */
  const { register, activeCampaignName } = useTopbar();
  React.useEffect(() => {
    if (campaigns.length > 0) {
      register(campaigns, campaigns[0].name, true);
    }
  }, [register, campaigns]);

  const setCtx = React.useCallback((next: ScreenContext) => {
    if (next?._jumpTo) {
      const j = next._jumpTo;
      if (j.sectionId) setActiveSection(j.sectionId as MenuSection['id']);
      if (j.itemId) setActiveItem(j.itemId);
      const { _jumpTo, ...clean } = next;
      setCtxRaw({ ...clean, ...j });
    } else {
      setCtxRaw(next);
    }
  }, []);

  /* Patch sidebar counts from real Drupal data */
  const pcs = liveData ? playerCharacters(liveData) : null;
  const npcs = liveData ? npcCharacters(liveData) : null;
  const stories = liveData?.stories ?? null;

  const sections = MENU_DATA.sections.map(s => {
    if (s.id === 'characters' && pcs) return { ...s, count: pcs.length };
    if (s.id === 'npcs' && npcs) return { ...s, count: npcs.length };
    if ((s.id === 'stories' || s.id === 'read') && stories) return { ...s, count: stories.length };
    return s;
  });

  const section = sections.find(s => s.id === activeSection);
  const item = section?.items.find(i => i.id === activeItem);

  /* Enrich ctx with active campaign so screens can filter by it */
  const enrichedCtx: ScreenContext = { ...ctx, activeCampaignName };

  const consoleData: ConsoleData = liveData ?? { campaigns: [], characters: [], stories: [] };

  return (
    <ConsoleContext.Provider value={consoleData}>
      <div className={`ledger-shell${fullscreen ? ' ledger-fullscreen' : ''}`}>

        <div className="ledger-body">

          {/* Left brass-tab sidebar */}
          <nav className="ledger-sidebar">
            {sections.map(s => (
              <button
                key={s.id}
                className={`ledger-tab${s.id === activeSection ? ' active' : ''}`}
                onClick={() => {
                  setActiveSection(s.id);
                  setActiveItem(SECTION_DEFAULTS[s.id] ?? s.items[0].id);
                }}
              >
                <span className="ledger-tab-glyph">
                  <Icon name={s.icon} size={18} />
                </span>
                <span className="ledger-tab-text">
                  <span className="ledger-tab-label">{s.label}</span>
                  <span className="ledger-tab-blurb">{s.blurb}</span>
                </span>
                {s.count != null && <span className="ledger-tab-count">{s.count}</span>}
              </button>
            ))}

            <div className="ledger-sidebar-foot">
              <div className="utility-block">
                <span className="utility-eyebrow">Utility commands</span>
                {MENU_DATA.utilityCommands.map(c => (
                  <button key={c.cmd} className="utility-cmd">
                    <code>{c.cmd}</code>
                    <span>{c.label}</span>
                    {c.slow && <SlowTag />}
                  </button>
                ))}
              </div>
            </div>
          </nav>

          {/* Action column */}
          <section className="ledger-action">
            <div className="action-header">
              <div className="action-header-top">
                <div className="action-header-text">
                  <span className="reader-eyebrow">{section?.label}</span>
                  <h2>{item ? item.label : section?.label}</h2>
                </div>
                <span className="action-header-meta">
                  {section ? `${section.items.length} actions` : ''}
                  {section && section.items.filter(i => i.ai).length > 0 && (
                    <>
                      <span className="dot-sep">·</span>
                      {section.items.filter(i => i.ai).length} AI-powered
                    </>
                  )}
                </span>
              </div>
              <nav className="action-tabs">
                {(section as MenuSection | undefined)?.items.map((it: MenuItem, i: number) => (
                  <button
                    key={it.id}
                    className={`action-tab${it.id === activeItem ? ' active' : ''}${it.deprecated ? ' deprecated' : ''}`}
                    onClick={() => setActiveItem(it.id)}
                  >
                    <span className="tab-num">{String(i + 1).padStart(2, '0')}</span>
                    <span>{it.label}</span>
                    <span className="tab-tags">
                      {it.ai && <AiTag />}
                      {it.slow && <SlowTag />}
                      {it.hasSubmenu && <Icon name="chevron" size={10} />}
                    </span>
                  </button>
                ))}
              </nav>
            </div>

            <div className="action-body">
              {section && item && (
                <ScreenRouter section={section} item={item} ctx={enrichedCtx} setCtx={setCtx} />
              )}
            </div>
          </section>

          {/* Right activity drawer */}
          {!activityFull && (
            <ActivityDrawer
              items={activityItems}
              open={drawerOpen}
              onToggle={() => setDrawerOpen(!drawerOpen)}
            />
          )}
        </div>

        {drawerOpen && !activityFull && (
          <button
            className="activity-expand-btn"
            onClick={() => setActivityFull(true)}
            title="Open activity log full-screen"
          >
            <Icon name="drawer" size={13} /> Expand
          </button>
        )}

        {activityFull && (
          <div className="activity-overlay">
            <ActivityFullScreen items={activityItems} onClose={() => setActivityFull(false)} />
          </div>
        )}
      </div>
    </ConsoleContext.Provider>
  );
}
