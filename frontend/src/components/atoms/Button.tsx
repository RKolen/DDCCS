import React from 'react';
import { GameIcon } from './GameIcon';
import type { GameIconName } from '../../types/icons';
import * as styles from './Button.module.css';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  children: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: GameIconName;
  iconPosition?: 'left' | 'right';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

const ICON_SIZE: Record<ButtonSize, number> = { sm: 12, md: 14, lg: 16 };

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary:   styles.varPrimary,
  secondary: styles.varSecondary,
  ghost:     styles.varGhost,
  danger:    styles.varDanger,
};

const SIZE_CLASS: Record<ButtonSize, string> = {
  sm: styles.sizeSm,
  md: styles.sizeMd,
  lg: styles.sizeLg,
};

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  disabled = false,
  loading = false,
  onClick,
  type = 'button',
  className,
}: ButtonProps): React.ReactElement {
  const cls = [
    styles.btn,
    VARIANT_CLASS[variant],
    SIZE_CLASS[size],
    className,
  ].filter(Boolean).join(' ');

  const iconEl = icon && !loading
    ? <GameIcon name={icon} size={ICON_SIZE[size]} decorative />
    : null;

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={cls}
    >
      {loading && <span className={styles.spinner} aria-hidden="true" />}
      {!loading && iconPosition === 'left' && iconEl}
      {children}
      {!loading && iconPosition === 'right' && iconEl}
    </button>
  );
}
