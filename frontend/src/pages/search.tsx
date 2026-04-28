import React, { useState, useCallback } from 'react';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { SearchTemplate } from '../components/templates/SearchTemplate';
import { SearchBar } from '../components/organisms/SearchBar';
import { SearchResults } from '../components/organisms/SearchResults';
import { Select } from '../components/atoms/Input';
import type { SearchResponse } from '../types/search';

const CONTENT_TYPES = [
  { value: '',         label: 'All types' },
  { value: 'character',label: 'Characters' },
  { value: 'npc',      label: 'NPCs' },
  { value: 'spell',    label: 'Spells' },
  { value: 'item',     label: 'Items' },
  { value: 'feat',     label: 'Feats' },
  { value: 'monster',  label: 'Monsters' },
];

const SearchPage: React.FC<PageProps> = ({ location }) => {
  const [query,       setQuery]       = useState('');
  const [contentType, setContentType] = useState('');
  const [response,    setResponse]    = useState<SearchResponse | null>(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState<string | null>(null);

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

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
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
          error ? (
            <p style={{ color: 'var(--color-danger)', fontFamily: 'var(--font-body)', fontSize: 'var(--text-base)' }}>
              {error}
            </p>
          ) : response ? (
            <SearchResults results={response.results} query={response.query} />
          ) : null
        }
      />
    </BaseTemplate>
  );
};

export const Head: HeadFC = () => <title>Lore Search | D&D Consultant</title>;

export default SearchPage;
