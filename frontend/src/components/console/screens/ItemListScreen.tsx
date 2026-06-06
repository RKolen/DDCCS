/**
 * ItemListScreen — `items / i-list`.
 *
 * The Loot Vault in console form. Uses allAllItem Gatsby nodes to paginate
 * past graphql_compose's 100-item limit. Renders an ItemCard per entry;
 * clicking one jumps to ItemDetailScreen (i-view) with ctx.itemIdx set.
 */

import * as React from 'react';
import { useStaticQuery, graphql } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { ItemCard } from '../../molecules/ItemCard';
import { drupalAdminUrl } from '../../../utils/drupalLinks';
import {
  type ItemNode,
  type ItemRarity,
  normalizeRarity,
  rarityDisplayLabel,
} from '../../../types/item';

/* ── Types ──────────────────────────────────────────────────────────── */

const RARITY_ORDER: ItemRarity[] = [
  'common', 'uncommon', 'rare', 'very-rare', 'legendary', 'artifact', 'vestige',
];

interface AllItemListNode {
  drupalId:               string;
  title:                  string;
  path:                   string | null;
  itemType:               string | null;
  itemRarity:             string | null;
  isMagic:                boolean | null;
  itemRequiresAttunement: boolean | null;
  weaponSubtype:          Array<{ name: string }> | null;
  image:                  { mediaImage: { url: string; alt: string } | null } | null;
}

interface ListQueryResult {
  allAllItem: { nodes: AllItemListNode[] };
}

function toItemNode(n: AllItemListNode): ItemNode {
  return {
    id:                     n.drupalId,
    title:                  n.title,
    path:                   n.path,
    itemType:               n.itemType,
    itemRarity:             n.itemRarity,
    isMagic:                n.isMagic,
    itemRequiresAttunement: n.itemRequiresAttunement,
    weaponSubtype:          n.weaponSubtype,
    image:                  n.image,
  };
}

/* ── Screen ─────────────────────────────────────────────────────────── */

export function ItemListScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useStaticQuery<ListQueryResult>(graphql`
    query ConsoleItemsList {
      allAllItem {
        nodes {
          drupalId title path itemType itemRarity isMagic itemRequiresAttunement
          weaponSubtype { name }
          image { mediaImage { url alt } }
        }
      }
    }
  `);

  const rawNodes = data?.allAllItem?.nodes ?? [];

  const [search,   setSearch]   = React.useState('');
  const [rarities, setRarities] = React.useState<Set<ItemRarity>>(new Set());
  const [attune,   setAttune]   = React.useState(false);

  const counts = React.useMemo(() => {
    const c: Partial<Record<ItemRarity, number>> = {};
    rawNodes.forEach(n => {
      const r = normalizeRarity(n.itemRarity);
      c[r] = (c[r] ?? 0) + 1;
    });
    return c;
  }, [rawNodes]);

  const filtered = React.useMemo(() => {
    const q = search.trim().toLowerCase();
    return rawNodes
      .map((n, origIdx) => ({ itemNode: toItemNode(n), origIdx }))
      .filter(({ itemNode }) => {
        if (rarities.size > 0 && !rarities.has(normalizeRarity(itemNode.itemRarity))) return false;
        if (attune && !itemNode.itemRequiresAttunement) return false;
        if (q && !itemNode.title.toLowerCase().includes(q)) return false;
        return true;
      })
      .sort((a, b) => {
        const ai = RARITY_ORDER.indexOf(normalizeRarity(a.itemNode.itemRarity));
        const bi = RARITY_ORDER.indexOf(normalizeRarity(b.itemNode.itemRarity));
        if (bi !== ai) return bi - ai;
        return a.itemNode.title.localeCompare(b.itemNode.title);
      });
  }, [rawNodes, search, rarities, attune]);

  const toggleRarity = (r: ItemRarity): void => {
    const next = new Set(rarities);
    next.has(r) ? next.delete(r) : next.add(r);
    setRarities(next);
  };

  const openItem = (origIdx: number): void => {
    setCtx({ ...ctx, itemIdx: origIdx, _jumpTo: { sectionId: 'items', itemId: 'i-view' } });
  };

  const drupalAddUrl = drupalAdminUrl('/node/add/item');

  if (rawNodes.length === 0) {
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Items</span>
            <h2>The Loot Vault</h2>
            <p className="screen-blurb">No items in Drupal yet.</p>
          </div>
          <div className="screen-head-actions">
            <a href={drupalAddUrl} target="_blank" rel="noreferrer"
               className="primary-btn" style={{ textDecoration: 'none' }}>
              <Icon name="plus" size={11} /> Add item
            </a>
          </div>
        </header>
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', padding: '24px 0' }}>
          Create an Item node in Drupal to populate the vault.
        </p>
      </div>
    );
  }

  return (
    <div className="screen-generic">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Items</span>
          <h2>The Loot Vault</h2>
          <p className="screen-blurb">
            {filtered.length} of {rawNodes.length} item{rawNodes.length === 1 ? '' : 's'}
            {rarities.size > 0 && ` · ${Array.from(rarities).map(rarityDisplayLabel).join(', ')}`}
            {attune && ' · attunement-only'}
          </p>
        </div>
        <div className="screen-head-actions">
          <a href={drupalAddUrl} target="_blank" rel="noreferrer"
             className="primary-btn" style={{ textDecoration: 'none' }}>
            <Icon name="plus" size={11} /> Add item
          </a>
        </div>
      </header>

      {/* Filter bar */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16, alignItems: 'center' }}>
        <div className="search-field" style={{ flex: 1, minWidth: 220, maxWidth: 360 }}>
          <Icon name="search" size={13} />
          <input
            type="text"
            placeholder="Search items..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {RARITY_ORDER.filter(r => counts[r]).map(r => (
          <button
            key={r}
            type="button"
            className="filter-chip"
            data-active={rarities.has(r) || undefined}
            onClick={() => toggleRarity(r)}
            title={`${counts[r]} ${rarityDisplayLabel(r).toLowerCase()}`}
          >
            {rarityDisplayLabel(r)} · {counts[r]}
          </button>
        ))}

        <button
          type="button"
          className="filter-chip"
          data-active={attune || undefined}
          onClick={() => setAttune(v => !v)}
        >
          Attune
        </button>
      </div>

      {/* Card list */}
      {filtered.length === 0 ? (
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic' }}>
          No items match those filters.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(({ itemNode, origIdx }) => (
            <ItemCard
              key={itemNode.id ?? itemNode.title}
              item={itemNode}
              onClick={() => openItem(origIdx)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
