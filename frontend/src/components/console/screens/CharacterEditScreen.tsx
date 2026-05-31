/**
 * CharacterEditScreen — `characters / edit`
 *
 * In-app richness-field editor. Required fields (name, class, level, etc.)
 * are managed in Drupal. This screen edits the optional fields that AI
 * generation benefits from: pronouns, background, the four RP quadruplet
 * (traits / ideals / bonds / flaws).
 *
 * Submits via /api/update-character (GraphQL mutation proxied server-side).
 * Portrait upload is intentionally excluded — handled separately via ComfyUI.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData, playerCharacters } from '../ConsoleContext';
import type { DrupalCharacter } from '../ConsoleContext';

/* ────────────────────────────────────────────────────────────
   API types
   ──────────────────────────────────────────────────────────── */

interface ApiError { error: string }

/* ────────────────────────────────────────────────────────────
   Helpers
   ──────────────────────────────────────────────────────────── */

function splitLines(v: string): string[] {
  return v.split('\n').map(s => s.trim()).filter(Boolean);
}

function joinLines(arr: string[]): string {
  return arr.join('\n');
}

/* ────────────────────────────────────────────────────────────
   Picker
   ──────────────────────────────────────────────────────────── */

function CharPicker({
  roster, selectedId, onSelect,
}: {
  roster: DrupalCharacter[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}): React.ReactElement {
  return (
    <aside className="char-picker">
      <ul className="char-picker-list">
        {roster.map(c => {
          const initials = c.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
          return (
            <li key={c.id}>
              <button
                type="button"
                className={`char-picker-item${c.id === selectedId ? ' active' : ''}`}
                onClick={() => onSelect(c.id)}
              >
                <span className="char-pip">
                  {c.imageUrl
                    ? <img src={c.imageUrl} alt={c.title} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
                    : initials
                  }
                </span>
                <span className="char-pip-meta">
                  <span className="char-pip-name">{c.title}</span>
                  {c.characterClass != null && (
                    <span className="char-pip-class">
                      {c.characterClass}{c.level != null ? ` ${c.level}` : ''}
                    </span>
                  )}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}

/* ────────────────────────────────────────────────────────────
   Edit form
   ──────────────────────────────────────────────────────────── */

function EditForm({ char }: { char: DrupalCharacter }): React.ReactElement {
  const [pronouns,   setPronouns]   = React.useState(char.pronouns ?? '');
  const [background, setBackground] = React.useState(char.background ?? '');
  const [traits,     setTraits]     = React.useState(joinLines(char.personalityTraits));
  const [ideals,     setIdeals]     = React.useState(joinLines(char.ideals));
  const [bonds,      setBonds]      = React.useState(joinLines(char.bonds));
  const [flaws,      setFlaws]      = React.useState(joinLines(char.flaws));

  const [saving,  setSaving]  = React.useState(false);
  const [error,   setError]   = React.useState<string | null>(null);
  const [savedAt, setSavedAt] = React.useState<string | null>(null);

  /* Reset form whenever the selected character changes */
  React.useEffect(() => {
    setPronouns(char.pronouns ?? '');
    setBackground(char.background ?? '');
    setTraits(joinLines(char.personalityTraits));
    setIdeals(joinLines(char.ideals));
    setBonds(joinLines(char.bonds));
    setFlaws(joinLines(char.flaws));
    setError(null);
    setSavedAt(null);
  }, [char.id]); /* eslint-disable-line react-hooks/exhaustive-deps */

  const isDirty =
    pronouns   !== (char.pronouns ?? '')           ||
    background !== (char.background ?? '')          ||
    traits     !== joinLines(char.personalityTraits) ||
    ideals     !== joinLines(char.ideals)            ||
    bonds      !== joinLines(char.bonds)             ||
    flaws      !== joinLines(char.flaws);

  const handleSave = async (): Promise<void> => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch('/api/update-character', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id:                char.id,
          pronouns:          pronouns.trim()   || null,
          background:        background.trim() || null,
          personalityTraits: splitLines(traits),
          ideals:            splitLines(ideals),
          bonds:             splitLines(bonds),
          flaws:             splitLines(flaws),
        }),
      });
      if (!res.ok) {
        const data = (await res.json()) as ApiError;
        setError(data.error ?? `Error ${res.status}`);
        return;
      }
      setSavedAt(new Date().toLocaleTimeString());
    } catch {
      setError('Network error — could not reach the server.');
    } finally {
      setSaving(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', background: 'var(--canvas)',
    border: '1px solid var(--rule)', borderRadius: 4,
    color: 'var(--ink)', fontFamily: 'var(--font-body)', fontSize: 14,
    padding: '8px 10px',
  };
  const labelStyle: React.CSSProperties = {
    display: 'block', fontFamily: 'var(--font-display)', fontSize: 9,
    fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase',
    color: 'var(--brass-dim)', marginBottom: 5,
  };
  const hintStyle: React.CSSProperties = {
    fontFamily: 'var(--font-body)', fontStyle: 'italic',
    fontSize: 11, color: 'var(--ink-faint)', marginLeft: 8,
  };

  return (
    <div className="char-sheet-detail" style={{ flex: 1, overflowY: 'auto', padding: '28px 32px 40px' }}>

      {/* Character header */}
      <div style={{ marginBottom: 28 }}>
        <span className="reader-eyebrow">Characters · Edit profile</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 26, color: 'var(--brass-bright)', letterSpacing: '0.04em', margin: '4px 0 6px' }}>
          {char.title}
        </h2>
        {char.characterClass != null && (
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-dim)', margin: 0 }}>
            {char.characterClass}{char.level != null ? ` · Level ${char.level}` : ''}{char.campaign != null ? ` · ${char.campaign}` : ''}
          </p>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

        {/* Single-line fields */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <label style={labelStyle}>Pronouns</label>
            <input
              type="text"
              value={pronouns}
              onChange={e => setPronouns(e.target.value)}
              placeholder="e.g. she/her"
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>Background</label>
            <input
              type="text"
              value={background}
              onChange={e => setBackground(e.target.value)}
              placeholder="e.g. Soldier, Outlander"
              style={inputStyle}
            />
          </div>
        </div>

        {/* RP quadruplet */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {([
            ['Personality traits', traits,  setTraits,  'What does this character look, act, and speak like?'],
            ['Ideals',             ideals,  setIdeals,  'What drives this character above all else?'],
            ['Bonds',              bonds,   setBonds,   'Who or what does this character care most about?'],
            ['Flaws',              flaws,   setFlaws,   "What are this character's vices or compulsions?"],
          ] as const).map(([label, value, setter, hint]) => (
            <div key={label}>
              <label style={labelStyle}>
                {label}
                <span style={hintStyle}>one per line</span>
              </label>
              <textarea
                rows={4}
                value={value}
                onChange={e => setter(e.target.value)}
                placeholder={hint}
                style={{ ...inputStyle, resize: 'vertical' }}
              />
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, paddingTop: 8 }}>
          <button
            type="button"
            className="primary-btn"
            disabled={saving || !isDirty}
            onClick={() => void handleSave()}
          >
            <Icon name="tools" size={11} />
            {saving ? 'Saving…' : 'Save changes'}
          </button>

          {!isDirty && savedAt == null && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)' }}>
              No changes
            </span>
          )}
          {savedAt != null && !isDirty && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--color-success)' }}>
              Saved at {savedAt}
            </span>
          )}
          {error != null && (
            <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-danger)' }}>
              {error}
            </span>
          )}
        </div>

        <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12, color: 'var(--ink-faint)', margin: 0 }}>
          Portrait, name, class, level, and combat stats are managed in Drupal.
          Reload the page after saving to reflect updates in other screens.
        </p>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Screen
   ──────────────────────────────────────────────────────────── */

export function CharacterEditScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data   = useConsoleData();
  const roster = playerCharacters(data);
  const idx    = ctx.charIdx ?? 0;
  const char   = roster[idx] ?? null;

  if (roster.length === 0) {
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Characters · Edit profile</span>
            <h2>Edit character profile</h2>
            <p className="screen-blurb">No characters found for this campaign.</p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="screen-chardetails">
      <CharPicker
        roster={roster}
        selectedId={char?.id ?? null}
        onSelect={id => {
          const i = roster.findIndex(c => c.id === id);
          if (i !== -1) setCtx({ ...ctx, charIdx: i });
        }}
      />
      {char != null && <EditForm key={char.id} char={char} />}
    </div>
  );
}
