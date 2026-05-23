/**
 * StoryDetailsScreen — `stories/work-series` > s-view.
 *
 * Two-pane DM-mode reader: annotated prose on the left,
 * structured data (combat log, DC checks, NPC mentions, loot) on the right.
 * Read-only — use Amend or Notes to edit.
 *
 * Port of _canonical_source/screens-series-view.jsx.
 * Production wiring: query node--story by id, with paragraphs, combat_log,
 * dc_checks, npc_mentions, and loot fields from Drupal.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData, storiesForCampaign } from '../ConsoleContext';

/* ─────────────────────────────────────────────────────────────
   Types
───────────────────────────────────────────────────────────── */

type BodyKind = 'p' | 'h' | 'note';

interface BodyBlock {
  kind: BodyKind;
  text: string;
  label?: string;
}

interface CombatEntry {
  round: string;
  who: string;
  action: string;
  d20: number | string;
  total: number | string;
  dmg: string;
  hit: boolean;
  crit: boolean;
}

interface DcEntry {
  skill: string;
  dc: number;
  who: string;
  result: 'pass' | 'fail' | 'mixed';
  outcome: string;
}

interface NpcMention {
  name: string;
  role: string;
  count: number;
}

interface LootEntry {
  rarity: string;
  name: string;
  meta: string;
}

interface StoryIndex {
  id: string;
  title: string;
  tag?: string;
}

interface StoryDetail {
  meta: {
    id: string;
    title: string;
    series: string;
    session: number;
    date_in_world: string;
    played_at: string;
    wordcount: number;
    party: string[];
  };
  summary: string;
  body: BodyBlock[];
  combat: CombatEntry[];
  dcs: DcEntry[];
  npcs: NpcMention[];
  loot: LootEntry[];
}

/* ─────────────────────────────────────────────────────────────
   Static demo data (read from game_data/campaigns/Example_Campaign)
   In production: query Drupal story node selected from ctx.storyIdx.
───────────────────────────────────────────────────────────── */

const DEMO_STORY: StoryDetail = {
  meta: {
    id: '002_continue',
    title: 'Mysteries of Trollshaws',
    series: 'The Fellowship — Eastern March',
    session: 2,
    date_in_world: 'Hammer 14, 1492 DR',
    played_at: '6 weeks ago',
    wordcount: 2_120,
    party: ['Aragorn', 'Frodo', 'Gandalf'],
  },
  summary: 'Gandalf detects magic ripples in Trollshaws Forest. A goblin ambush on the road. Frodo gets the killing blow with Sting. A map fragment points east.',
  body: [
    { kind: 'p', text: 'The road into **Trollshaws** was quiet in a way that was not comfortable.' },
    { kind: 'p', text: '**Gandalf** drew Detect Magic across them without warning — a ritual gesture, almost unconscious. The forest answered. *Ripples*, deep and patient. Not local.' },
    { kind: 'note', label: 'DM note', text: 'Gandalf rolled a natural 20 on the concentration check. Mark the bearing for a later session — something in the east is homing.' },
    { kind: 'h', text: 'Goblin ambush on the road' },
    { kind: 'p', text: '**Aragorn** was already reaching for his sword when the archers rose from the high ground. Six of them, with a captain on the road and a flanker in the brush.' },
    { kind: 'p', text: '**Frodo** did not freeze. He stepped left, found the gap between two stones, and drove *Sting* into the flanker before the goblin could cry out. A critical hit. Instakill.' },
    { kind: 'note', label: 'Mechanics', text: 'Natural 20 on Sting attack. Sneak attack triggered (flanking with Aragorn). Total: 1d4+3+2d6 = 11 damage vs 7 HP. Instakill.' },
  ],
  combat: [
    { round: 'R1', who: 'Goblin archers', action: 'Ambush volley', d20: 14, total: 16, dmg: '1d6+1', hit: true, crit: false },
    { round: 'R1', who: 'Aragorn', action: 'Drew bow, attacked', d20: 18, total: 21, dmg: '1d8+3', hit: true, crit: false },
    { round: 'R1', who: 'Gandalf', action: 'Fireball (3rd-level)', d20: 'DC 15', total: 'Dex', dmg: '8d6 fire', hit: true, crit: false },
    { round: 'R2', who: 'Frodo', action: 'Sneak attack with Sting', d20: 20, total: 23, dmg: '1d4+3+2d6', hit: true, crit: true },
    { round: 'R2', who: 'Aragorn', action: 'Closed to melee', d20: 16, total: 19, dmg: '1d8+3', hit: true, crit: false },
  ],
  dcs: [
    { skill: 'WIS · Perception', dc: 18, who: 'Aragorn', result: 'fail', outcome: 'Missed the ambush setup.' },
    { skill: 'DEX · Stealth', dc: 13, who: 'Frodo', result: 'pass', outcome: 'Flanked without detection.' },
    { skill: 'CON · Concentration', dc: 10, who: 'Gandalf', result: 'pass', outcome: 'Maintained Detect Magic mid-combat.' },
  ],
  npcs: [
    { name: 'Goblin scout', count: 6, role: 'Encounter · CR 1/4' },
    { name: 'Goblin captain', count: 1, role: 'Encounter · CR 1' },
  ],
  loot: [
    { rarity: 'common', name: 'Bone whistle', meta: 'unknown function' },
    { rarity: 'common', name: 'Map fragment', meta: 'rune in corner matches Bree letter seal' },
    { rarity: 'common', name: '14 gp', meta: 'from captain' },
  ],
};

const RARITY_COLORS: Record<string, string> = {
  common: 'var(--color-rarity-common)',
  uncommon: 'var(--color-rarity-uncommon)',
  rare: 'var(--color-rarity-rare)',
  'very-rare': 'var(--color-rarity-very-rare)',
  legendary: 'var(--color-rarity-legendary)',
  artifact: 'var(--color-rarity-artifact)',
};

/* ─────────────────────────────────────────────────────────────
   Helpers
───────────────────────────────────────────────────────────── */

function renderInline(s: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const re = /\*\*([^*]+)\*\*|\*([^*]+)\*/g;
  let m: RegExpExecArray | null;
  let last = 0;
  while ((m = re.exec(s)) !== null) {
    if (m.index > last) parts.push(s.slice(last, m.index));
    if (m[1] !== undefined) parts.push(<strong key={parts.length}>{m[1]}</strong>);
    else if (m[2] !== undefined) parts.push(<em key={parts.length}>{m[2]}</em>);
    last = re.lastIndex;
  }
  if (last < s.length) parts.push(s.slice(last));
  return parts;
}

/* ─────────────────────────────────────────────────────────────
   StoryDetailsScreen
───────────────────────────────────────────────────────────── */

export function StoryDetailsScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useConsoleData();
  const campaign = (ctx.activeCampaignName as string | null | undefined) ?? data.campaigns[0]?.name ?? null;
  const stories = campaign ? storiesForCampaign(data, campaign) : data.stories;

  const storyIndex: StoryIndex[] = stories.map((s, i) => ({
    id: String(s.storyNumber ?? i + 1).padStart(3, '0'),
    title: s.title,
    tag: i === stories.length - 1 ? 'latest' : undefined,
  }));

  const demo = DEMO_STORY;

  const goBack = (): void => {
    setCtx({ ...ctx, workSeriesAction: null });
  };

  return (
    <div>
      <div className="action-back-row">
        <button type="button" className="action-back" onClick={goBack}>
          <Icon name="chevronLeft" size={11} /> Back to series workspace
        </button>
        <span className="action-entry-pip">
          <span className="dot" />
          DM view &middot; annotations on
        </span>
      </div>

      <header className="screen-head" style={{ marginBottom: 16, paddingBottom: 12 }}>
        <div>
          <span className="reader-eyebrow">View story details</span>
          <h2>
            Story {String(demo.meta.session).padStart(3, '0')} &middot; {demo.meta.title}
          </h2>
          <p className="screen-blurb">
            DM-mode read of <em>{demo.meta.title}</em>. Prose left, structured data right.
            This view is read-only — use Amend or Notes to edit.
          </p>
        </div>
        <div className="screen-head-actions">
          <button type="button" className="ghost-btn">
            <Icon name="search" size={11} /> Find in story
          </button>
          <button type="button" className="ghost-btn">
            <Icon name="sparkle" size={11} /> Analyze
          </button>
          <button type="button" className="primary-btn">Amend</button>
        </div>
      </header>

      <div className="screen-storyview">
        <article className="storyview-prose">
          <div className="storyview-meta-row">
            <span>series &middot; <b>{demo.meta.series}</b></span>
            <span className="dot-sep">&middot;</span>
            <span>session &middot; <b>{String(demo.meta.session).padStart(3, '0')}</b></span>
            <span className="dot-sep">&middot;</span>
            <span>in-world &middot; <b>{demo.meta.date_in_world}</b></span>
            <span className="dot-sep">&middot;</span>
            <span>played &middot; <b>{demo.meta.played_at}</b></span>
            <span className="dot-sep">&middot;</span>
            <span><b>{demo.meta.wordcount.toLocaleString()}</b> words</span>
          </div>

          <span className="reader-eyebrow">Title</span>
          <h1>{demo.meta.title}</h1>
          <p className="summary">{demo.summary}</p>

          <div className="body">
            {demo.body.map((blk, i) => {
              if (blk.kind === 'h') return <h3 key={i}>{blk.text}</h3>;
              if (blk.kind === 'note') {
                return (
                  <span key={i} className="annotation">
                    <span className="ann-label">{blk.label}</span>
                    {blk.text}
                  </span>
                );
              }
              return <p key={i}>{renderInline(blk.text)}</p>;
            })}
          </div>
        </article>

        <aside className="storyview-rail">
          <section className="storyview-panel">
            <h4>
              Party present <span className="count">{demo.meta.party.length}</span>
            </h4>
            <ul>
              {demo.meta.party.map(name => (
                <li key={name} className="npc-mention">
                  <span className="npc-pip">{name[0]}</span>
                  <span className="npc-info">
                    <span className="npc-name">{name}</span>
                    <span className="npc-role">present this session</span>
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="storyview-panel">
            <h4>Combat log <span className="count">{demo.combat.length} entries</span></h4>
            <ul>
              {demo.combat.map((c, i) => (
                <li key={i} className="combat-entry">
                  <span className="round">{c.round}</span>
                  <span>
                    <span className="who">{c.who}</span><br />
                    {c.action}
                  </span>
                  <span className={`roll ${c.crit ? 'crit' : c.hit ? 'hit' : 'miss'}`}>
                    {c.d20 === '—'
                      ? '—'
                      : <>{c.d20}<br /><span style={{ fontSize: 9 }}>total {c.total}</span></>}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="storyview-panel">
            <h4>DC checks <span className="count">{demo.dcs.length}</span></h4>
            <ul>
              {demo.dcs.map((d, i) => (
                <li key={i} className="dc-entry">
                  <div>
                    <span className="skill">{d.skill}</span><br />
                    <span style={{ fontSize: 11, fontStyle: 'italic', color: 'var(--ink-dim)' }}>
                      {d.outcome}
                    </span>
                  </div>
                  <span className={`target ${d.result === 'pass' ? 'ok' : d.result === 'fail' ? 'fail' : ''}`}>
                    DC {d.dc}
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--brass-dim)' }}>
                    {d.who}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="storyview-panel">
            <h4>NPC mentions <span className="count">{demo.npcs.length}</span></h4>
            <ul>
              {demo.npcs.map(n => (
                <li key={n.name} className="npc-mention">
                  <span className="npc-pip">{n.name[0]}</span>
                  <span className="npc-info">
                    <span className="npc-name">{n.name}</span>
                    <span className="npc-role">{n.role}</span>
                  </span>
                  <span className="npc-count">&times;{n.count}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="storyview-panel">
            <h4>Loot &amp; items <span className="count">{demo.loot.length}</span></h4>
            <ul>
              {demo.loot.map((l, i) => (
                <li key={i} className="loot-entry">
                  <span
                    className="loot-rarity"
                    style={{ background: RARITY_COLORS[l.rarity] ?? 'var(--ink-dim)' }}
                  />
                  <span className="loot-name">{l.name}</span>
                  <span className="loot-meta">{l.meta}</span>
                </li>
              ))}
            </ul>
          </section>

          {storyIndex.length > 0 && (
            <section className="storyview-panel">
              <h4>
                Other stories in series <span className="count">{storyIndex.length}</span>
              </h4>
              <ul>
                {storyIndex.map(s => (
                  <li
                    key={s.id}
                    style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '6px 0', borderBottom: '1px dashed var(--rule)',
                    }}
                  >
                    <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink)' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--brass-dim)', marginRight: 8 }}>
                        {s.id}
                      </span>
                      {s.title}
                    </span>
                    {s.tag !== undefined && <span className="latest-tag">{s.tag}</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}
