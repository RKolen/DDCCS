import React, { useState, useCallback, useRef } from 'react';
import type { HeadFC } from 'gatsby';
import { Search, AlertTriangle } from 'lucide-react';
import { SearchResultItem } from '../components/molecules/SearchResultItem';
import { DiceIcon } from '../components/atoms/DiceIcon';
import { GameIcon } from '../components/atoms/GameIcon';
import type { DieType, GameIconName } from '../types/icons';
import type { SearchResponse } from '../types/search';
import * as styles from './search.module.css';

// Requests go through Gatsby's dev proxy (/api/* → Drupal).
// The search endpoint is public (_access: TRUE) — no credentials needed.
const SEARCH_BASE = '';

const CONTENT_TYPES = ['', 'character', 'npc', 'spell', 'item', 'feat', 'monster'];

const ALL_DICE: DieType[] = ['d4', 'd6', 'd8', 'd10', 'd12', 'd20'];

const ALL_GAME_ICONS: GameIconName[] = [
  'crossed-swords', 'broadsword', 'arrow-flights', 'shield', 'round-shield',
  'magic-swirl', 'fire-spell-cast', 'crystal-ball', 'shadow-follower', 'lightning-arc',
  'holy-symbol', 'book-cover', 'concentration-orb', 'muscle-up', 'run',
  'heart-plus', 'brain', 'eye', 'charm', 'cowled',
  'knight-helmet', 'hood', 'wolf-head', 'holy-grail', 'heart-beats',
  'skull', 'poison-bottle', 'burning-passion', 'frozen-orb', 'stars-stack',
  'swap-bag', 'gem-pendant', 'ring', 'scroll-unfurled', 'potion-ball',
];

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
    <main className={styles.page}>
      <h1 className={styles.heading}>Content Search JUST FOR TESTING PURPOSES</h1>

      <section className={styles.iconPreview}>
        <p className={styles.iconPreviewLabel}>Dice icons</p>
        <div className={styles.iconGrid}>
          {ALL_DICE.map(die => (
            <div key={die} className={styles.iconCell}>
              <DiceIcon die={die} size={32} />
              <span className={styles.iconName}>{die}</span>
            </div>
          ))}
        </div>
        <p className={styles.iconPreviewLabel}>Game icons</p>
        <div className={styles.iconGrid}>
          {ALL_GAME_ICONS.map(name => (
            <div key={name} className={styles.iconCell}>
              <GameIcon name={name} size={32} label={name} />
              <span className={styles.iconName}>{name}</span>
            </div>
          ))}
        </div>
      </section>

      <p className={styles.subtitle}>Semantic search powered by Milvus vector embeddings</p>

      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          ref={inputRef}
          className={styles.input}
          type="search"
          placeholder="Search characters, spells, items..."
          value={query}
          onChange={e => setQuery(e.target.value)}
          autoFocus
        />
        <select
          className={styles.select}
          value={contentType}
          onChange={e => setContentType(e.target.value)}
        >
          {CONTENT_TYPES.map(t => (
            <option key={t} value={t}>{t === '' ? 'All types' : t}</option>
          ))}
        </select>
        <button type="submit" className={styles.button} disabled={loading}>
          <Search size={14} aria-hidden />
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && (
        <p className={styles.error}>
          <AlertTriangle size={14} aria-hidden />
          {error}
        </p>
      )}

      {response && (
        <>
          <p className={styles.meta}>
            {response.count} result{response.count !== 1 ? 's' : ''} for &quot;{response.query}&quot;
          </p>
          {response.results.length > 0 ? (
            <ul className={styles.results}>
              {response.results.map(r => (
                <SearchResultItem key={r.id} result={r} />
              ))}
            </ul>
          ) : (
            <p className={styles.meta}>No results found.</p>
          )}
        </>
      )}
    </main>
  );
};

export const Head: HeadFC = () => <title>Content Search | D&D Consultant</title>;

export default SearchPage;
