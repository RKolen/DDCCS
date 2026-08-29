/**
 * SpellSearchScreen — `spells/sp-search`.
 *
 * Looks up an official spell on the rules wiki via the sidecar, then
 * imports it as a Drupal spell node through /api/create-spell.
 */

import * as React from 'react';
import { graphql, useStaticQuery } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { Icon, Spinner } from '../atoms';
import { SpellSheet } from '../../molecules/SpellSheet';
import { type SpellRecord, levelLabel } from '../../../types/spell';
import { refreshAndReload } from '../../../utils/refreshContent';

interface VaultNode {
  id: string;
  title: string;
}

interface VaultQuery {
  drupal: { nodeSpells: { nodes: VaultNode[] } };
}

interface LookupSpell {
  name: string;
  level: number;
  school: string;
  casting_time: string;
  spell_range: string;
  components: string;
  duration: string;
  concentration: boolean;
  ritual: boolean;
  description: string;
}

interface LookupResponse {
  spell?: LookupSpell | null;
  error?: string;
}

interface CreateResult {
  id?: string;
  title?: string;
  error?: string;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function toRecord(data: LookupSpell): SpellRecord {
  const escaped = escapeHtml(data.description);
  const html = escaped === ''
    ? null
    : `<p>${escaped.replace(/\n\n/g, '</p><p>')}</p>`;
  return {
    id: data.name,
    title: data.name,
    path: null,
    spellLevel: data.level,
    school: data.school === '' ? null : data.school,
    castingTime: data.casting_time === '' ? null : data.casting_time,
    spellRange: data.spell_range === '' ? null : data.spell_range,
    spellComponents: data.components === '' ? null : data.components,
    spellDuration: data.duration === '' ? null : data.duration,
    concentration: data.concentration,
    ritual: data.ritual,
    descriptionHtml: html,
  };
}

export function SpellSearchScreen(_props: ScreenProps): React.ReactElement {
  const vault = useStaticQuery<VaultQuery>(graphql`
    query ConsoleSpellVaultTitles {
      drupal {
        nodeSpells(first: 100) {
          nodes { id title }
        }
      }
    }
  `);
  const known = React.useMemo(() => {
    const titles = new Set<string>();
    (vault?.drupal?.nodeSpells?.nodes ?? []).forEach(node => {
      titles.add(node.title.toLowerCase());
    });
    return titles;
  }, [vault]);

  const [query, setQuery] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [importing, setImporting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [found, setFound] = React.useState<LookupSpell | null>(null);
  const [imported, setImported] = React.useState<string | null>(null);

  const alreadyInVault = found != null && known.has(found.name.toLowerCase());

  const lookup = async (event: React.FormEvent): Promise<void> => {
    event.preventDefault();
    const name = query.trim();
    if (name === '') {
      setError('Enter a spell name.');
      return;
    }
    setLoading(true);
    setError(null);
    setFound(null);
    setImported(null);
    try {
      const res = await fetch('/api/lookup-spell', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      const payload = (await res.json()) as LookupResponse;
      if (!res.ok || payload.error != null) {
        throw new Error(payload.error ?? `Request failed (${res.status})`);
      }
      if (payload.spell == null) {
        setError(`No wiki page for "${name}".`);
        return;
      }
      setFound(payload.spell);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  const importSpell = async (): Promise<void> => {
    if (found == null) return;
    setImporting(true);
    setError(null);
    try {
      const res = await fetch('/api/create-spell', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: found.name,
          level: found.level,
          school: found.school || null,
          castingTime: found.casting_time || null,
          spellRange: found.spell_range || null,
          components: found.components || null,
          duration: found.duration || null,
          concentration: found.concentration,
          ritual: found.ritual,
          description: found.description || null,
        }),
      });
      const payload = (await res.json()) as CreateResult;
      if (!res.ok || payload.error != null) {
        throw new Error(payload.error ?? `Request failed (${res.status})`);
      }
      setImported(payload.title ?? found.name);
      void refreshAndReload();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="screen-generic">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Spells</span>
          <h2>Search Rules Wiki</h2>
          <p className="screen-blurb">
            Look up an official spell by name, then import it into the vault.
          </p>
        </div>
      </header>

      <form onSubmit={event => { void lookup(event); }} style={{ display: 'flex', gap: 8, maxWidth: 480, marginBottom: 20 }}>
        <div className="search-field" style={{ flex: 1 }}>
          <Icon name="search" size={13} />
          <input
            type="text"
            placeholder="Fireball"
            value={query}
            onChange={event => setQuery(event.target.value)}
          />
        </div>
        <button type="submit" className="primary-btn" disabled={loading}>
          {loading ? <Spinner /> : <Icon name="sparkle" size={11} />}
          {loading ? 'Looking up' : 'Look up'}
        </button>
      </form>

      {error != null && (
        <p style={{ fontFamily: 'var(--font-body)', color: 'var(--color-danger)' }}>{error}</p>
      )}

      {found != null && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span className="reader-eyebrow">
              {levelLabel(found.level)}
              {alreadyInVault ? ' · already in vault' : ' · not in vault'}
            </span>
            <button
              type="button"
              className="primary-btn"
              disabled={importing || alreadyInVault || imported != null}
              onClick={() => { void importSpell(); }}
            >
              {importing ? <Spinner /> : <Icon name="plus" size={11} />}
              {alreadyInVault || imported != null ? 'In vault' : 'Import'}
            </button>
          </div>
          {imported != null && (
            <p style={{ fontFamily: 'var(--font-body)', color: 'var(--color-success)' }}>
              Imported {imported}. Refreshing the compendium...
            </p>
          )}
          <SpellSheet spell={toRecord(found)} />
        </div>
      )}
    </div>
  );
}
