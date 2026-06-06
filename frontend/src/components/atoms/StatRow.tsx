import * as React from 'react';
import * as styles from './StatRow.module.css';

interface StatRowProps {
  label: string;
  value: string;
  unit?: string;
}

export function StatRow({ label, value, unit }: StatRowProps): React.ReactElement {
  return (
    <div className={styles.row}>
      <span className={styles.label}>{label}</span>
      <span className={styles.right}>
        <span className={styles.value}>{value}</span>
        {unit && <span className={styles.unit}>{unit}</span>}
      </span>
    </div>
  );
}
