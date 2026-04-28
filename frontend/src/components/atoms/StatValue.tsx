import React from 'react';
import { GameIcon } from './GameIcon';
import type { GameIconName } from '../../types/icons';
import * as styles from './StatValue.module.css';

interface StatValueProps {
  score: number;
  modifier: number;
  label: string;
  icon?: GameIconName;
}

export function StatValue({ score, modifier, label, icon }: StatValueProps): React.ReactElement {
  const modClass =
    modifier > 0 ? styles.modPositive :
    modifier < 0 ? styles.modNegative :
    styles.modZero;

  const modStr = modifier >= 0 ? `+${modifier}` : String(modifier);

  return (
    <div className={styles.block}>
      {icon && (
        <GameIcon
          name={icon}
          size={16}
          colorFilter="var(--filter-gold-dim)"
          decorative
          className={styles.icon}
        />
      )}
      <span className={styles.label}>{label}</span>
      <span className={styles.score}>{score}</span>
      <span className={`${styles.modifier} ${modClass}`}>{modStr}</span>
    </div>
  );
}
