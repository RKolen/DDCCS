/**
 * ItemRoster — the Loot Vault grid.
 *
 * Mirrors `CharacterRoster` pattern: takes a query result, computes
 * filters, renders an `ItemCard` grid. Used by /items/ page.
 *
 * Uses `allAllItem` Gatsby nodes (paginates past graphql_compose 100-item limit).
 */

import * as React from 'react';
import { ItemCard } from '../molecules/ItemCard';
import {
  type ItemNode,
  type ItemRarity,
  normalizeRarity,
  normalizeType,
  rarityDisplayLabel,
  typeDisplayLabel,
} from '../../types/item';
import * as styles from './ItemRoster.module.css';

const RARITY_ORDER: ItemRarity[] = [
  'common', 'uncommon', 'rare', 'very-rare', 'legendary', 'artifact', 'vestige',
];

export interface ItemRosterData {
  allAllItem: { nodes: ItemNode[] };
}

interface ItemRosterProps {
  data: ItemRosterData;
}

export function ItemRoster({ data }: ItemRosterProps): React.ReactElement {
  const all = data?.allAllItem?.nodes ?? [];
  const [search,   setSearch]   = React.useState('');
  const [rarities, setRarities] = React.useState<Set<ItemRarity>>(new Set());
  const [types,    setTypes]    = React.useState<Set<string>>(new Set());
  const [attune,   setAttune]   = React.useState(false);

  const allTypes = React.useMemo(() => {
    const s = new Set<string>();
    all.forEach(i => { if (i.itemType) s.add(normalizeType(i.itemType, i.weaponSubtype)); });
    return Array.from(s).sort();
  }, [all]);

  const rarityCounts = React.useMemo(() => {
    const c: Record<ItemRarity, number> = {
      common: 0, uncommon: 0, rare: 0,
      'very-rare': 0, legendary: 0, artifact: 0, vestige: 0,
    };
    all.forEach(i => { c[normalizeRarity(i.itemRarity ?? null)]++; });
    return c;
  }, [all]);

  const filtered = React.useMemo(() => {
    const q = search.trim().toLowerCase();
    return all.filter(i => {
      const r = normalizeRarity(i.itemRarity);
      const t = normalizeType(i.itemType, i.weaponSubtype);
      if (rarities.size > 0 && !rarities.has(r)) return false;
      if (types.size > 0 && !types.has(t))       return false;
      if (attune && !i.itemRequiresAttunement)   return false;
      if (q && !i.title.toLowerCase().includes(q)) return false;
      return true;
    }).sort((a, b) => {
      const ai = RARITY_ORDER.indexOf(normalizeRarity(a.itemRarity ?? null));
      const bi = RARITY_ORDER.indexOf(normalizeRarity(b.itemRarity ?? null));
      if (bi !== ai) return bi - ai;
      return a.title.localeCompare(b.title);
    });
  }, [all, search, rarities, types, attune]);

  const toggle = <T,>(set: Set<T>, v: T): Set<T> => {
    const next = new Set(set);
    next.has(v) ? next.delete(v) : next.add(v);
    return next;
  };

  const bgClass = (r: ItemRarity): string => {
    const key = r.replace('-', '_') as keyof typeof styles;
    return (styles[`bg_${key}`] as string | undefined) ?? '';
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <span className={styles.eyebrow}>The Loot Vault</span>
          <h1 className={styles.title}>Items &amp; Relics</h1>
          <p className={styles.blurb}>
            Every relic, weapon, vial, and curio recorded by the Dungeon Master across the campaign.
          </p>
        </div>
      </header>

      {/* ── Rarity summary band ─────────────────────────────────── */}
      <div className={styles.summary}>
        {RARITY_ORDER.filter(r => rarityCounts[r] > 0).map(r => (
          <div key={r} className={`${styles.summaryCell} ${bgClass(r)}`}>
            <div className={styles.summaryLabel}>{rarityDisplayLabel(r)}</div>
            <div className={styles.summaryCount}>{rarityCounts[r]}</div>
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
          <span className={styles.chipLabel}>Rarity</span>
          {RARITY_ORDER.filter(r => rarityCounts[r] > 0).map(r => (
            <button
              key={r}
              type="button"
              className={`${styles.chip}${rarities.has(r) ? ` ${styles.chipActive}` : ''}`}
              onClick={() => setRarities(toggle(rarities, r))}
            >
              {rarityDisplayLabel(r)}
            </button>
          ))}
          {rarities.size > 0 && (
            <button type="button" className={styles.chipClear} onClick={() => setRarities(new Set())}>
              clear
            </button>
          )}
        </div>

        <div className={styles.chipRow}>
          <span className={styles.chipLabel}>Type</span>
          {allTypes.map(t => (
            <button
              key={t}
              type="button"
              className={`${styles.chip}${types.has(t) ? ` ${styles.chipActive}` : ''}`}
              onClick={() => setTypes(toggle(types, t))}
            >
              {typeDisplayLabel(t as Parameters<typeof typeDisplayLabel>[0])}
            </button>
          ))}
          {types.size > 0 && (
            <button type="button" className={styles.chipClear} onClick={() => setTypes(new Set())}>
              clear
            </button>
          )}
          <span className={styles.flexSpace} />
          <button
            type="button"
            className={`${styles.chip}${attune ? ` ${styles.chipActive}` : ''}`}
            onClick={() => setAttune(!attune)}
          >
            Requires Attunement
          </button>
        </div>
      </div>

      {/* ── Results ─────────────────────────────────────────────── */}
      <div className={styles.resultCount}>
        {filtered.length === all.length
          ? `All ${all.length} items`
          : `${filtered.length} of ${all.length} items`}
      </div>

      {filtered.length === 0 ? (
        <div className={styles.empty}>
          <p>No relics match those terms. The vault is silent.</p>
        </div>
      ) : (
        <div className={styles.grid}>
          {filtered.map(item => (
            <ItemCard key={item.id ?? item.title} item={item} />
          ))}
        </div>
      )}
    </div>
  );
}
