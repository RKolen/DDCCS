import React from 'react';
import { AbilityScore } from '../molecules/AbilityScore';
import type { AbilityKey } from '../molecules/AbilityScore';
import * as styles from './AbilityScoreGrid.module.css';

type AbilityMap = Record<AbilityKey, number>;

interface AbilityScoreGridProps {
  scores: AbilityMap;
  modifiers: AbilityMap;
}

const ABILITY_ORDER: AbilityKey[] = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'];

export function AbilityScoreGrid({ scores, modifiers }: AbilityScoreGridProps): React.ReactElement {
  return (
    <div className={styles.grid}>
      {ABILITY_ORDER.map(ability => (
        <AbilityScore
          key={ability}
          ability={ability}
          score={scores[ability]}
          modifier={modifiers[ability]}
        />
      ))}
    </div>
  );
}
