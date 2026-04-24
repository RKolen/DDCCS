import React from 'react';
import * as styles from './Badge.module.css';

interface BadgeProps {
  label: string;
}

export function Badge({ label }: BadgeProps): React.ReactElement {
  return <span className={styles.badge}>{label}</span>;
}
