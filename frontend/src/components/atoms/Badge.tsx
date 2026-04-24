import React from 'react';

interface BadgeProps {
  label: string;
}

export function Badge({ label }: BadgeProps): React.ReactElement {
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: '12px',
      fontSize: '11px',
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      background: '#3a2a1a',
      color: '#c9a96e',
      border: '1px solid #c9a96e55',
    }}>
      {label}
    </span>
  );
}
