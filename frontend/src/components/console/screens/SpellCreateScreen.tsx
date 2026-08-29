/**
 * SpellCreateScreen — `spells/sp-create`.
 *
 * Homebrew form that writes a Drupal spell node through /api/create-spell.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon, Spinner } from '../atoms';
import { SPELL_SCHOOLS } from '../../../types/spell';
import { refreshAndReload } from '../../../utils/refreshContent';

interface CreateSpellResult {
  id?: string;
  title?: string;
  path?: string | null;
  error?: string;
}

const LEVELS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];

export function SpellCreateScreen(_props: ScreenProps): React.ReactElement {
  const [title, setTitle] = React.useState('');
  const [level, setLevel] = React.useState(0);
  const [school, setSchool] = React.useState('');
  const [castingTime, setCastingTime] = React.useState('1 action');
  const [spellRange, setSpellRange] = React.useState('60 feet');
  const [components, setComponents] = React.useState('V, S');
  const [duration, setDuration] = React.useState('Instantaneous');
  const [concentration, setConcentration] = React.useState(false);
  const [ritual, setRitual] = React.useState(false);
  const [description, setDescription] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [savedTitle, setSavedTitle] = React.useState<string | null>(null);

  const submit = async (event: React.FormEvent): Promise<void> => {
    event.preventDefault();
    const name = title.trim();
    if (name === '') {
      setError('A spell name is required.');
      return;
    }
    setSaving(true);
    setError(null);
    setSavedTitle(null);
    try {
      const res = await fetch('/api/create-spell', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: name,
          level,
          school: school.trim() || null,
          castingTime: castingTime.trim() || null,
          spellRange: spellRange.trim() || null,
          components: components.trim() || null,
          duration: duration.trim() || null,
          concentration,
          ritual,
          description: description.trim() || null,
        }),
      });
      const payload = (await res.json()) as CreateSpellResult;
      if (!res.ok || payload.error != null) {
        throw new Error(payload.error ?? `Request failed (${res.status})`);
      }
      setSavedTitle(payload.title ?? name);
      void refreshAndReload();
      setTitle('');
      setDescription('');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="screen-generic">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Spells</span>
          <h2>Create Custom Spell</h2>
          <p className="screen-blurb">
            Writes a homebrew Spell node in Drupal. Official spells belong
            on Search Rules Wiki.
          </p>
        </div>
      </header>

      <form onSubmit={event => { void submit(event); }} className="ai-form-pane" style={{ maxWidth: 560 }}>
        <div className="ai-form-row">
          <label className="ai-form-control">
            <span>Name</span>
            <input
              type="text"
              value={title}
              onChange={event => setTitle(event.target.value)}
              placeholder="Spell name"
              required
            />
          </label>
        </div>
        <div className="ai-form-row">
          <label className="ai-form-control">
            <span>Level</span>
            <select value={level} onChange={event => setLevel(Number(event.target.value))}>
              {LEVELS.map(value => (
                <option key={value} value={value}>
                  {value === 0 ? 'Cantrip' : `Level ${String(value)}`}
                </option>
              ))}
            </select>
          </label>
          <label className="ai-form-control">
            <span>School</span>
            <select value={school} onChange={event => setSchool(event.target.value)}>
              <option value="">None</option>
              {SPELL_SCHOOLS.map(name => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="ai-form-row">
          <label className="ai-form-control">
            <span>Casting time</span>
            <input
              type="text"
              value={castingTime}
              onChange={event => setCastingTime(event.target.value)}
            />
          </label>
          <label className="ai-form-control">
            <span>Range</span>
            <input
              type="text"
              value={spellRange}
              onChange={event => setSpellRange(event.target.value)}
            />
          </label>
        </div>
        <div className="ai-form-row">
          <label className="ai-form-control">
            <span>Components</span>
            <input
              type="text"
              value={components}
              onChange={event => setComponents(event.target.value)}
            />
          </label>
          <label className="ai-form-control">
            <span>Duration</span>
            <input
              type="text"
              value={duration}
              onChange={event => setDuration(event.target.value)}
            />
          </label>
        </div>
        <div className="ai-form-row">
          <label className="ai-form-control" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={concentration}
              onChange={event => setConcentration(event.target.checked)}
            />
            <span>Concentration</span>
          </label>
          <label className="ai-form-control" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <input
              type="checkbox"
              checked={ritual}
              onChange={event => setRitual(event.target.checked)}
            />
            <span>Ritual</span>
          </label>
        </div>
        <div className="ai-form-row">
          <label className="ai-form-control">
            <span>Description</span>
            <textarea
              value={description}
              onChange={event => setDescription(event.target.value)}
              rows={8}
              placeholder="Rules text"
            />
          </label>
        </div>

        {error != null && (
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--color-danger)' }}>{error}</p>
        )}
        {savedTitle != null && (
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--color-success)' }}>
            Saved {savedTitle}. Refreshing the compendium...
          </p>
        )}

        <div className="screen-head-actions" style={{ marginTop: 12 }}>
          <button type="submit" className="primary-btn" disabled={saving}>
            {saving ? <Spinner /> : <Icon name="plus" size={11} />}
            {saving ? 'Saving' : 'Create spell'}
          </button>
        </div>
      </form>
    </div>
  );
}
