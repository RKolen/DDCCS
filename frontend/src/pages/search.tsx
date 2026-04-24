import React, { useState, useCallback, useRef } from 'react';
import type { HeadFC } from 'gatsby';
import { SearchResultItem } from '../components/molecules/SearchResultItem';
import type { SearchResponse } from '../types/search';

// Requests go through Gatsby's dev proxy (/api/* → Drupal).
// The search endpoint is public (_access: TRUE) — no credentials needed.
const SEARCH_BASE = '';

const CONTENT_TYPES = ['', 'character', 'npc', 'spell', 'item', 'feat', 'monster'];

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    background: '#1a1008',
    color: '#e8d5b0',
    fontFamily: "'Georgia', serif",
    padding: '40px 24px',
  },
  heading: {
    fontSize: '28px',
    marginBottom: '8px',
    color: '#c9a96e',
    letterSpacing: '0.03em',
  },
  subtitle: {
    fontSize: '14px',
    color: '#7a6a5a',
    marginBottom: '32px',
  },
  form: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
    flexWrap: 'wrap' as const,
  },
  input: {
    flex: 1,
    minWidth: '200px',
    padding: '10px 14px',
    background: '#2a1f14',
    border: '1px solid #c9a96e55',
    borderRadius: '4px',
    color: '#e8d5b0',
    fontSize: '15px',
    outline: 'none',
  },
  select: {
    padding: '10px 12px',
    background: '#2a1f14',
    border: '1px solid #c9a96e55',
    borderRadius: '4px',
    color: '#e8d5b0',
    fontSize: '14px',
  },
  button: {
    padding: '10px 20px',
    background: '#c9a96e',
    color: '#1a1008',
    border: 'none',
    borderRadius: '4px',
    fontWeight: 700,
    fontSize: '14px',
    cursor: 'pointer',
    letterSpacing: '0.05em',
  },
  results: {
    background: '#221508',
    border: '1px solid #2a1f14',
    borderRadius: '6px',
    listStyle: 'none',
    margin: 0,
    padding: 0,
    overflow: 'hidden',
  },
  meta: {
    fontSize: '13px',
    color: '#7a6a5a',
    marginBottom: '12px',
  },
  error: {
    color: '#c0392b',
    padding: '12px',
    background: '#2a1008',
    borderRadius: '4px',
    fontSize: '14px',
  },
};

const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [contentType, setContentType] = useState('');
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const runSearch = useCallback(async (q: string, type: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams({ q: q.trim(), limit: '20' });
    if (type) params.set('type', type);

    try {
      const res = await fetch(
        `${SEARCH_BASE}/api/content-search?${params.toString()}`,
        { headers: { Accept: 'application/json' } },
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: SearchResponse = await res.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void runSearch(query, contentType);
  };

  return (
    <main style={styles.page}>
      <h1 style={styles.heading}>Content Search JUST FOR TESTING PURPOSES</h1>
      <p style={styles.subtitle}>Semantic search powered by Milvus vector embeddings</p>

      <form onSubmit={handleSubmit} style={styles.form}>
        <input
          ref={inputRef}
          style={styles.input}
          type="search"
          placeholder="Search characters, spells, items..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          autoFocus
        />
        <select
          style={styles.select}
          value={contentType}
          onChange={e => setContentType(e.target.value)}
        >
          {CONTENT_TYPES.map(t => (
            <option key={t} value={t}>{t === '' ? 'All types' : t}</option>
          ))}
        </select>
        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <p style={styles.error}>{error}</p>}

      {response && (
        <>
          <p style={styles.meta}>
            {response.count} result{response.count !== 1 ? 's' : ''} for &quot;{response.query}&quot;
          </p>
          {response.results.length > 0 ? (
            <ul style={styles.results}>
              {response.results.map(r => (
                <SearchResultItem key={r.id} result={r} />
              ))}
            </ul>
          ) : (
            <p style={styles.meta}>No results found.</p>
          )}
        </>
      )}
    </main>
  );
};

export const Head: HeadFC = () => <title>Content Search | D&D Consultant</title>;

export default SearchPage;
