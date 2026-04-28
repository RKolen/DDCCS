import React from 'react';
import { Badge } from '../atoms/Badge';
import { Divider } from '../atoms/Divider';
import { GameIcon } from '../atoms/GameIcon';
import * as styles from './NPCCard.module.css';

interface Relationship {
  name: string;
  description: string;
}

interface NPCCardProps {
  name: string;
  role: string;
  location?: string;
  alignment?: string;
  personality: string;
  relationships?: Relationship[];
}

export function NPCCard({
  name,
  role,
  location,
  alignment,
  personality,
  relationships,
}: NPCCardProps): React.ReactElement {
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.identity}>
          <GameIcon
            name="hood"
            size={24}
            colorFilter="var(--filter-gold-dim)"
            decorative
            className={styles.icon}
          />
          <div className={styles.nameBlock}>
            <span className={styles.name}>{name}</span>
            <span className={styles.role}>
              {role}{location ? ` · ${location}` : ''}
            </span>
          </div>
        </div>
        {alignment && (
          <div className={styles.badges}>
            <Badge label={alignment} variant="alignment" size="sm" />
          </div>
        )}
      </div>

      <Divider />

      <p className={styles.personality}>{personality}</p>

      {relationships && relationships.length > 0 && (
        <div className={styles.relationships}>
          {relationships.map(rel => (
            <span key={rel.name} className={styles.relationship}>
              <span className={styles.relName}>{rel.name}</span>
              <span className={styles.relDesc}>— {rel.description}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
