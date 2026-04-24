import React from 'react';
import type { DieType } from '../../types/icons';
import * as styles from './DiceIcon.module.css';

interface DiceIconProps {
  die: DieType;
  size?: number;
  colorFilter?: string;
  decorative?: boolean;
  className?: string;
}

export function DiceIcon({
  die,
  size = 20,
  colorFilter,
  decorative = false,
  className,
}: DiceIconProps): React.ReactElement {
  const ariaProps = decorative ? { alt: '' } : { alt: `${die} die` };

  return (
    <img
      src={`/icons/game/dice-${die}.svg`}
      width={size}
      height={size}
      className={`${styles.icon}${className ? ` ${className}` : ''}`}
      style={colorFilter ? { filter: colorFilter } : undefined}
      {...ariaProps}
    />
  );
}
