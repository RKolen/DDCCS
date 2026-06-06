/**
 * ItemCard — compact inventory row ("Inventory Strip").
 *
 * Accepts a Drupal `ItemNode` directly. Adds:
 *   - 70px portrait thumbnail (image OR type icon) with rarity glow
 *   - rarity-tinted 3px left rule + inner glow
 *   - 3-column grid (thumb / body / meta)
 *   - attunement chip inline with the name
 *
 * Pass `detailed={false}` for the legacy compact one-line layout.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import { Badge } from '../atoms/Badge';
import { GameIcon } from '../atoms/GameIcon';
import type { GameIconName } from '../../types/icons';
import {
  type ItemNode,
  type ItemRarity,
  type ItemType,
  normalizeRarity,
  normalizeType,
  rarityDisplayLabel,
  typeDisplayLabel,
} from '../../types/item';
import * as styles from './ItemCard.module.css';

export type { ItemRarity, ItemType } from '../../types/item';

interface ItemCardProps {
  item: ItemNode;
  detail?: string;
  /** When true, lays out as a wider strip (default).
   *  Pass false for the legacy compact one-line layout. */
  detailed?: boolean;
  to?:    string | null;
  onClick?: () => void;
  className?: string;
}

const TYPE_ICONS: Record<ItemType, GameIconName> = {
  weapon:        'broadsword',
  ranged_weapon: 'arrow-flights',
  armor:         'round-shield',
  shield:        'round-shield',
  ring:          'ring',
  staff:         'magic-swirl',
  wondrous:      'gem-pendant',
  scroll:        'scroll-unfurled',
  potion:        'potion-ball',
  tool:          'swap-bag',
  gear:          'swap-bag',
};

const RARITY_CLASS: Record<ItemRarity, string> = {
  common:      styles.rarityCommon,
  uncommon:    styles.rarityUncommon,
  rare:        styles.rarityRare,
  'very-rare': styles.rarityVeryRare,
  legendary:   styles.rarityLegendary,
  artifact:    styles.rarityArtifact,
  vestige:     styles.rarityVestige,
};

export function ItemCard({
  item,
  detail,
  detailed = true,
  to,
  onClick,
  className,
}: ItemCardProps): React.ReactElement {
  const rarity     = normalizeRarity(item.itemRarity);
  const type       = normalizeType(item.itemType, item.weaponSubtype);
  const typeIcon   = TYPE_ICONS[type] ?? 'gem-pendant';
  const rarityCls  = RARITY_CLASS[rarity];
  const rarityName = rarityDisplayLabel(rarity);
  const typeLabel  = typeDisplayLabel(type);
  const imageUrl   = item.image?.mediaImage?.url ?? null;
  const linkPath   = to !== undefined ? to : (item.path ?? null);
  const description = detail ?? item.shortFlavour ?? typeLabel;
  const allClasses = `${rarityCls}${className ? ` ${className}` : ''}`;

  if (!detailed) {
    return (
      <Wrapper to={linkPath} onClick={onClick} className={`${styles.compact} ${allClasses}`}>
        <GameIcon name={typeIcon} size={20} color="currentColor" decorative className={styles.compactIcon} />
        <div className={styles.compactBody}>
          <span className={styles.compactName}>{item.title}</span>
          <span className={styles.compactDetail}>{description}</span>
        </div>
        <div className={styles.badges}>
          <Badge label={rarityName} variant={rarity} size="sm" />
          <Badge label={typeLabel} size="sm" />
        </div>
      </Wrapper>
    );
  }

  return (
    <Wrapper to={linkPath} onClick={onClick} className={`${styles.strip} ${allClasses}`}>
      <div className={styles.thumb}>
        {imageUrl ? (
          <img src={imageUrl} alt="" className={styles.thumbImg} />
        ) : (
          <GameIcon name={typeIcon} size={36} color="currentColor" decorative className={styles.thumbIcon} />
        )}
      </div>

      <div className={styles.body}>
        <div className={styles.nameRow}>
          <span className={styles.name}>{item.title}</span>
          {item.itemRequiresAttunement && (
            <span className={styles.attChip} title="Requires attunement" aria-label="Requires attunement">ATT</span>
          )}
        </div>
        <div className={styles.detail}>{description}</div>
      </div>

      <div className={styles.meta}>
        <Badge label={rarityName} variant={rarity} size="sm" />
        <span className={styles.typeLine}>
          <GameIcon name={typeIcon} size={11} color="currentColor" decorative />
          {typeLabel}
        </span>
      </div>
    </Wrapper>
  );
}

/* ──────────────────────────────────────────────────────────────────── */

interface WrapperProps {
  to:      string | null;
  onClick?: () => void;
  className: string;
  children: React.ReactNode;
}

function Wrapper({ to, onClick, className, children }: WrapperProps): React.ReactElement {
  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={`${className} ${styles.clickable}`}>
        {children}
      </button>
    );
  }
  if (to) {
    return (
      <Link to={to} className={`${className} ${styles.clickable}`}>
        {children}
      </Link>
    );
  }
  return <div className={className}>{children}</div>;
}
