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
import {
  useJobActivity, jobResult, requeueJob, clearFinishedJobs, JOB_TYPES,
} from '../../utils/aiJobs';
import type { AiJob } from '../../utils/aiJobs';
import type { PortraitJobResult } from '../../utils/portraitProfile';
import type { ActivityItem, ActivityTarget } from './menuData';
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
  stories:    'work-series',
  read:       'r-story',
  npcs:       'n-list',
  items:      'i-list',
  monsters:   'm-list',
  config:     'c-view',
  model:      'm-switch',
  tools:      't-recent',
};

interface StatelyLedgerProps {
  fullscreen?: boolean;
  initialSection?: MenuSection['id'];
  initialItem?: string;
  liveData?: ConsoleData;
}

/**
 * Render one queued AI job as an activity-drawer row.
 *
 * A job waiting for the processor reads as `queued`, not `running`: it is in
 * flight from the operator's point of view, but nothing is working on it yet and
 * showing it as busy has misled us before.
 *
 * Every portrait job gets a target - the screen its output lands on - so the row
 * is a way back to the work from the moment it is queued, not only once it has
 * finished. `subjectId` is what makes that possible before there is a result. A
 * finished job whose result is still `pending` additionally gets `needsReview`,
 * which is what turns the link into the accept/discard decision; without it a
 * render would sit in the media library with nothing pointing at it.
 *
 * @param job    The job as the queue reports it.
 * @param locate Resolves a character id to the screen showing that character.
 */
function jobToActivityItem(
  job: AiJob,
  locate: (characterId: string) => ActivityTarget | undefined,
): ActivityItem {
  const stalled = Boolean(job.stalled);
  const status: ActivityItem['status'] =
    job.state === 'success' ? 'done'
      : job.state === 'failure' ? 'failed'
        : job.state === 'queued' ? 'queued'
          // A claimed job whose lease lapsed is not running, whatever the state
          // column says; drawing it as busy is what left us watching a spinner.
          : stalled ? 'failed' : 'running';
  const elapsed = job.processed && job.created && job.processed > job.created
    ? `${job.processed - job.created}s`
    : undefined;

  const isPortrait = job.type === JOB_TYPES.portrait;
  const portrait = isPortrait ? jobResult<PortraitJobResult>(job) : null;
  const needsReview = portrait?.review === 'pending';
  const subject = portrait?.characterId ?? job.subjectId;
  const target = isPortrait && subject ? locate(subject) : undefined;

  const detail = needsReview
    ? 'Rendered - not attached until you accept it'
    : stalled
      ? 'Stalled - the host stopped responding; requeue to run it again'
      : job.state === 'queued'
        ? 'Waiting for the host queue'
        : job.message ?? (job.state === 'processing' ? 'Running on the host' : '');

  return {
    kind: 'ai',
    status,
    label: job.label,
    detail,
    elapsed,
    jobId: job.id,
    target,
    needsReview,
    stalled,
  };
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
  /* Live activity: what the host queue is running, waiting on, and just
     finished. Polled, so a job that completed while you were on another screen
     still reports itself here. */
  const { running, recent, refresh: refreshActivity } = useJobActivity();
  const [clearing, setClearing] = React.useState(false);
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

  /* Where a job's character can be reviewed. A party member goes to the Portrait
     Studio, whose roster is this same unfiltered player list, so the index lines
     up; an NPC goes to its detail screen. A character that is in neither list
     yields no target and the row stays a plain status line. */
  const locateCharacter = React.useCallback((characterId: string): ActivityTarget | undefined => {
    const pcIdx = pcs?.findIndex(c => c.id === characterId) ?? -1;
    if (pcIdx >= 0) {
      return { sectionId: 'characters', itemId: 'ascii', charIdx: pcIdx };
    }
    const npcIdx = npcs?.findIndex(c => c.id === characterId) ?? -1;
    if (npcIdx >= 0) {
      return { sectionId: 'npcs', itemId: 'n-view', charIdx: npcIdx, npcMode: true };
    }
    return undefined;
  }, [pcs, npcs]);

  const activityItems = React.useMemo(
    () => [...running, ...recent].map(job => jobToActivityItem(job, locateCharacter)),
    [running, recent, locateCharacter],
  );

  /* Open the screen a row points at, carrying the job id so that screen picks
     the result back up and can accept or discard it. */
  const openActivity = React.useCallback((item: ActivityItem): void => {
    if (!item.target) return;
    setActivityFull(false);
    setCtxRaw(current => ({
      ...current,
      charIdx: item.target?.charIdx ?? 0,
      npcMode: item.target?.npcMode ?? false,
      reviewJobId: item.jobId,
    }));
    setActiveSection(item.target.sectionId);
    setActiveItem(item.target.itemId);
  }, []);

  /* Put a stalled job back on the queue, then re-read so the row updates now
     rather than on the next tick. */
  const requeueActivity = React.useCallback((item: ActivityItem): void => {
    if (!item.jobId) return;
    void requeueJob(item.jobId)
      .catch(() => {
        /* The refresh below re-reads the truth either way. */
      })
      .finally(() => refreshActivity());
  }, [refreshActivity]);

  /* Clear the finished jobs. Drupal decides what is safe to delete; anything it
     keeps back (a result still awaiting a decision) reappears on the refresh. */
  const clearActivity = React.useCallback((): void => {
    setClearing(true);
    void clearFinishedJobs()
      .catch(() => {
        /* Nothing was deleted; the refresh shows the list unchanged. */
      })
      .finally(() => {
        setClearing(false);
        refreshActivity();
      });
  }, [refreshActivity]);

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

  const consoleData: ConsoleData = liveData ?? { campaigns: [], characters: [], stories: [], monsters: [], items: [] };

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
              onOpen={openActivity}
              onRequeue={requeueActivity}
              onClear={clearActivity}
              clearing={clearing}
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
            <ActivityFullScreen
              items={activityItems}
              onClose={() => setActivityFull(false)}
              onOpen={openActivity}
              onRequeue={requeueActivity}
            />
          </div>
        )}
      </div>
    </ConsoleContext.Provider>
  );
}
