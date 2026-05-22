import React, { useState, useCallback } from 'react';
import { navigate } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { SearchTemplate } from '../components/templates/SearchTemplate';
import { SearchBar } from '../components/organisms/SearchBar';
import { SearchResults } from '../components/organisms/SearchResults';
import { Select } from '../components/atoms/Input';
import type { SearchDecomposition, SearchResponse } from '../types/search';

const CONTENT_TYPES = [
  { value: '', label: 'All types' },
  { value: 'character', label: 'Characters' },
  { value: 'spell', label: 'Spells' },
  { value: 'item', label: 'Items' },
  { value: 'monster', label: 'Monsters' },
];

interface DecompositionPanelProps {
  decomposition: SearchDecomposition;
}

function DecompositionPanel({ decomposition }: DecompositionPanelProps): React.ReactElement {
  const [open, setOpen] = useState(false);

  const activeFilters = [
    ...decomposition.filters.equipment.map(v => `equipment = ${v}`),
    ...decomposition.filters.species.map(v => `species = ${v}`),
    ...decomposition.filters.class.map(v => `class = ${v}`),
    ...decomposition.filters.campaign.map(v => `campaign = ${v}`),
  ];

  return (
    <details
      open={open}
      onToggle={e => setOpen((e.currentTarget as HTMLDetailsElement).open)}
      style={{
        marginTop: 'var(--space-3)',
        fontSize: 'var(--text-sm)',
        color: 'var(--color-text-muted)',
        fontFamily: 'var(--font-ui)',
        borderTop: '1px solid var(--color-border)',
        paddingTop: 'var(--space-2)',
      }}
    >
      <summary style={{ cursor: 'pointer', userSelect: 'none' }}>
        {open ? 'Hide' : 'Show'} query breakdown
      </summary>
      <div style={{ marginTop: 'var(--space-2)', display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
        <span>
          <strong>Backends:</strong>{' '}
          {decomposition.backends.join(', ') || '—'}
        </span>
        {decomposition.entity_types.length > 0 && (
          <span>
            <strong>Type filter:</strong>{' '}
            {decomposition.entity_types.join(', ')}
          </span>
        )}
        {activeFilters.length > 0 && (
          <span>
            <strong>Filters:</strong>{' '}
            {activeFilters.join('  |  ')}
          </span>
        )}
        {decomposition.semantic_query !== '' && (
          <span>
            <strong>Semantic query:</strong>{' '}
            &ldquo;{decomposition.semantic_query}&rdquo;
          </span>
        )}
        {decomposition.keyword_query !== '' && (
          <span>
            <strong>Keyword query:</strong>{' '}
            &ldquo;{decomposition.keyword_query}&rdquo;
          </span>
        )}
        {decomposition.timings && (
          <span>
            <strong>Timings:</strong>{' '}
            {[
              `total: ${decomposition.timings.total_ms}ms`,
              `decompose: ${decomposition.timings.decompose_ms}ms`,
              ...(decomposition.timings.entity_query_ms !== null
                ? [`entity query: ${decomposition.timings.entity_query_ms}ms`]
                : []),
              ...(decomposition.timings.solr_ms !== null
                ? [`solr: ${decomposition.timings.solr_ms}ms`]
                : []),
              ...(decomposition.timings.milvus_ms !== null
                ? [`milvus: ${decomposition.timings.milvus_ms}ms`]
                : []),
            ].join('  |  ')}
          </span>
        )}
      </div>
    </details>
  );
}

const SearchPage: React.FC<PageProps> = ({ location }) => {
  const initialQuery = new URLSearchParams(location.search).get('q') ?? '';
  const [query, setQuery] = useState(initialQuery);
  const [contentType, setContentType] = useState('');
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSearch = useCallback(async (q: string, type: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams({ q: q.trim(), limit: '20' });
    if (type) params.set('type', type);

    try {
      const res = await fetch(
        `/api/content-search?${params.toString()}`,
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

  /* Auto-run once on mount when arriving from the topbar with ?q=.
     Deferred one tick so the page finishes rendering before the fetch fires. */
  const didAutoSearch = React.useRef(false);
  React.useEffect(() => {
    if (!didAutoSearch.current && initialQuery) {
      didAutoSearch.current = true;
      const id = setTimeout(() => { void runSearch(initialQuery, ''); }, 0);
      return () => clearTimeout(id);
    }
    return undefined;
  }, [initialQuery, runSearch]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!query.trim()) return;
    /* Update the URL so it's shareable and reflects the current search */
    void navigate(`/search/?q=${encodeURIComponent(query.trim())}`, { replace: true });
    void runSearch(query, contentType);
  };

  return (
    <BaseTemplate currentPath={location.pathname}>
      <SearchTemplate
        searchBar={
          <SearchBar
            value={query}
            onChange={e => setQuery(e.target.value)}
            onSubmit={handleSubmit}
            loading={loading}
          />
        }
        filters={
          <Select
            id="content-type"
            label="Content type"
            value={contentType}
            onChange={e => setContentType(e.target.value)}
            options={CONTENT_TYPES}
          />
        }
        results={
          loading ? (
            <p style={{
              fontFamily: 'var(--font-body)',
              fontStyle: 'italic',
              color: 'var(--color-text-secondary)',
              fontSize: 'var(--text-base)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}>
              <span style={{
                display: 'inline-block',
                width: '1em',
                height: '1em',
                border: '2px solid var(--color-gold-muted)',
                borderTopColor: 'var(--color-gold-bright)',
                borderRadius: '50%',
                animation: 'spin 0.7s linear infinite',
              }} />
              Searching...
            </p>
          ) : error ? (
            <p style={{ color: 'var(--color-danger)', fontFamily: 'var(--font-body)', fontSize: 'var(--text-base)' }}>
              {error}
            </p>
          ) : response ? (
            <>
              {response.decomposition && (
                <DecompositionPanel decomposition={response.decomposition} />
              )}
              <SearchResults results={response.results} query={response.query} />
            </>
          ) : null
        }
      />
    </BaseTemplate>
  );
};

export const Head: HeadFC = () => <title>Lore Search | D&D Consultant</title>;

export default SearchPage;
