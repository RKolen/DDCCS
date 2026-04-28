import React from 'react';
import * as styles from './SkillRow.module.css';

interface SkillRowProps {
  name: string;
  modifier: number;
  proficient: boolean;
}

export function SkillRow({ name, modifier, proficient }: SkillRowProps): React.ReactElement {
  const modStr = modifier >= 0 ? `+${modifier}` : String(modifier);

  return (
    <div className={styles.row}>
      <span
        className={`${styles.pip} ${proficient ? styles.pipFilled : ''}`}
        role="img"
        aria-label={proficient ? 'proficient' : 'not proficient'}
      />
      <span className={styles.name}>{name}</span>
      <span className={styles.modifier}>{modStr}</span>
    </div>
  );
}
