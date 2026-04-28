import React from 'react';
import { SpellSlotPip } from '../atoms/SpellSlotPip';
import type { PipState } from '../atoms/SpellSlotPip';
import * as styles from './SpellSlotRow.module.css';

interface SpellSlotRowProps {
  level: string;
  total: number;
  available: number;
}

export function SpellSlotRow({ level, total, available }: SpellSlotRowProps): React.ReactElement {
  return (
    <div className={styles.row}>
      <span className={styles.level}>{level}</span>
      <div className={styles.pips}>
        {Array.from({ length: total }).map((_, i) => {
          const state: PipState = i < available ? 'available' : 'expended';
          return <SpellSlotPip key={i} state={state} />;
        })}
      </div>
      <span className={styles.count}>{available}/{total}</span>
    </div>
  );
}
