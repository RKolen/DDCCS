import React from 'react';
import { SearchResultItem } from '../molecules/SearchResultItem';
import type { SearchResult } from '../../types/search';
import * as styles from './SearchResults.module.css';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
}

export function SearchResults({ results, query }: SearchResultsProps): React.ReactElement {
  if (results.length === 0) {
    return (
      <p className={styles.empty}>No results for &ldquo;{query}&rdquo;</p>
    );
  }

  return (
    <div>
      <p className={styles.count}>
        {results.length} result{results.length !== 1 ? 's' : ''} for &ldquo;{query}&rdquo;
      </p>
      <ul className={styles.list}>
        {results.map(result => (
          <SearchResultItem key={result.id} result={result} />
        ))}
      </ul>
    </div>
  );
}
