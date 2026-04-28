import React from 'react';
import * as styles from './SearchTemplate.module.css';

interface SearchTemplateProps {
  searchBar: React.ReactNode;
  filters?: React.ReactNode;
  results: React.ReactNode;
  subtitle?: string;
}

export function SearchTemplate({
  searchBar,
  filters,
  results,
  subtitle = 'Semantic search powered by Milvus vector embeddings',
}: SearchTemplateProps): React.ReactElement {
  return (
    <div className={styles.page}>
      <h1>Lore Search</h1>
      <p className={styles.subtitle}>{subtitle}</p>
      <div className={styles.searchRow}>{searchBar}</div>
      {filters && <div className={styles.filters}>{filters}</div>}
      {results}
    </div>
  );
}
