import React from 'react';
import { Badge } from '../atoms/Badge';
import type { GameIconName } from '../../types/icons';
import * as styles from './CharacterBadgeGroup.module.css';

interface CharacterBadgeGroupProps {
  cls: string;
  subclass?: string;
  level: number;
  species: string;
  alignment?: string;
  classIcon?: GameIconName;
  size?: 'sm' | 'md';
}

export function CharacterBadgeGroup({
  cls,
  subclass,
  level,
  species,
  alignment,
  classIcon,
  size = 'md',
}: CharacterBadgeGroupProps): React.ReactElement {
  const classLabel = subclass ? `${cls} — ${subclass}` : cls;

  return (
    <div className={styles.group}>
      <Badge
        label={classLabel}
        variant="class"
        icon={classIcon}
        size={size}
      />
      <Badge label={`Level ${level}`} size={size} />
      <Badge label={species} size={size} />
      {alignment && <Badge label={alignment} variant="alignment" size={size} />}
    </div>
  );
}
