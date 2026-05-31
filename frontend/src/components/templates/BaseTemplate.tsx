import React from 'react';

interface BaseTemplateProps {
  currentPath?: string;
  campaignTitle?: string;
  children: React.ReactNode;
}

export function BaseTemplate({ children }: BaseTemplateProps): React.ReactElement {
  return (
    <main style={{ flex: 1, overflowY: 'auto', background: 'var(--color-bg-base)' }}>
      {children}
    </main>
  );
}
