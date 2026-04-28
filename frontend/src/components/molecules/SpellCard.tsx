import React from 'react';
import { Badge } from '../atoms/Badge';
import { GameIcon } from '../atoms/GameIcon';
import type { GameIconName } from '../../types/icons';
import * as styles from './SpellCard.module.css';

export type SpellSchool =
  | 'Abjuration'
  | 'Conjuration'
  | 'Divination'
  | 'Enchantment'
  | 'Evocation'
  | 'Illusion'
  | 'Necromancy'
  | 'Transmutation';

interface SpellCardProps {
  name: string;
  level: number;
  school: SpellSchool;
  concentration?: boolean;
  description?: string;
}

const SCHOOL_ICONS: Record<SpellSchool, GameIconName> = {
  Abjuration:    'shield',
  Conjuration:   'magic-swirl',
  Divination:    'crystal-ball',
  Enchantment:   'charm',
  Evocation:     'fire-spell-cast',
  Illusion:      'magic-swirl',
  Necromancy:    'skull',
  Transmutation: 'magic-swirl',
};

export function SpellCard({
  name,
  level,
  school,
  concentration = false,
  description,
}: SpellCardProps): React.ReactElement {
  const schoolIcon = SCHOOL_ICONS[school] ?? 'magic-swirl';
  const levelLabel = level === 0 ? 'Cantrip' : `Lv ${level}`;

  return (
    <div className={styles.card}>
      <GameIcon
        name={schoolIcon}
        size={18}
        colorFilter="var(--filter-blue)"
        decorative
        className={styles.icon}
      />
      <span className={styles.name}>{name}</span>
      <div className={styles.badges}>
        <Badge label={school} variant="school" size="sm" />
        <Badge label={levelLabel} size="sm" />
        {concentration && (
          <Badge label="Conc." variant="concentration" icon="concentration-orb" size="sm" />
        )}
      </div>
      {description && (
        <p className={styles.description}>{description}</p>
      )}
    </div>
  );
}
