import React from 'react';
import { GameIcon } from './GameIcon';
import type { GameIconName } from '../../types/icons';
import * as styles from './Badge.module.css';

export type BadgeVariant =
  | 'default'
  | 'class'
  | 'school'
  | 'common'
  | 'uncommon'
  | 'rare'
  | 'very-rare'
  | 'legendary'
  | 'artifact'
  | 'danger'
  | 'success'
  | 'concentration'
  | 'alignment';

export type BadgeSize = 'sm' | 'md';

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  size?: BadgeSize;
  icon?: GameIconName;
}

const VARIANT_CLASS: Record<BadgeVariant, string> = {
  default:       styles.varDefault,
  class:         styles.varClass,
  school:        styles.varSchool,
  common:        styles.varCommon,
  uncommon:      styles.varUncommon,
  rare:          styles.varRare,
  'very-rare':   styles.varVeryRare,
  legendary:     styles.varLegendary,
  artifact:      styles.varArtifact,
  danger:        styles.varDanger,
  success:       styles.varSuccess,
  concentration: styles.varConcentration,
  alignment:     styles.varAlignment,
};

export function Badge({
  label,
  variant = 'default',
  size = 'md',
  icon,
}: BadgeProps): React.ReactElement {
  const variantClass = VARIANT_CLASS[variant] ?? styles.varDefault;
  const sizeClass = size === 'sm' ? styles.sizeSm : styles.sizeMd;
  const iconSize = size === 'sm' ? 10 : 12;

  return (
    <span className={`${styles.badge} ${variantClass} ${sizeClass}`}>
      {icon && <GameIcon name={icon} size={iconSize} decorative />}
      {label}
    </span>
  );
}
