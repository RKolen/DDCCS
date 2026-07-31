/**
 * NpcValidatorScreen — `npcs / n-validate`
 *
 * Profile completeness audit for NPCs and PCs. Drupal enforces required
 * fields and types at save time; this screen surfaces the optional richness
 * fields that the AI generation layer benefits from (bonds, ideals, flaws,
 * portrait, relationships) so a DM can spot thin profiles before a session.
 *
 * Design reference: /project/NPC Validator.html
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData, playerCharacters, npcCharacters } from '../ConsoleContext';
import type { DrupalCharacter } from '../ConsoleContext';

/* ────────────────────────────────────────────────────────────
   Colours
   ──────────────────────────────────────────────────────────── */

const COLOR_WARN = 'var(--color-warning)';
const COLOR_PASS = 'var(--color-success)';
const COLOR_PARTIAL = 'var(--color-partial)';

type Completeness = 'full' | 'partial' | 'thin';
type EntityFilter = 'npc' | 'pc';
type StatusFilter = 'all' | 'full' | 'partial' | 'thin';

/* ────────────────────────────────────────────────────────────
   Completeness check types
   ──────────────────────────────────────────────────────────── */

interface AuditResult {
  status: Completeness;
  score: number;
  maxScore: number;
}

interface AuditRecord {
  char: DrupalCharacter;
  entity: 'npc' | 'pc';
  audit: AuditResult;
}

/* ────────────────────────────────────────────────────────────
   Completeness engine
   ──────────────────────────────────────────────────────────── */

function isEmpty(v: unknown): boolean {
  if (v == null) return true;
  if (Array.isArray(v)) return v.length === 0;
  if (typeof v === 'string') return v.trim() === '';
  return false;
}

/**
 * What counts toward a complete profile, and how much each part is worth.
 *
 * `label` is retained as the reason each weight exists - the score is otherwise
 * an unexplained number - even though the per-field breakdown is no longer
 * rendered.
 */
const CHECKS: Array<{
  label: string;
  weight: number;
  get: (c: DrupalCharacter) => boolean;
}> = [
    {
      label: 'Portrait image',
      weight: 2,
      get: c => !isEmpty(c.imageUrl),
    },
    {
      label: 'Pronouns',
      weight: 1,
      get: c => !isEmpty(c.pronouns),
    },
    {
      label: 'Background',
      weight: 1,
      get: c => !isEmpty(c.background),
    },
    {
      label: 'Personality traits',
      weight: 2,
      get: c => !isEmpty(c.personalityTraits),
    },
    {
      label: 'Ideals',
      weight: 2,
      get: c => !isEmpty(c.ideals),
    },
    {
      label: 'Bonds',
      weight: 2,
      get: c => !isEmpty(c.bonds),
    },
    {
      label: 'Flaws',
      weight: 2,
      get: c => !isEmpty(c.flaws),
    },
    {
      label: 'Ancestry',
      weight: 1,
      get: c => !isEmpty(c.species) || !isEmpty(c.lineage),
    },
  ];

const MAX_SCORE = CHECKS.reduce((s, c) => s + c.weight, 0);

function auditCharacter(char: DrupalCharacter): AuditResult {
  let score = 0;
  for (const def of CHECKS) {
    if (def.get(char)) score += def.weight;
  }

  const pct: number = score / MAX_SCORE;
  const status: Completeness = pct >= 1 ? 'full' : pct >= 0.6 ? 'partial' : 'thin';
  return { status, score, maxScore: MAX_SCORE };
}

/* ────────────────────────────────────────────────────────────
   Visual helpers
   ──────────────────────────────────────────────────────────── */

const STATUS_META: Record<Completeness, { color: string; label: string }> = {
  full: { color: COLOR_PASS, label: 'Full' },
  partial: { color: COLOR_PARTIAL, label: 'Partial' },
  thin: { color: COLOR_WARN, label: 'Thin' },
};

function ScoreBar({ score, maxScore, color }: { score: number; maxScore: number; color: string }): React.ReactElement {
  const pct = Math.round((score / maxScore) * 100);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{
        flex: 1, height: 4, borderRadius: 2,
        background: 'var(--canvas)',
        border: '1px solid var(--rule)',
        overflow: 'hidden',
      }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2, transition: '300ms ease' }} />
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-dim)', minWidth: 28 }}>
        {pct}%
      </span>
    </div>
  );
}

function SummaryTile({
  label, value, color, icon, active, onClick,
}: {
  label: string; value: number; color: string;
  icon: React.ReactElement; active: boolean; onClick: () => void;
}): React.ReactElement {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        background: 'var(--canvas-raised)',
        border: `1px solid ${active ? color : 'var(--rule)'}`,
        borderRadius: 10, padding: '16px 18px', textAlign: 'left',
        cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 8,
        boxShadow: active
          ? `0 0 0 1px ${color}, 0 0 14px color-mix(in srgb, ${color} 28%, transparent)`
          : 'none',
        transition: '120ms ease', width: '100%',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ color }}>{icon}</span>
        <span style={{
          fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--ink-dim)',
          letterSpacing: '0.14em', textTransform: 'uppercase', fontWeight: 700,
        }}>
          {label}
        </span>
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 30, fontWeight: 700, color, lineHeight: 1 }}>
        {value}
      </span>
    </button>
  );
}

/**
 * One audited character: portrait, name, and how complete the profile is.
 *
 * Deliberately not expandable and not actionable. Editing lives in one place -
 * the character editor - and an audit that also edits is how the two ended up
 * competing in the first place.
 */
function ProfileRow({ rec, compact }: { rec: AuditRecord; compact: boolean }): React.ReactElement {
  const { char, audit } = rec;
  const meta = STATUS_META[audit.status];
  const initials = char.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();

  return (
    <div style={{
      background: 'var(--canvas-raised)',
      border: '1px solid var(--rule)',
      borderRadius: 8, overflow: 'hidden',
      borderLeft: `3px solid ${meta.color}`,
      display: 'grid',
      gridTemplateColumns: '40px 1fr',
      gap: 14, alignItems: 'center',
      padding: compact ? '10px 16px' : '14px 18px',
    }}>
      {/* Portrait */}
      <div style={{
        width: 40, height: 40, borderRadius: 6, flexShrink: 0,
        background: 'var(--canvas)', border: '1px solid var(--rule)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        overflow: 'hidden',
      }}>
        {char.imageUrl
          ? <img src={char.imageUrl} alt={char.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          : <span style={{ fontFamily: 'var(--font-display)', fontSize: 13, color: 'var(--brass)', fontWeight: 700 }}>{initials}</span>
        }
      </div>

      {/* Name + score bar */}
      <div style={{ minWidth: 0 }}>
        <div style={{ marginBottom: 6 }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 15, color: 'var(--brass-bright)', fontWeight: 600 }}>
            {char.title}
          </span>
        </div>
        <ScoreBar score={audit.score} maxScore={audit.maxScore} color={meta.color} />
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Main screen
   ──────────────────────────────────────────────────────────── */

export function NpcValidatorScreen({ ctx }: ScreenProps): React.ReactElement {
  const data = useConsoleData();

  /* Entity mode is locked by the route: npcs/n-validate → npc, characters/completeness → pc */
  const entityFilter: EntityFilter = ctx.pcMode === true ? 'pc' : 'npc';

  const [statusFilter, setStatusFilter] = React.useState<StatusFilter>('all');
  const [query, setQuery] = React.useState('');
  const [density] = React.useState<'comfortable' | 'compact'>('comfortable');

  const audited = React.useMemo<AuditRecord[]>(() => {
    return data.characters.map(char => ({
      char,
      entity: char.characterType === false ? 'npc' : 'pc',
      audit: auditCharacter(char),
    }));
  }, [data.characters]);

  const scoped = React.useMemo(() =>
    audited.filter(r => r.entity === entityFilter),
    [audited, entityFilter]);

  const summary = React.useMemo(() => {
    const s = { total: scoped.length, full: 0, partial: 0, thin: 0 };
    scoped.forEach(r => { s[r.audit.status]++; });
    return s;
  }, [scoped]);

  const visible = React.useMemo(() =>
    scoped.filter(r => {
      if (statusFilter !== 'all' && r.audit.status !== statusFilter) return false;
      if (query && !r.char.title.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    }).sort((a, b) => a.audit.score - b.audit.score),
    [scoped, statusFilter, query]);

  const compact = density === 'compact';
  const isNpcMode = entityFilter === 'npc';

  const npcCount = npcCharacters(data).length;
  const pcCount = playerCharacters(data).length;

  return (
    <div style={{ minHeight: '100%' }}>

      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">{isNpcMode ? 'NPCs' : 'Characters'} · Profile completeness</span>
          <h2>Profile completeness</h2>
          <p className="screen-blurb">
            Drupal enforces required fields at save time. This audit checks the optional
            richness fields — bonds, ideals, portrait, relationships — that AI generation
            benefits from. Thin profiles produce thin stories.
          </p>
        </div>
      </header>

      <div style={{
        fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)',
        letterSpacing: '0.05em', marginBottom: 20,
      }}>
        {data.characters.length > 0
          ? `${isNpcMode ? npcCount : pcCount} ${isNpcMode ? 'NPCs' : 'PCs'} · scored out of ${MAX_SCORE} richness points`
          : 'No character data — check the Drupal connection.'
        }
      </div>

      {/* Summary tiles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <SummaryTile
          label="Total profiles" value={summary.total}
          color="var(--brass-bright)"
          icon={<Icon name="list" size={13} />}
          active={statusFilter === 'all'}
          onClick={() => setStatusFilter('all')}
        />
        <SummaryTile
          label="Full" value={summary.full}
          color={COLOR_PASS}
          icon={<Icon name="flag" size={13} />}
          active={statusFilter === 'full'}
          onClick={() => setStatusFilter(statusFilter === 'full' ? 'all' : 'full')}
        />
        <SummaryTile
          label="Partial" value={summary.partial}
          color={COLOR_PARTIAL}
          icon={<Icon name="book" size={13} />}
          active={statusFilter === 'partial'}
          onClick={() => setStatusFilter(statusFilter === 'partial' ? 'all' : 'partial')}
        />
        <SummaryTile
          label="Thin" value={summary.thin}
          color={COLOR_WARN}
          icon={<Icon name="scroll" size={13} />}
          active={statusFilter === 'thin'}
          onClick={() => setStatusFilter(statusFilter === 'thin' ? 'all' : 'thin')}
        />
      </div>

      {/* Filter bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
        marginBottom: 18, paddingBottom: 14, borderBottom: '1px solid var(--rule)',
      }}>
        <div className="search-field" style={{ flex: 1, minWidth: 200, maxWidth: 320 }}>
          <Icon name="search" size={13} />
          <input
            type="text"
            placeholder="Filter by name…"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
        </div>

        <select
          aria-label="Completeness filter"
          className="console-select"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value as StatusFilter)}
        >
          <option value="all">All profiles</option>
          <option value="thin">Thin only</option>
          <option value="partial">Partial only</option>
          <option value="full">Full only</option>
        </select>

      </div>

      {/* Results */}
      {data.characters.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '50px 20px',
          border: '1px dashed var(--rule)', borderRadius: 8,
        }}>
          <Icon name="drawer" size={36} style={{ color: 'var(--brass-dim)', display: 'block', margin: '0 auto 12px' }} />
          <p className="screen-blurb" style={{ textAlign: 'center' }}>
            No character data from Drupal yet.
          </p>
        </div>
      ) : visible.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '50px 20px',
          border: '1px dashed var(--rule)', borderRadius: 8,
        }}>
          <p className="screen-blurb" style={{ textAlign: 'center' }}>No profiles match this filter.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {visible.map(rec => (
            <ProfileRow key={rec.char.id} rec={rec} compact={compact} />
          ))}
        </div>
      )}
    </div>
  );
}
