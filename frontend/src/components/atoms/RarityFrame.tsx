/**
 * RarityFrame — a gilded picture-frame around an item portrait.
 *
 * Wraps an <img> (or an empty slot) in a rarity-tinted glow plus a gold
 * inner liner and four corner brackets. Used by ItemSheet.
 * Size and corner radius are author-controlled.
 *
 * Pass `shape="circle"` to omit the brackets and make the inner liner
 * a circle instead of a rectangle.
 */

import * as React from 'react';
import type { ItemRarity } from '../../types/item';
import * as styles from './RarityFrame.module.css';

interface RarityFrameProps {
  rarity:       ItemRarity;
  imageUrl?:    string | null;
  placeholder?: string;
  size?:        number;
  radius?:      number;
  shape?:       'rect' | 'circle';
  alt?:         string;
  className?:   string;
}

const RARITY_VAR: Record<ItemRarity, string> = {
  common:      'var(--color-rarity-common)',
  uncommon:    'var(--color-rarity-uncommon)',
  rare:        'var(--color-rarity-rare)',
  'very-rare': 'var(--color-rarity-very-rare)',
  legendary:   'var(--color-rarity-legendary)',
  artifact:    'var(--color-rarity-artifact)',
  vestige:     'var(--color-rarity-vestige)',
};

/* Low-alpha rarity glow colours as 8-digit hex (per project colour rules). */
const RARITY_GLOW: Record<ItemRarity, string> = {
  common:      '#9e9e9e2e',
  uncommon:    '#5ec45e38',
  rare:        '#5ba8f542',
  'very-rare': '#bf7fe047',
  legendary:   '#ffa83057',
  artifact:    '#f060556b',
  vestige:     '#b58cf252',
};

export function RarityFrame({
  rarity,
  imageUrl,
  placeholder = 'No portrait',
  size = 320,
  radius = 4,
  shape = 'rect',
  alt,
  className,
}: RarityFrameProps): React.ReactElement {
  const glow = RARITY_GLOW[rarity];
  const outer: React.CSSProperties = {
    width: size,
    height: size,
    borderRadius: shape === 'circle' ? '50%' : radius + 4,
    borderColor: RARITY_VAR[rarity],
    boxShadow: `0 0 24px ${glow}, 0 6px 20px #00000099, inset 0 0 0 1px #00000066`,
    backgroundImage: `radial-gradient(circle at 30% 0%, ${glow}, transparent 60%), linear-gradient(135deg, var(--color-bg-overlay), var(--color-bg-surface))`,
  };
  const slotShape: React.CSSProperties = {
    borderRadius: shape === 'circle' ? '50%' : radius,
  };
  const liner: React.CSSProperties = {
    borderRadius: shape === 'circle' ? '50%' : radius + 1,
  };
  const bracketStyle: React.CSSProperties = {
    borderTopColor: RARITY_VAR[rarity],
    borderLeftColor: RARITY_VAR[rarity],
  };

  return (
    <div className={`${styles.frame}${className ? ` ${className}` : ''}`} style={outer}>
      <div className={styles.liner} style={liner} aria-hidden="true" />
      <div className={styles.slot} style={slotShape}>
        {imageUrl ? (
          <img src={imageUrl} alt={alt ?? ''} className={styles.img} />
        ) : (
          <span className={styles.placeholder}>{placeholder}</span>
        )}
      </div>
      {shape === 'rect' && (
        <>
          <span className={`${styles.bracket} ${styles.bracketTL}`} style={bracketStyle} aria-hidden="true" />
          <span className={`${styles.bracket} ${styles.bracketTR}`} style={bracketStyle} aria-hidden="true" />
          <span className={`${styles.bracket} ${styles.bracketBL}`} style={bracketStyle} aria-hidden="true" />
          <span className={`${styles.bracket} ${styles.bracketBR}`} style={bracketStyle} aria-hidden="true" />
        </>
      )}
    </div>
  );
}
