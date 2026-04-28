import React from 'react';
import * as styles from './SpellSlotPip.module.css';

export type PipState = 'available' | 'expended' | 'empty';

interface SpellSlotPipProps {
  state?: PipState;
  size?: number;
}

export function SpellSlotPip({
  state = 'empty',
  size = 12,
}: SpellSlotPipProps): React.ReactElement {
  const stateClass =
    state === 'available' ? styles.filled :
    state === 'expended'  ? styles.expended :
    '';

  const ariaLabel =
    state === 'available' ? 'spell slot available' :
    state === 'expended'  ? 'spell slot expended' :
    'no spell slot';

  return (
    <span
      className={`${styles.pip} ${stateClass}`}
      style={size !== 12 ? { width: size, height: size } : undefined}
      role="img"
      aria-label={ariaLabel}
    />
  );
}
