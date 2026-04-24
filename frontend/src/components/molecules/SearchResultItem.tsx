import React from 'react';
import { Badge } from '../atoms/Badge';
import type { SearchResult } from '../../types/search';

interface SearchResultItemProps {
  result: SearchResult;
}

export function SearchResultItem({ result }: SearchResultItemProps): React.ReactElement {
  return (
    <li style={{
      padding: '12px 16px',
      borderBottom: '1px solid #2a1f14',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
    }}>
      <div style={{ flex: 1 }}>
        <span style={{ fontWeight: 600, color: '#e8d5b0' }}>{result.title}</span>
      </div>
      <Badge label={result.type} />
      <span style={{ fontSize: '12px', color: '#7a6a5a', minWidth: '60px', textAlign: 'right' }}>
        {(result.relevance * 100).toFixed(1)}% match
      </span>
    </li>
  );
}
