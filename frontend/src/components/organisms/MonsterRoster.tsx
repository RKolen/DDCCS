/**
 * MonsterRoster — the Bestiary grid.
 *
 * Mirrors the ItemRoster pattern: takes a query result, computes filters,
 * renders a monster list. Used by the /monsters/ page.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import * as styles from './MonsterRoster.module.css';

/* ── Data shapes ────────────────────────────────────────────────────── */

export interface MonsterNode {
  id:               string;
  title:            string;
  challengeRating:  number | null;
  type:             { name: string } | null;
  monsterSize:      string | null;
  monsterAlignment: string | null;
  path:             string | null;
  image:            { mediaImage: { url: string; alt: string } | null } | null;
}

export interface MonsterRosterData {
  drupal: {
    nodeMonsters: {
      nodes: MonsterNode[];
    };
  } | null;
}

interface MonsterRosterProps {
  data: MonsterRosterData;
}

/* ── CR tier definitions ────────────────────────────────────────────── */

interface CrTier {
  key:   string;
  label: string;
  min:   number;
  color: string;
}

const CR_TIERS: CrTier[] = [
  { key: 'cr0_4',   label: '0–4',   min: 0,  color: 'var(--color-success)' },
  { key: 'cr5_9',   label: '5–9',   min: 5,  color: 'var(--color-info)' },
  { key: 'cr10_14', label: '10–14', min: 10, color: 'var(--color-warning)' },
  { key: 'cr15_19', label: '15–19', min: 15, color: 'var(--color-danger)' },
  { key: 'cr20',    label: '20+',   min: 20, color: 'var(--color-rarity-artifact)' },
];

function getCrTierKey(cr: number | null): string {
  if (cr == null) return '';
  if (cr >= 20) return 'cr20';
  if (cr >= 15) return 'cr15_19';
  if (cr >= 10) return 'cr10_14';
  if (cr >= 5)  return 'cr5_9';
  return 'cr0_4';
}

function getCrColor(cr: number | null): string {
  if (cr == null) return 'var(--color-text-secondary)';
  const tier = CR_TIERS.find(t => t.key === getCrTierKey(cr));
  return tier?.color ?? 'var(--color-text-secondary)';
}

function formatCr(cr: number | null): string {
  if (cr == null) return '?';
  if (cr === 0.125) return '1/8';
  if (cr === 0.25)  return '1/4';
  if (cr === 0.5)   return '1/2';
  return String(cr);
}

/* ── MonsterRow ─────────────────────────────────────────────────────── */

interface MonsterRowProps {
  monster: MonsterNode;
}

function MonsterRow({ monster: m }: MonsterRowProps): React.ReactElement {
  const color    = getCrColor(m.challengeRating);
  const initials = m.title.split(' ').map((w: string) => w[0]).slice(0, 2).join('').toUpperCase();

  const row = (
    <div className={styles.row} style={{ borderLeft: `3px solid ${color}` }}>
      <div className={styles.thumb}>
        {m.image?.mediaImage
          ? <img src={m.image.mediaImage.url} alt={m.title} className={styles.thumbImg} />
          : <span className={styles.thumbInitials}>{initials}</span>
        }
      </div>

      <div className={styles.body}>
        <div className={styles.name}>{m.title}</div>
        <div className={styles.subtitle}>
          {[m.monsterSize, m.type?.name, m.monsterAlignment].filter(Boolean).join(' · ')}
        </div>
      </div>

      {m.type != null && (
        <div className={styles.typePill}>{m.type.name}</div>
      )}

      <div className={styles.crBadge} style={{ color }}>
        <div className={styles.crValue}>{formatCr(m.challengeRating)}</div>
        <div className={styles.crLabel}>CR</div>
      </div>
    </div>
  );

  if (m.path) {
    return <Link to={m.path} className={styles.rowLink}>{row}</Link>;
  }
  return <>{row}</>;
}

/* ── MonsterRoster ──────────────────────────────────────────────────── */

export function MonsterRoster({ data }: MonsterRosterProps): React.ReactElement {
  const all = data?.drupal?.nodeMonsters?.nodes ?? [];

  const [search,  setSearch]  = React.useState('');
  const [crKeys,  setCrKeys]  = React.useState<Set<string>>(new Set());
  const [types,   setTypes]   = React.useState<Set<string>>(new Set());

  const allTypes = React.useMemo(() => {
    const s = new Set<string>();
    all.forEach(m => { if (m.type?.name) s.add(m.type.name); });
    return Array.from(s).sort();
  }, [all]);

  const tierCounts = React.useMemo(() => {
    const c: Record<string, number> = {};
    CR_TIERS.forEach(t => { c[t.key] = 0; });
    all.forEach(m => {
      const k = getCrTierKey(m.challengeRating);
      if (k) { c[k] = (c[k] ?? 0) + 1; }
    });
    return c;
  }, [all]);

  const filtered = React.useMemo(() => {
    const q = search.trim().toLowerCase();
    return all.filter(m => {
      if (crKeys.size > 0 && !crKeys.has(getCrTierKey(m.challengeRating))) return false;
      if (types.size > 0 && !(m.type?.name != null && types.has(m.type.name))) return false;
      if (q && !m.title.toLowerCase().includes(q)) return false;
      return true;
    }).sort((a, b) => {
      const ac = a.challengeRating ?? -1;
      const bc = b.challengeRating ?? -1;
      if (bc !== ac) return bc - ac;
      return a.title.localeCompare(b.title);
    });
  }, [all, search, crKeys, types]);

  const toggle = <T,>(set: Set<T>, v: T): Set<T> => {
    const next = new Set(set);
    next.has(v) ? next.delete(v) : next.add(v);
    return next;
  };

  const bgClass = (key: string): string =>
    (styles[`bg_${key}` as keyof typeof styles] as string | undefined) ?? '';

  return (
    <div className={styles.page}>

      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>The Bestiary</span>
          <h1 className={styles.title}>Monsters &amp; Creatures</h1>
          <p className={styles.blurb}>
            Every beast, fiend, and aberration catalogued by the Dungeon Master.
          </p>
        </div>
      </header>

      {/* ── CR summary band ─────────────────────────────────────── */}
      <div className={styles.summary}>
        {CR_TIERS.filter(t => (tierCounts[t.key] ?? 0) > 0).map(t => (
          <div key={t.key} className={`${styles.summaryCell} ${bgClass(t.key)}`}>
            <div className={styles.summaryLabel}>CR {t.label}</div>
            <div className={styles.summaryCount}>{tierCounts[t.key]}</div>
          </div>
        ))}
        <div className={`${styles.summaryCell} ${styles.summaryTotal}`}>
          <div className={styles.summaryLabel}>Total</div>
          <div className={styles.summaryCount}>{all.length}</div>
        </div>
      </div>

      {/* ── Filter bar ──────────────────────────────────────────── */}
      <div className={styles.filters}>
        <input
          type="search"
          className={styles.search}
          placeholder="Search by name..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />

        <div className={styles.chipRow}>
          <span className={styles.chipLabel}>CR</span>
          {CR_TIERS.filter(t => (tierCounts[t.key] ?? 0) > 0).map(t => (
            <button
              key={t.key}
              type="button"
              className={`${styles.chip}${crKeys.has(t.key) ? ` ${styles.chipActive}` : ''}`}
              onClick={() => setCrKeys(toggle(crKeys, t.key))}
            >
              {t.label}
            </button>
          ))}
          {crKeys.size > 0 && (
            <button type="button" className={styles.chipClear} onClick={() => setCrKeys(new Set())}>
              clear
            </button>
          )}
        </div>

        {allTypes.length > 0 && (
          <div className={styles.chipRow}>
            <span className={styles.chipLabel}>Type</span>
            {allTypes.map(t => (
              <button
                key={t}
                type="button"
                className={`${styles.chip}${types.has(t) ? ` ${styles.chipActive}` : ''}`}
                onClick={() => setTypes(toggle(types, t))}
              >
                {t}
              </button>
            ))}
            {types.size > 0 && (
              <button type="button" className={styles.chipClear} onClick={() => setTypes(new Set())}>
                clear
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── Results ─────────────────────────────────────────────── */}
      <div className={styles.resultCount}>
        {filtered.length === all.length
          ? `All ${all.length} creatures`
          : `${filtered.length} of ${all.length} creatures`}
      </div>

      {filtered.length === 0 ? (
        <div className={styles.empty}>
          <p>No creatures match those terms. The bestiary is silent.</p>
        </div>
      ) : (
        <div className={styles.list}>
          {filtered.map(m => <MonsterRow key={m.id} monster={m} />)}
        </div>
      )}

    </div>
  );
}
