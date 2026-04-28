import React from 'react';
import { GameIcon } from './GameIcon';
import type { GameIconName } from '../../types/icons';
import * as styles from './Divider.module.css';

interface DividerProps {
  icon?: GameIconName;
  iconSize?: number;
}

export function Divider({ icon, iconSize = 14 }: DividerProps): React.ReactElement {
  if (icon) {
    return (
      <div className={styles.divider}>
        <div className={`${styles.line} ${styles.lineLeft}`} />
        <GameIcon
          name={icon}
          size={iconSize}
          colorFilter="var(--filter-gold-dim)"
          decorative
          className={styles.iconEl}
        />
        <div className={`${styles.line} ${styles.lineRight}`} />
      </div>
    );
  }

  return (
    <div className={styles.divider}>
      <div className={`${styles.line} ${styles.lineFull}`} />
    </div>
  );
}
