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

interface Check {
  label: string;
  present: boolean;
  note?: string;
}

interface AuditResult {
  status: Completeness;
  score: number;
  maxScore: number;
  checks: Check[];
}

interface AuditRecord {
  char: DrupalCharacter;
  entity: 'npc' | 'pc';
  audit: AuditResult;
}

/* ── API response shape ── */
interface UpdateResult { id: string; title: string }
interface ApiError { error: string }

/* ────────────────────────────────────────────────────────────
   Completeness engine
   ──────────────────────────────────────────────────────────── */

function isEmpty(v: unknown): boolean {
  if (v == null) return true;
  if (Array.isArray(v)) return v.length === 0;
  if (typeof v === 'string') return v.trim() === '';
  return false;
}

const CHECKS: Array<{
  label: string;
  weight: number;
  get: (c: DrupalCharacter) => boolean;
  note: string;
}> = [
    {
      label: 'Portrait image',
      weight: 2,
      get: c => !isEmpty(c.imageUrl),
      note: 'A portrait helps identify the character at the table.',
    },
    {
      label: 'Pronouns',
      weight: 1,
      get: c => !isEmpty(c.pronouns),
      note: 'Used in AI narration and combat descriptions.',
    },
    {
      label: 'Background',
      weight: 1,
      get: c => !isEmpty(c.background),
      note: 'Gives the AI context for roleplay and story suggestions.',
    },
    {
      label: 'Personality traits',
      weight: 2,
      get: c => !isEmpty(c.personalityTraits),
      note: 'AI uses these for in-character dialogue.',
    },
    {
      label: 'Ideals',
      weight: 2,
      get: c => !isEmpty(c.ideals),
      note: 'Drives motivation in story generation.',
    },
    {
      label: 'Bonds',
      weight: 2,
      get: c => !isEmpty(c.bonds),
      note: 'Connects the character to the world; also powers cross-references.',
    },
    {
      label: 'Flaws',
      weight: 2,
      get: c => !isEmpty(c.flaws),
      note: 'Makes generated stories more interesting and realistic.',
    },
    {
      label: 'Referenced by others',
      weight: 1,
      get: () => false, /* filled in by auditCharacter with referencedSet */
      note: 'No other character mentions this name — may be orphaned.',
    },
  ];

const MAX_SCORE = CHECKS.reduce((s, c) => s + c.weight, 0);

function auditCharacter(
  char: DrupalCharacter,
  referencedIds: Set<string>,
): AuditResult {
  let score = 0;
  const checks: Check[] = CHECKS.map(def => {
    const present = def.label === 'Referenced by others'
      ? referencedIds.has(char.id)
      : def.get(char);
    if (present) score += def.weight;
    return { label: def.label, present, note: present ? undefined : def.note };
  });

  const pct: number = score / MAX_SCORE;
  const status: Completeness = pct >= 1 ? 'full' : pct >= 0.6 ? 'partial' : 'thin';
  return { status, score, maxScore: MAX_SCORE, checks };
}

function buildReferencedSet(all: DrupalCharacter[]): Set<string> {
  const referenced = new Set<string>();
  all.forEach(source => {
    const text = [
      ...source.bonds,
      ...source.ideals,
      ...source.flaws,
      ...source.personalityTraits,
      ...source.majorPlotActions,
    ].join(' ').toLowerCase();
    all.forEach(target => {
      if (target.id === source.id) return;
      const title = (target.title ?? '').toLowerCase();
      if (title && text.includes(title)) referenced.add(target.id);
    });
  });
  return referenced;
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

/* ── Inline edit panel (richness fields only) ── */
function EditPanel({ char, onSaved }: { char: DrupalCharacter; onSaved: () => void }): React.ReactElement {
  const [pronouns, setPronouns] = React.useState(char.pronouns ?? '');
  const [background, setBackground] = React.useState(char.background ?? '');
  const [traits, setTraits] = React.useState(char.personalityTraits.join('\n'));
  const [ideals, setIdeals] = React.useState(char.ideals.join('\n'));
  const [bonds, setBonds] = React.useState(char.bonds.join('\n'));
  const [flaws, setFlaws] = React.useState(char.flaws.join('\n'));
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [saved, setSaved] = React.useState(false);

  const splitLines = (v: string): string[] =>
    v.split('\n').map(s => s.trim()).filter(Boolean);

  const handleSave = async (): Promise<void> => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch('/api/update-character', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: char.id,
          pronouns: pronouns.trim() || null,
          background: background.trim() || null,
          personalityTraits: splitLines(traits),
          ideals: splitLines(ideals),
          bonds: splitLines(bonds),
          flaws: splitLines(flaws),
        }),
      });
      if (!res.ok) {
        const data = (await res.json()) as ApiError;
        setError(data.error ?? `Error ${res.status}`);
        return;
      }
      setSaved(true);
      onSaved();
    } catch {
      setError('Network error — could not reach the server.');
    } finally {
      setSaving(false);
    }
  };

  const fieldStyle: React.CSSProperties = {
    width: '100%', background: 'var(--canvas)',
    border: '1px solid var(--rule)', borderRadius: 4,
    color: 'var(--ink)', fontFamily: 'var(--font-body)', fontSize: 13,
    padding: '6px 10px', resize: 'vertical',
  };
  const labelStyle: React.CSSProperties = {
    display: 'block', fontFamily: 'var(--font-display)', fontSize: 9, fontWeight: 700,
    letterSpacing: '0.12em', textTransform: 'uppercase',
    color: 'var(--brass-dim)', marginBottom: 4,
  };

  return (
    <div style={{
      marginTop: 16, padding: '16px 18px', borderRadius: 6,
      background: 'rgba(0,0,0,.2)', border: '1px solid var(--rule)',
    }}>
      <div style={{
        fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700,
        letterSpacing: '0.12em', color: 'var(--brass)', marginBottom: 14,
        textTransform: 'uppercase',
      }}>
        Edit profile — {char.title}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        <div>
          <label style={labelStyle}>Pronouns</label>
          <input
            type="text"
            value={pronouns}
            onChange={e => setPronouns(e.target.value)}
            placeholder="e.g. he/him"
            style={{ ...fieldStyle, resize: 'none' }}
          />
        </div>
        <div>
          <label style={labelStyle}>Background</label>
          <input
            type="text"
            value={background}
            onChange={e => setBackground(e.target.value)}
            placeholder="e.g. Soldier"
            style={{ ...fieldStyle, resize: 'none' }}
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {([
          ['Personality traits', traits, setTraits],
          ['Ideals', ideals, setIdeals],
          ['Bonds', bonds, setBonds],
          ['Flaws', flaws, setFlaws],
        ] as const).map(([label, value, setter]) => (
          <div key={label}>
            <label style={labelStyle}>{label} <span style={{ fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>(one per line)</span></label>
            <textarea
              rows={3}
              value={value}
              onChange={e => setter(e.target.value)}
              placeholder={`Enter ${label.toLowerCase()}, one per line`}
              style={fieldStyle}
            />
          </div>
        ))}
      </div>

      {error != null && (
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-danger)', marginTop: 10 }}>
          {error}
        </p>
      )}
      {saved && (
        <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-success)', marginTop: 10 }}>
          Saved. Reload the page to see updated scores.
        </p>
      )}

      <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
        <button
          type="button"
          className="primary-btn"
          disabled={saving || saved}
          onClick={() => void handleSave()}
        >
          <Icon name="tools" size={11} />
          {saving ? 'Saving...' : saved ? 'Saved' : 'Save changes'}
        </button>
      </div>
    </div>
  );
}

function ProfileRow({
  rec, expanded, onToggle, compact,
}: {
  rec: AuditRecord; expanded: boolean; onToggle: () => void; compact: boolean;
}): React.ReactElement {
  const { char, audit, entity } = rec;
  const [editOpen, setEditOpen] = React.useState(false);
  const meta = STATUS_META[audit.status];
  const isNpc = entity === 'npc';
  const missing = audit.checks.filter(c => !c.present);
  const initials = char.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();

  const classLabel = isNpc
    ? (char.role ?? null)
    : (char.characterClass != null && char.level != null
      ? `${char.characterClass} ${char.level}`
      : char.characterClass ?? null);

  return (
    <div style={{
      background: 'var(--canvas-raised)',
      border: `1px solid ${expanded ? 'var(--brass-dim)' : 'var(--rule)'}`,
      borderRadius: 8, overflow: 'hidden',
      borderLeft: `3px solid ${meta.color}`,
    }}>
      <button
        type="button"
        onClick={onToggle}
        style={{
          display: 'grid',
          gridTemplateColumns: '40px 1fr auto auto',
          gap: 14, alignItems: 'center',
          width: '100%', background: 'none', border: 'none', cursor: 'pointer',
          padding: compact ? '10px 16px' : '14px 18px', textAlign: 'left',
        }}
      >
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
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 15, color: 'var(--brass-bright)', fontWeight: 600 }}>
              {char.title}
            </span>
            {char.nickname != null && char.nickname !== '' && (
              <span style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12, color: 'var(--ink-dim)' }}>
                &ldquo;{char.nickname}&rdquo;
              </span>
            )}
            {classLabel != null && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-dim)' }}>
                {classLabel}
              </span>
            )}
          </div>
          <ScoreBar score={audit.score} maxScore={audit.maxScore} color={meta.color} />
        </div>

        {/* Status badge */}
        <span style={{
          fontFamily: 'var(--font-display)', fontSize: 9, fontWeight: 700,
          letterSpacing: '0.12em', textTransform: 'uppercase', padding: '3px 8px',
          borderRadius: 4, border: `1px solid ${meta.color}`,
          color: meta.color,
          background: `color-mix(in srgb, ${meta.color} 10%, transparent)`,
          whiteSpace: 'nowrap',
        }}>
          {meta.label}
          {missing.length > 0 && ` · ${missing.length} missing`}
        </span>

        <Icon
          name={expanded ? 'chevronDown' : 'chevron'}
          size={12}
          style={{ color: 'var(--brass-dim)', opacity: 0.7 }}
        />
      </button>

      {expanded && (
        <div style={{
          padding: compact ? '4px 18px 16px 18px' : '6px 20px 20px',
          borderTop: '1px solid var(--rule)',
        }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: 8, marginTop: 14,
          }}>
            {audit.checks.map(check => (
              <div
                key={check.label}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: 10,
                  padding: '8px 12px', borderRadius: 6,
                  background: check.present
                    ? `color-mix(in srgb, ${COLOR_PASS} 6%, transparent)`
                    : 'color-mix(in srgb, #e8a030 6%, transparent)',
                  border: `1px solid ${check.present ? 'color-mix(in srgb, #5a9e6f 25%, transparent)' : 'color-mix(in srgb, #e8a030 25%, transparent)'}`,
                }}
              >
                <span style={{
                  width: 16, height: 16, borderRadius: 9999, flexShrink: 0, marginTop: 1,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: check.present
                    ? `color-mix(in srgb, ${COLOR_PASS} 20%, transparent)`
                    : `color-mix(in srgb, ${COLOR_WARN} 20%, transparent)`,
                  border: `1px solid ${check.present ? COLOR_PASS : COLOR_WARN}`,
                  color: check.present ? COLOR_PASS : COLOR_WARN,
                  fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 9,
                }}>
                  {check.present ? '✓' : '!'}
                </span>
                <div>
                  <div style={{
                    fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700,
                    letterSpacing: '0.08em', color: check.present ? 'var(--ink-dim)' : 'var(--ink)',
                  }}>
                    {check.label}
                  </div>
                  {!check.present && check.note != null && (
                    <div style={{
                      fontFamily: 'var(--font-body)', fontSize: 12,
                      color: 'var(--ink-dim)', marginTop: 2, lineHeight: 1.4,
                    }}>
                      {check.note}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 14 }}>
            <button
              type="button"
              className={`ghost-btn${editOpen ? ' ghost-active' : ''}`}
              onClick={() => setEditOpen(p => !p)}
            >
              <Icon name="tools" size={11} />
              {editOpen ? 'Close editor' : 'Edit profile'}
            </button>
          </div>
          {editOpen && (
            <EditPanel char={char} onSaved={() => setEditOpen(false)} />
          )}
        </div>
      )}
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
  const [density, setDensity] = React.useState<'comfortable' | 'compact'>('comfortable');
  const [expanded, setExpanded] = React.useState<Record<string, boolean>>({});

  const audited = React.useMemo<AuditRecord[]>(() => {
    const all = data.characters;
    const referenced = buildReferencedSet(all);
    return all.map(char => ({
      char,
      entity: char.characterType === false ? 'npc' : 'pc',
      audit: auditCharacter(char, referenced),
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

  const toggle = (id: string): void => setExpanded(p => ({ ...p, [id]: !p[id] }));
  const setAllExp = (val: boolean): void => {
    const next: Record<string, boolean> = {};
    visible.forEach(r => { next[r.char.id] = val; });
    setExpanded(next);
  };

  const linkBtnStyle: React.CSSProperties = {
    background: 'none', border: 'none', cursor: 'pointer',
    fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--ink-dim)',
    letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 700, padding: 0,
  };

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
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value as StatusFilter)}
          style={{
            fontFamily: 'var(--font-display)', fontSize: 10, letterSpacing: '0.08em',
            background: 'var(--canvas-raised)', color: 'var(--ink-dim)',
            border: '1px solid var(--rule)', borderRadius: 4, padding: '6px 10px', cursor: 'pointer',
          }}
        >
          <option value="all">All profiles</option>
          <option value="thin">Thin only</option>
          <option value="partial">Partial only</option>
          <option value="full">Full only</option>
        </select>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button type="button" onClick={() => setAllExp(true)} style={linkBtnStyle}>Expand all</button>
          <span style={{ color: 'var(--ink-faint)' }}>·</span>
          <button type="button" onClick={() => setAllExp(false)} style={linkBtnStyle}>Collapse all</button>
        </div>
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
            <ProfileRow
              key={rec.char.id}
              rec={rec}
              expanded={!!expanded[rec.char.id]}
              onToggle={() => toggle(rec.char.id)}
              compact={compact}
            />
          ))}
        </div>
      )}
    </div>
  );
}
