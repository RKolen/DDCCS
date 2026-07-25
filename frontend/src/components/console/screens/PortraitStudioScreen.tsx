/**
 * PortraitStudioScreen — `characters / ascii` ("Customize Portrait").
 *
 * The ComfyUI portrait input setup: pick a character, tune the generation
 * inputs (appearance details, seed, size), and generate. Posts to
 * /api/generate-portrait, which drives local ComfyUI and attaches the result to
 * the character's field_image. Replaces the old deprecated ASCII-portrait notice.
 *
 * Generation needs COMFYUI_ENABLED=true on the sidecar; when disabled or
 * unreachable the endpoint returns 503 and this screen shows the reason.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData, playerCharacters } from '../ConsoleContext';
import type { DrupalCharacter } from '../ConsoleContext';
import {
  buildPortraitProfile,
  DEFAULT_PORTRAIT_WIDTH,
  DEFAULT_PORTRAIT_HEIGHT,
  type GeneratePortraitResult,
} from '../../../utils/portraitProfile';

interface ApiError { error: string }

const labelStyle: React.CSSProperties = {
  display: 'block', fontFamily: 'var(--font-display)', fontSize: 9,
  fontWeight: 700, letterSpacing: '0.14em', textTransform: 'uppercase',
  color: 'var(--brass-dim)', marginBottom: 5,
};
const inputStyle: React.CSSProperties = {
  width: '100%', background: 'var(--canvas)',
  border: '1px solid var(--rule)', borderRadius: 4,
  color: 'var(--ink)', fontFamily: 'var(--font-body)', fontSize: 14,
  padding: '8px 10px',
};

/**
 * Parse an integer from a form field, returning null for blank/invalid input so
 * a blank seed becomes a random seed server-side.
 */
function parseIntOrNull(value: string): number | null {
  const trimmed = value.trim();
  if (trimmed === '') return null;
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function StudioPanel({ char }: { char: DrupalCharacter }): React.ReactElement {
  const [appearance, setAppearance] = React.useState('');
  const [seed, setSeed] = React.useState('');
  const [width, setWidth] = React.useState(String(DEFAULT_PORTRAIT_WIDTH));
  const [height, setHeight] = React.useState(String(DEFAULT_PORTRAIT_HEIGHT));

  const [generating, setGenerating] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [resultUrl, setResultUrl] = React.useState<string | null>(null);
  const [usedSeed, setUsedSeed] = React.useState<number | null>(null);

  /* Reset the form and result whenever the selected character changes. */
  React.useEffect(() => {
    setAppearance('');
    setSeed('');
    setWidth(String(DEFAULT_PORTRAIT_WIDTH));
    setHeight(String(DEFAULT_PORTRAIT_HEIGHT));
    setError(null);
    setResultUrl(null);
    setUsedSeed(null);
  }, [char.id]);

  const portraitUrl = resultUrl ?? char.imageUrl;

  const handleGenerate = async (): Promise<void> => {
    setGenerating(true);
    setError(null);
    try {
      const profile = buildPortraitProfile(char);
      const extra = appearance.trim();
      if (extra) profile.appearance = extra;
      const res = await fetch('/api/generate-portrait', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          id:      char.id,
          profile,
          seed:    parseIntOrNull(seed),
          width:   parseIntOrNull(width) ?? DEFAULT_PORTRAIT_WIDTH,
          height:  parseIntOrNull(height) ?? DEFAULT_PORTRAIT_HEIGHT,
        }),
      });
      if (!res.ok) {
        const data = (await res.json()) as ApiError;
        setError(data.error ?? `Error ${res.status}`);
        return;
      }
      const data = (await res.json()) as GeneratePortraitResult;
      if (data.imageUrl) setResultUrl(data.imageUrl);
      if (typeof data.seed === 'number') setUsedSeed(data.seed);
    } catch {
      setError('Network error — could not reach the server.');
    } finally {
      setGenerating(false);
    }
  };

  const initials = char.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();

  return (
    <div className="char-sheet-detail" style={{ flex: 1, overflowY: 'auto', padding: '28px 32px 40px' }}>
      <div style={{ marginBottom: 24 }}>
        <span className="reader-eyebrow">Characters · Customize portrait</span>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 26, color: 'var(--brass-bright)', letterSpacing: '0.04em', margin: '4px 0 6px' }}>
          {char.title}
        </h2>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-dim)', margin: 0 }}>
          {[char.characterClass, char.level !== null ? `Level ${char.level}` : null, char.species]
            .filter(Boolean).join(' · ')}
        </p>
      </div>

      <div style={{ display: 'flex', gap: 28, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        {/* Preview */}
        <div style={{ width: 220, flexShrink: 0 }}>
          <div
            className="char-sheet-portrait"
            style={{ width: 220, height: 320, borderRadius: 4, overflow: 'hidden' }}
          >
            {portraitUrl
              ? <img src={portraitUrl} alt={char.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              : <span className="portrait-placeholder">{initials}</span>
            }
          </div>
          {usedSeed !== null && (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)', margin: '8px 0 0' }}>
              Seed {usedSeed} — reuse it above to reproduce this render.
            </p>
          )}
        </div>

        {/* Inputs */}
        <div style={{ flex: 1, minWidth: 280, display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div>
            <label style={labelStyle}>Appearance details <span style={{ textTransform: 'none', letterSpacing: 0, color: 'var(--ink-faint)', fontWeight: 400 }}>— optional, folded into the prompt</span></label>
            <textarea
              rows={4}
              value={appearance}
              onChange={e => setAppearance(e.target.value)}
              placeholder="e.g. weathered face, silver braid, deep green cloak, faint scar over the left brow"
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14 }}>
            <div>
              <label style={labelStyle}>Seed</label>
              <input
                type="text"
                inputMode="numeric"
                value={seed}
                onChange={e => setSeed(e.target.value)}
                placeholder="random"
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Width</label>
              <input
                type="text"
                inputMode="numeric"
                value={width}
                onChange={e => setWidth(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Height</label>
              <input
                type="text"
                inputMode="numeric"
                value={height}
                onChange={e => setHeight(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>

          <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12, color: 'var(--ink-faint)', margin: 0 }}>
            Portraits generate on the local ComfyUI (SD 1.5-class); 512×768 suits
            it best. CPU generation takes a few minutes. The result attaches to
            the character automatically.
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14, paddingTop: 2 }}>
            <button
              type="button"
              className="primary-btn"
              disabled={generating}
              onClick={() => void handleGenerate()}
            >
              <Icon name="sparkle" size={11} />
              {generating ? 'Generating…' : (portraitUrl ? 'Regenerate portrait' : 'Generate portrait')}
            </button>
            {generating && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-dim)', fontStyle: 'italic' }}>
                Rendering with ComfyUI — this can take a few minutes on CPU.
              </span>
            )}
            {error != null && (
              <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-danger)' }}>
                {error}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function PortraitStudioScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useConsoleData();
  const roster = playerCharacters(data);
  const idx = ctx.charIdx ?? 0;
  const char = roster[idx] ?? null;

  if (roster.length === 0) {
    return (
      <div className="screen-generic">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Characters · Customize portrait</span>
            <h2>Customize portrait</h2>
            <p className="screen-blurb">No characters found for this campaign.</p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="screen-chardetails">
      <aside className="char-picker">
        <ul className="char-picker-list">
          {roster.map((c, i) => {
            const initials = c.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
            return (
              <li key={c.id}>
                <button
                  type="button"
                  className={`char-picker-item${i === idx ? ' active' : ''}`}
                  onClick={() => setCtx({ ...ctx, charIdx: i })}
                >
                  <span className="char-pip">
                    {c.imageUrl
                      ? <img src={c.imageUrl} alt={c.title} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
                      : initials
                    }
                  </span>
                  <span className="char-pip-meta">
                    <strong>{c.title}</strong>
                    <span>
                      {[c.characterClass, c.level !== null ? `Lv ${c.level}` : null]
                        .filter(Boolean).join(' · ')}
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </aside>
      {char != null && <StudioPanel key={char.id} char={char} />}
    </div>
  );
}
