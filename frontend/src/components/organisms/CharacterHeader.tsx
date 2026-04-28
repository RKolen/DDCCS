import React from 'react';
import { GameIcon } from '../atoms/GameIcon';
import { CharacterBadgeGroup } from '../molecules/CharacterBadgeGroup';
import type { GameIconName } from '../../types/icons';
import * as styles from './CharacterHeader.module.css';

interface CharacterHeaderProps {
  name: string;
  nickname?: string;
  background?: string;
  cls: string;
  subclass?: string;
  level: number;
  species: string;
  alignment?: string;
  hp: number;
  maxHp: number;
  ac: number;
  profBonus: number;
  speed: number;
}

const CLASS_ICONS: Record<string, GameIconName> = {
  Wizard:    'cowled',
  Ranger:    'crossed-swords',
  Rogue:     'hood',
  Fighter:   'knight-helmet',
  Paladin:   'knight-helmet',
  Cleric:    'holy-grail',
  Bard:      'scroll-unfurled',
  Druid:     'eye',
  Monk:      'muscle-up',
  Warlock:   'crystal-ball',
  Sorcerer:  'magic-swirl',
  Barbarian: 'broadsword',
};

const DEFAULT_CLASS_ICON: GameIconName = 'crossed-swords';

function resolveHpColor(hp: number, maxHp: number): string {
  const pct = maxHp > 0 ? hp / maxHp : 0;
  if (pct > 0.65) return 'var(--color-success)';
  if (pct > 0.35) return 'var(--color-warning)';
  return 'var(--color-danger)';
}

function resolveHpFilter(hp: number, maxHp: number): string {
  const pct = maxHp > 0 ? hp / maxHp : 0;
  if (pct > 0.65) return 'var(--filter-green)';
  if (pct > 0.35) return 'invert(70%) sepia(60%) saturate(700%) hue-rotate(350deg) brightness(95%)';
  return 'var(--filter-red)';
}

interface StatItemProps {
  icon: GameIconName;
  value: string;
  label: string;
  color: string;
  colorFilter: string;
}

function StatItem({ icon, value, label, color, colorFilter }: StatItemProps): React.ReactElement {
  return (
    <div className={styles.statItem}>
      <GameIcon name={icon} size={18} colorFilter={colorFilter} decorative />
      <span className={styles.statValue} style={{ color }}>{value}</span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  );
}

export function CharacterHeader({
  name,
  nickname,
  background,
  cls,
  subclass,
  level,
  species,
  alignment,
  hp,
  maxHp,
  ac,
  profBonus,
  speed,
}: CharacterHeaderProps): React.ReactElement {
  const classIcon = CLASS_ICONS[cls] ?? DEFAULT_CLASS_ICON;

  return (
    <div className={styles.header}>
      <div className={styles.identity}>
        <GameIcon
          name={classIcon}
          size={48}
          colorFilter="var(--filter-gold-dim)"
          decorative
          className={styles.classIcon}
        />
        <div className={styles.nameBlock}>
          <h1 className={styles.name}>{name}</h1>
          {(nickname ?? background) && (
            <p className={styles.subtitle}>
              {nickname && `"${nickname}"`}
              {nickname && background && ' · '}
              {background && `${background} Background`}
            </p>
          )}
          <CharacterBadgeGroup
            cls={cls}
            subclass={subclass}
            level={level}
            species={species}
            alignment={alignment}
            classIcon={classIcon}
          />
        </div>
      </div>

      <div className={styles.stats}>
        <StatItem
          icon="heart-beats"
          value={`${hp}/${maxHp}`}
          label="Hit Points"
          color={resolveHpColor(hp, maxHp)}
          colorFilter={resolveHpFilter(hp, maxHp)}
        />
        <StatItem
          icon="shield"
          value={String(ac)}
          label="Armor Class"
          color="var(--color-gold-mid)"
          colorFilter="var(--filter-gold)"
        />
        <StatItem
          icon="stars-stack"
          value={`+${profBonus}`}
          label="Prof Bonus"
          color="var(--color-gold-mid)"
          colorFilter="var(--filter-gold)"
        />
        <StatItem
          icon="run"
          value={`${speed}ft`}
          label="Speed"
          color="var(--color-text-secondary)"
          colorFilter="var(--filter-gold-dim)"
        />
      </div>
    </div>
  );
}
