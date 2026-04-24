import React from 'react';
import type { GameIconName } from '../../types/icons';
import * as styles from './GameIcon.module.css';

export type { GameIconName };

interface GameIconProps {
  name: GameIconName;
  size?: number;
  colorFilter?: string;
  label?: string;
  decorative?: boolean;
  className?: string;
}

export function GameIcon({
  name,
  size = 20,
  colorFilter,
  label,
  decorative = false,
  className,
}: GameIconProps): React.ReactElement {
  const ariaProps = decorative ? { alt: '' } : { alt: label ?? name };

  return (
    <img
      src={`/icons/game/${name}.svg`}
      width={size}
      height={size}
      className={`${styles.icon}${className ? ` ${className}` : ''}`}
      style={colorFilter ? { filter: colorFilter } : undefined}
      {...ariaProps}
    />
  );
}
