import React from 'react';
import { Badge } from '../atoms/Badge';
import type { BadgeVariant } from '../atoms/Badge';
import { GameIcon } from '../atoms/GameIcon';
import type { GameIconName } from '../../types/icons';
import * as styles from './ItemCard.module.css';

export type ItemRarity =
  | 'common'
  | 'uncommon'
  | 'rare'
  | 'very-rare'
  | 'legendary'
  | 'artifact';

export type ItemType =
  | 'Melee Weapon'
  | 'Ranged Weapon'
  | 'Armor'
  | 'Ring'
  | 'Staff'
  | 'Wondrous';

interface ItemCardProps {
  name: string;
  rarity: ItemRarity;
  type: ItemType;
  detail: string;
}

const TYPE_ICONS: Record<ItemType, GameIconName> = {
  'Melee Weapon':  'broadsword',
  'Ranged Weapon': 'arrow-flights',
  Armor:           'round-shield',
  Ring:            'ring',
  Staff:           'magic-swirl',
  Wondrous:        'gem-pendant',
};

const RARITY_VARIANTS: Record<ItemRarity, BadgeVariant> = {
  common:    'common',
  uncommon:  'uncommon',
  rare:      'rare',
  'very-rare': 'very-rare',
  legendary: 'legendary',
  artifact:  'artifact',
};

export function ItemCard({ name, rarity, type, detail }: ItemCardProps): React.ReactElement {
  const typeIcon = TYPE_ICONS[type] ?? 'gem-pendant';
  const rarityLabel = rarity.replace('-', ' ');

  return (
    <div className={styles.card}>
      <GameIcon
        name={typeIcon}
        size={20}
        colorFilter="var(--filter-gold-dim)"
        decorative
        className={styles.icon}
      />
      <div className={styles.body}>
        <span className={styles.name}>{name}</span>
        <span className={styles.detail}>{detail}</span>
      </div>
      <div className={styles.badges}>
        <Badge label={rarityLabel} variant={RARITY_VARIANTS[rarity]} size="sm" />
        <Badge label={type} size="sm" />
      </div>
    </div>
  );
}
