import React from 'react';
import { StatValue } from '../atoms/StatValue';
import type { GameIconName } from '../../types/icons';

export type AbilityKey = 'STR' | 'DEX' | 'CON' | 'INT' | 'WIS' | 'CHA';

interface AbilityScoreProps {
  ability: AbilityKey;
  score: number;
  modifier: number;
}

const ABILITY_ICONS: Record<AbilityKey, GameIconName> = {
  STR: 'muscle-up',
  DEX: 'run',
  CON: 'heart-plus',
  INT: 'brain',
  WIS: 'eye',
  CHA: 'charm',
};

export function AbilityScore({ ability, score, modifier }: AbilityScoreProps): React.ReactElement {
  return (
    <StatValue
      score={score}
      modifier={modifier}
      label={ability}
      icon={ABILITY_ICONS[ability]}
    />
  );
}
