/**
 * ItemDetailScreen — `items / i-view`.
 *
 * Split-pane layout: left column is a scrollable item picker, right column
 * renders the full ItemSheet for the selected entry.
 *
 * ctx.itemIdx indexes into the allAllItem list. ItemListScreen sets this
 * value and _jumpTo before navigating here.
 */

import * as React from 'react';
import { useStaticQuery, graphql, Link } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { ItemSheet } from '../../molecules/ItemSheet';
import { drupalAdminUrl } from '../../../utils/drupalLinks';
import {
  type ItemNode,
  normalizeRarity,
  rarityDisplayLabel,
} from '../../../types/item';

/* ── Types ──────────────────────────────────────────────────────────── */

interface AllItemDetailNode {
  drupalId:               string;
  title:                  string;
  path:                   string | null;
  itemType:               string | null;
  itemRarity:             string | null;
  isMagic:                boolean | null;
  itemRequiresAttunement: boolean | null;
  descriptionHtml:        string | null;
  weaponSubtype:          Array<{ name: string }> | null;
  image:                  { mediaImage: { url: string; alt: string } | null } | null;
}

interface DetailQueryResult {
  allAllItem: { nodes: AllItemDetailNode[] };
}

function toItemNode(n: AllItemDetailNode): ItemNode {
  return {
    id:                     n.drupalId,
    title:                  n.title,
    path:                   n.path,
    itemType:               n.itemType,
    itemRarity:             n.itemRarity,
    isMagic:                n.isMagic,
    itemRequiresAttunement: n.itemRequiresAttunement,
    body:                   n.descriptionHtml ? { value: n.descriptionHtml } : null,
    weaponSubtype:          n.weaponSubtype,
    image:                  n.image,
  };
}

/* ── Screen ─────────────────────────────────────────────────────────── */

export function ItemDetailScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useStaticQuery<DetailQueryResult>(graphql`
    query ConsoleItemDetail {
      allAllItem {
        nodes {
          drupalId title path itemType itemRarity isMagic itemRequiresAttunement
          descriptionHtml
          weaponSubtype { name }
          image { mediaImage { url alt } }
        }
      }
    }
  `);

  const all      = data?.allAllItem?.nodes ?? [];
  const idx      = (ctx.itemIdx as number | undefined) ?? 0;
  const rawNode  = all[idx] ?? null;
  const item: ItemNode | null = rawNode ? toItemNode(rawNode) : null;

  return (
    <div className="screen-itemdetails">

      {/* Picker rail */}
      {all.length > 0 && (
        <aside className="char-picker">
          <ul className="char-picker-list">
            {all.map((n, i) => {
              const rarity   = normalizeRarity(n.itemRarity);
              const initials = n.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
              return (
                <li key={n.drupalId}>
                  <button
                    type="button"
                    className={`char-picker-item${i === idx ? ' active' : ''}`}
                    onClick={() => setCtx({ ...ctx, itemIdx: i })}
                  >
                    <span className="char-pip" data-rarity={rarity}>{initials}</span>
                    <span className="char-pip-meta">
                      <strong>{n.title}</strong>
                      <span>{rarityDisplayLabel(rarity)}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>
      )}

      {/* Sheet */}
      <div className="char-sheet">
        {item === null ? (
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic' }}>
            {all.length === 0
              ? 'No items in Drupal. Create an Item node to begin building the vault.'
              : 'Select an item from the list.'}
          </p>
        ) : (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <span className="reader-eyebrow">Item Sheet</span>
              <div style={{ display: 'flex', gap: 8 }}>
                {item.path != null && (
                  <Link to={item.path} className="ghost-btn" style={{ textDecoration: 'none' }}>
                    <Icon name="scroll" size={11} /> Full sheet
                  </Link>
                )}
                {item.id != null && (
                  <a
                    href={drupalAdminUrl(`/node/${item.id}/edit`)}
                    target="_blank"
                    rel="noreferrer"
                    className="ghost-btn"
                    style={{ textDecoration: 'none' }}
                  >
                    <Icon name="tools" size={11} /> Edit in Drupal
                  </a>
                )}
              </div>
            </div>
            <ItemSheet item={item} />
          </>
        )}
      </div>

    </div>
  );
}
