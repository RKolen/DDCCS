/**
 * Portrait — character portrait atom.
 *
 * Shows an actual image when one is available, otherwise falls back to a
 * dark-fantasy colour block: deterministic background, large initials, and
 * a faint species/class icon watermark.
 *
 * Used by the characters page and character sheets.
 */

import * as React from 'react';
import { GameIcon } from './GameIcon';
import type { GameIconName } from '../../types/icons';
import * as styles from './Portrait.module.css';

/* ── Species → watermark icon ─────────────────────────────────────────────── */

const SPECIES_ICON: Partial<Record<string, GameIconName>> = {
  human:           'muscle-up',
  elf:             'eye',
  'wood elf':      'eye',
  'high elf':      'eye',
  'dark elf':      'eye',
  halfling:        'run',
  dwarf:           'shield',
  'hill dwarf':    'shield',
  'mountain dwarf':'shield',
  dragonborn:      'fire-spell-cast',
  gnome:           'brain',
  'forest gnome':  'brain',
  'rock gnome':    'brain',
  'half-orc':      'skull',
  tiefling:        'skull',
  aasimar:         'stars-stack',
  'half-elf':      'magic-swirl',
};

function speciesIcon(species: string | null | undefined): GameIconName {
  if (!species) return 'crossed-swords';
  return SPECIES_ICON[species.toLowerCase()] ?? 'crossed-swords';
}

/* ── Background colour from name hash ────────────────────────────────────── */

const BG_PALETTE = [
  '#3a2818',  // warm brown
  '#182838',  // deep teal-blue
  '#181e38',  // indigo-dark
  '#261838',  // purple-dark
  '#1a2618',  // forest-dark
];

function bgColor(name: string): string {
  let h = 0;
  for (let i = 0; i < name.length; i++) {
    h = Math.imul(31, h) + name.charCodeAt(i);
  }
  return BG_PALETTE[Math.abs(h) % BG_PALETTE.length];
}

/* ── Component ────────────────────────────────────────────────────────────── */

export interface PortraitProps {
  name:      string;
  size?:     number;
  imageUrl?: string | null;
  species?:  string | null;
  className?: string;
}

export function Portrait({
  name,
  size = 56,
  imageUrl,
  species,
  className,
}: PortraitProps): React.ReactElement {
  const initials = name
    .split(' ')
    .map(w => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  const iconName = speciesIcon(species);

  const outer: React.CSSProperties = {
    width:  size,
    height: size,
    background: imageUrl ? undefined : bgColor(name),
    fontSize: Math.round(size * 0.33),
  };

  return (
    <div
      className={`${styles.portrait}${className ? ` ${className}` : ''}`}
      style={outer}
      aria-hidden="true"
    >
      {imageUrl ? (
        <img src={imageUrl} alt={name} className={styles.img} />
      ) : (
        <>
          <span className={styles.watermark}>
            <GameIcon
              name={iconName}
              size={Math.round(size * 0.72)}
              color="currentColor"
              decorative
            />
          </span>
          <span className={styles.initials}>{initials}</span>
        </>
      )}
    </div>
  );
}
