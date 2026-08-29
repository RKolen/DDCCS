import React from 'react';
import { Badge } from '../atoms/Badge';
import { GameIcon } from '../atoms/GameIcon';
import type { GameIconName } from '../../types/icons';
import { type SpellSchoolName, SPELL_SCHOOLS, levelLabel } from '../../types/spell';
import * as styles from './SpellCard.module.css';

export type SpellSchool = SpellSchoolName;

interface SpellCardProps {
  name: string;
  level: number;
  school?: string | null;
  concentration?: boolean;
  ritual?: boolean;
  description?: string;
  onClick?: () => void;
}

const SCHOOL_ICONS: Record<SpellSchoolName, GameIconName> = {
  Abjuration:    'shield',
  Conjuration:   'magic-swirl',
  Divination:    'crystal-ball',
  Enchantment:   'charm',
  Evocation:     'fire-spell-cast',
  Illusion:      'magic-swirl',
  Necromancy:    'skull',
  Transmutation: 'magic-swirl',
};

function isSchool(value: string): value is SpellSchoolName {
  return (SPELL_SCHOOLS as readonly string[]).includes(value);
}

export function SpellCard({
  name,
  level,
  school = null,
  concentration = false,
  ritual = false,
  description,
  onClick,
}: SpellCardProps): React.ReactElement {
  const iconName = school != null && isSchool(school)
    ? SCHOOL_ICONS[school]
    : 'magic-swirl';
  const className = onClick == null ? styles.card : `${styles.card} ${styles.clickable}`;
  const inner = (
    <>
      <GameIcon
        name={iconName}
        size={18}
        colorFilter="var(--filter-gold-bright)"
        decorative
        className={styles.icon}
      />
      <span className={styles.name}>{name}</span>
      <div className={styles.badges}>
        {school != null && school !== '' && (
          <Badge label={school} variant="school" size="sm" />
        )}
        <Badge label={levelLabel(level)} size="sm" />
        {concentration && (
          <Badge label="Conc." variant="concentration" icon="concentration-orb" size="sm" />
        )}
        {ritual && (
          <Badge label="Ritual" size="sm" />
        )}
      </div>
      {description != null && description !== '' && (
        <p className={styles.description}>{description}</p>
      )}
    </>
  );

  if (onClick != null) {
    return (
      <button type="button" className={className} onClick={onClick}>
        {inner}
      </button>
    );
  }
  return <div className={className}>{inner}</div>;
}
