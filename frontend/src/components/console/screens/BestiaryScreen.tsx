/**
 * BestiaryScreen — `monsters / m-list`
 *
 * Filterable catalogue of all monster nodes.
 * Design reference: /project/Bestiary.html
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData } from '../ConsoleContext';
import type { DrupalMonster } from '../ConsoleContext';

/* ────────────────────────────────────────────────────────────
   Helpers
   ──────────────────────────────────────────────────────────── */

function crTier(cr: number | null): { label: string; color: string } {
  if (cr == null) return { label: 'Unknown', color: 'var(--ink-dim)' };
  if (cr >= 17)   return { label: 'Deadly',   color: 'var(--color-danger)' };
  if (cr >= 11)   return { label: 'Hard',     color: 'var(--color-warning)' };
  if (cr >= 5)    return { label: 'Medium',   color: 'var(--color-info)' };
  return            { label: 'Standard', color: 'var(--color-success)' };
}

function crBand(cr: number | null): string {
  if (cr == null)  return 'unknown';
  if (cr >= 17)    return 'deadly';
  if (cr >= 11)    return 'hard';
  if (cr >= 5)     return 'medium';
  return 'standard';
}

const ABILITIES = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'] as const;

/* ────────────────────────────────────────────────────────────
   MonsterSigil — portrait placeholder matching the design
   ──────────────────────────────────────────────────────────── */

function MonsterSigil({ monster, size = 54 }: { monster: DrupalMonster; size?: number }): React.ReactElement {
  const initials = monster.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
  return (
    <div style={{
      width: size, height: size, borderRadius: 8, flexShrink: 0,
      background: 'var(--canvas-raised)', border: '1px solid var(--rule)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      overflow: 'hidden',
    }}>
      {monster.imageUrl
        ? <img src={monster.imageUrl} alt={monster.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        : <span style={{ fontFamily: 'var(--font-display)', fontSize: size * 0.24, color: 'var(--brass)', fontWeight: 700 }}>{initials}</span>
      }
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   CR badge
   ──────────────────────────────────────────────────────────── */

function CRBadge({ cr }: { cr: number | null }): React.ReactElement {
  const tier = crTier(cr);
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      width: 40, height: 40, borderRadius: 6, flexShrink: 0,
      background: `color-mix(in srgb, ${tier.color} 12%, transparent)`,
      border: `1px solid color-mix(in srgb, ${tier.color} 40%, transparent)`,
    }}>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700, color: tier.color, lineHeight: 1 }}>
        {cr ?? '?'}
      </span>
      <span style={{ fontFamily: 'var(--font-display)', fontSize: 7, color: tier.color, letterSpacing: '0.1em', textTransform: 'uppercase' }}>CR</span>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Monster row (list view)
   ──────────────────────────────────────────────────────────── */

function MonsterRow({
  monster, onSelect, active,
}: {
  monster: DrupalMonster;
  onSelect: () => void;
  active: boolean;
}): React.ReactElement {
  const tier    = crTier(monster.cr);
  const isBoss  = monster.profileType === 'major';

  return (
    <button
      type="button"
      onClick={onSelect}
      style={{
        display: 'grid', gridTemplateColumns: '54px 1fr auto 40px',
        gap: 16, alignItems: 'center', width: '100%',
        background: active ? 'var(--canvas-raised)' : 'var(--canvas)',
        border: `1px solid ${active ? 'var(--brass-dim)' : 'var(--rule)'}`,
        borderLeft: `3px solid ${tier.color}`,
        borderRadius: 8, padding: '12px 16px', textAlign: 'left', cursor: 'pointer',
        transition: '120ms ease',
      }}
    >
      <MonsterSigil monster={monster} size={54} />

      <div style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap', marginBottom: 3 }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, color: 'var(--brass-bright)', fontWeight: 600 }}>
            {monster.title}
          </span>
          {monster.nickname != null && (
            <span style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12, color: 'var(--ink-dim)' }}>
              &ldquo;{monster.nickname}&rdquo;
            </span>
          )}
          {isBoss && (
            <span style={{
              fontFamily: 'var(--font-display)', fontSize: 8, fontWeight: 700,
              letterSpacing: '0.14em', textTransform: 'uppercase', padding: '2px 7px',
              borderRadius: 4, border: '1px solid var(--brass-dim)',
              color: 'var(--brass)', background: 'var(--gold-a05)',
            }}>Boss</span>
          )}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-dim)', letterSpacing: '0.02em' }}>
          {[monster.size, monster.monsterType, monster.alignment].filter(Boolean).join(' · ')}
        </div>
        {monster.tagline != null && (
          <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12.5, color: 'var(--ink-dim)', marginTop: 4, lineHeight: 1.4 }}>
            {monster.tagline}
          </p>
        )}
      </div>

      <div style={{ textAlign: 'right' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--ink)' }}>
          {monster.maxHp != null ? `${monster.maxHp} HP` : '—'}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-dim)' }}>
          {monster.ac != null ? `AC ${monster.ac}` : ''}
        </div>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: 8, color: tier.color, letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 3 }}>
          {tier.label}
        </div>
      </div>

      <CRBadge cr={monster.cr} />
    </button>
  );
}

/* ────────────────────────────────────────────────────────────
   Screen
   ──────────────────────────────────────────────────────────── */

export function BestiaryScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data     = useConsoleData();
  const monsters = data.monsters;

  const [search,   setSearch]   = React.useState('');
  const [typeFilter, setType]   = React.useState('all');
  const [bandFilter, setBand]   = React.useState('all');
  const [sortKey,  setSortKey]  = React.useState<'cr-desc' | 'cr-asc' | 'name'>('cr-desc');

  const selectedIdx = (ctx.monsterIdx as number | undefined) ?? 0;

  const allTypes = React.useMemo(() =>
    ['all', ...Array.from(new Set(monsters.map(m => m.monsterType).filter(Boolean)))],
  [monsters]) as string[];

  const filtered = React.useMemo(() => {
    let list = monsters.filter(m => {
      if (typeFilter !== 'all' && m.monsterType !== typeFilter) return false;
      if (bandFilter !== 'all' && crBand(m.cr) !== bandFilter) return false;
      if (search && !m.title.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
    if (sortKey === 'cr-desc') list = [...list].sort((a, b) => (b.cr ?? -1) - (a.cr ?? -1));
    if (sortKey === 'cr-asc')  list = [...list].sort((a, b) => (a.cr ?? -1) - (b.cr ?? -1));
    if (sortKey === 'name')    list = [...list].sort((a, b) => a.title.localeCompare(b.title));
    return list;
  }, [monsters, typeFilter, bandFilter, search, sortKey]);

  const summaryTiles = React.useMemo(() => {
    const deadly   = monsters.filter(m => (m.cr ?? 0) >= 17).length;
    const hard     = monsters.filter(m => { const c = m.cr ?? 0; return c >= 11 && c < 17; }).length;
    const bosses   = monsters.filter(m => m.profileType === 'major').length;
    return { total: monsters.length, deadly, hard, bosses };
  }, [monsters]);

  const selectMonster = (idx: number): void => {
    setCtx({ ...ctx, monsterIdx: idx });
  };

  if (monsters.length === 0) {
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Monsters · Bestiary</span>
            <h2>Bestiary</h2>
            <p className="screen-blurb">
              No monster nodes in Drupal yet. Create <code>node--monster</code> content to populate the bestiary.
            </p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100%' }}>
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Monsters · Bestiary</span>
          <h2>Bestiary</h2>
          <p className="screen-blurb">
            All campaign monsters. Click a row to view the full stat block or launch an encounter.
          </p>
        </div>
      </header>

      {/* Summary tiles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 20 }}>
        {[
          { label: 'Total', value: summaryTiles.total, color: 'var(--brass-bright)' },
          { label: 'Deadly (CR 17+)', value: summaryTiles.deadly, color: 'var(--color-danger)' },
          { label: 'Hard (CR 11+)', value: summaryTiles.hard, color: 'var(--color-warning)' },
          { label: 'Boss', value: summaryTiles.bosses, color: 'var(--color-partial)' },
        ].map(tile => (
          <div key={tile.label} style={{
            background: 'var(--canvas-raised)', border: '1px solid var(--rule)',
            borderRadius: 8, padding: '12px 16px',
          }}>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 9, color: 'var(--ink-dim)', letterSpacing: '0.14em', textTransform: 'uppercase', fontWeight: 700, marginBottom: 4 }}>
              {tile.label}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 26, fontWeight: 700, color: tile.color, lineHeight: 1 }}>
              {tile.value}
            </div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div style={{
        display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center',
        marginBottom: 16, paddingBottom: 14, borderBottom: '1px solid var(--rule)',
      }}>
        <div className="search-field" style={{ flex: 1, minWidth: 180, maxWidth: 280 }}>
          <Icon name="search" size={13} />
          <input type="text" placeholder="Search monsters..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        <select className="console-select" aria-label="Type filter" value={typeFilter} onChange={e => setType(e.target.value)}>
          <option value="all">All types</option>
          {allTypes.filter(t => t !== 'all').map(t => <option key={t} value={t}>{t}</option>)}
        </select>

        <select className="console-select" aria-label="Difficulty filter" value={bandFilter} onChange={e => setBand(e.target.value)}>
          <option value="all">All difficulties</option>
          <option value="deadly">Deadly (CR 17+)</option>
          <option value="hard">Hard (CR 11–16)</option>
          <option value="medium">Medium (CR 5–10)</option>
          <option value="standard">Standard (CR &lt;5)</option>
        </select>

        <select className="console-select" aria-label="Sort" value={sortKey} onChange={e => setSortKey(e.target.value as typeof sortKey)}>
          <option value="cr-desc">CR: Highest first</option>
          <option value="cr-asc">CR: Lowest first</option>
          <option value="name">Name A–Z</option>
        </select>

        <span className="muted mono" style={{ fontSize: 10, marginLeft: 'auto' }}>
          {filtered.length} of {monsters.length}
        </span>
      </div>

      {/* Monster list */}
      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 20px', border: '1px dashed var(--rule)', borderRadius: 8 }}>
          <p className="screen-blurb" style={{ textAlign: 'center' }}>No monsters match this filter.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map((m, i) => (
            <MonsterRow
              key={m.id}
              monster={m}
              active={i === selectedIdx}
              onSelect={() => selectMonster(i)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export { ABILITIES };
