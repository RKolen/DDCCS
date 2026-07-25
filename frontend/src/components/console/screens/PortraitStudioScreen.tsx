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
import { MediaPickerModal } from '../MediaPickerModal';
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
  const [prompt, setPrompt] = React.useState(char.imagePrompt ?? '');
  // The last persisted prompt (the "old" one), shown for comparison whenever the
  // working box diverges. `previousPrompt` is the box value before the last
  // Generate/Enhance/Image->prompt, for a one-step Undo.
  const [savedPrompt, setSavedPrompt] = React.useState(char.imagePrompt ?? '');
  const [previousPrompt, setPreviousPrompt] = React.useState<string | null>(null);
  const [seed, setSeed] = React.useState('');
  const [width, setWidth] = React.useState(String(DEFAULT_PORTRAIT_WIDTH));
  const [height, setHeight] = React.useState(String(DEFAULT_PORTRAIT_HEIGHT));

  const [generating, setGenerating] = React.useState(false);
  const [promptBusy, setPromptBusy] = React.useState<null | 'build' | 'enhance' | 'vision' | 'save'>(null);
  const [promptMsg, setPromptMsg] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [resultUrl, setResultUrl] = React.useState<string | null>(null);
  const [usedSeed, setUsedSeed] = React.useState<number | null>(null);
  const [pickerOpen, setPickerOpen] = React.useState(false);

  /* Reset the form and result whenever the selected character changes. */
  React.useEffect(() => {
    setPrompt(char.imagePrompt ?? '');
    setSavedPrompt(char.imagePrompt ?? '');
    setPreviousPrompt(null);
    setSeed('');
    setWidth(String(DEFAULT_PORTRAIT_WIDTH));
    setHeight(String(DEFAULT_PORTRAIT_HEIGHT));
    setPromptMsg(null);
    setError(null);
    setResultUrl(null);
    setUsedSeed(null);
    setPickerOpen(false);
  }, [char.id, char.imagePrompt]);

  const portraitUrl = resultUrl ?? char.imageUrl;
  const busy = generating || promptBusy !== null;

  /* Fetch the template / enhanced prompt into the editable box. */
  const runPromptEndpoint = async (enhance: boolean): Promise<void> => {
    setPromptBusy(enhance ? 'enhance' : 'build');
    setPreviousPrompt(prompt);
    setPromptMsg(null);
    setError(null);
    try {
      const res = await fetch('/api/portrait-prompt', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          profile:  buildPortraitProfile(char),
          positive: enhance ? prompt : null,
          enhance,
        }),
      });
      const data = (await res.json()) as { positive?: string; error?: string };
      if (!res.ok) { setError(data.error ?? `Error ${res.status}`); return; }
      if (data.positive) setPrompt(data.positive);
    } catch {
      setError('Network error — could not reach the server.');
    } finally {
      setPromptBusy(null);
    }
  };

  /* Describe the current portrait into a prompt (image -> prompt). */
  const handleDescribe = async (): Promise<void> => {
    if (!portraitUrl) { setError('No portrait to describe yet.'); return; }
    setPromptBusy('vision');
    setPreviousPrompt(prompt);
    setPromptMsg(null);
    setError(null);
    try {
      const res = await fetch('/api/describe-image', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ imageUrl: portraitUrl, profile: buildPortraitProfile(char) }),
      });
      const data = (await res.json()) as { positive?: string; error?: string };
      if (!res.ok) { setError(data.error ?? `Error ${res.status}`); return; }
      if (data.positive) setPrompt(data.positive);
    } catch {
      setError('Network error — could not reach the server.');
    } finally {
      setPromptBusy(null);
    }
  };

  const handleSavePrompt = async (): Promise<void> => {
    setPromptBusy('save');
    setPromptMsg(null);
    setError(null);
    try {
      const res = await fetch('/api/save-image-prompt', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ id: char.id, prompt }),
      });
      if (!res.ok) {
        const data = (await res.json()) as ApiError;
        setError(data.error ?? `Error ${res.status}`);
        return;
      }
      setSavedPrompt(prompt);
      setPromptMsg('Prompt saved.');
    } catch {
      setError('Network error — could not reach the server.');
    } finally {
      setPromptBusy(null);
    }
  };

  const handleGenerate = async (): Promise<void> => {
    setGenerating(true);
    setError(null);
    try {
      const res = await fetch('/api/generate-portrait', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          id:       char.id,
          profile:  buildPortraitProfile(char),
          positive: prompt.trim() || null,
          seed:     parseIntOrNull(seed),
          width:    parseIntOrNull(width) ?? DEFAULT_PORTRAIT_WIDTH,
          height:   parseIntOrNull(height) ?? DEFAULT_PORTRAIT_HEIGHT,
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
            <label style={labelStyle}>Image prompt <span style={{ textTransform: 'none', letterSpacing: 0, color: 'var(--ink-faint)', fontWeight: 400 }}>— edit freely; this exact text drives generation</span></label>
            <textarea
              rows={5}
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              placeholder="Click Generate prompt to build one from the profile, or Image → prompt to describe the current portrait."
              style={{ ...inputStyle, resize: 'vertical' }}
            />
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
              <button type="button" className="ghost-btn" disabled={busy} onClick={() => void runPromptEndpoint(false)}>
                <Icon name="sparkle" size={11} /> {promptBusy === 'build' ? 'Generating…' : 'Generate prompt'}
              </button>
              <button type="button" className="ghost-btn" disabled={busy || !prompt.trim()} onClick={() => void runPromptEndpoint(true)}>
                <Icon name="model" size={11} /> {promptBusy === 'enhance' ? 'Enhancing…' : 'Enhance with AI'}
              </button>
              <button type="button" className="ghost-btn" disabled={busy || !portraitUrl} onClick={() => void handleDescribe()}>
                <Icon name="image" size={11} /> {promptBusy === 'vision' ? 'Reading image…' : 'Image → prompt'}
              </button>
              <button type="button" className="ghost-btn" disabled={busy || !prompt.trim()} onClick={() => void handleSavePrompt()}>
                <Icon name="scroll" size={11} /> {promptBusy === 'save' ? 'Saving…' : 'Save prompt'}
              </button>
              {previousPrompt !== null && previousPrompt !== prompt && (
                <button type="button" className="ghost-btn" disabled={busy} onClick={() => { setPrompt(previousPrompt); setPreviousPrompt(null); }}>
                  <Icon name="chevronLeft" size={11} /> Undo
                </button>
              )}
            </div>
            {promptMsg != null && (
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--color-success)', margin: '6px 0 0' }}>{promptMsg}</p>
            )}

            {/* Comparison: show the saved prompt whenever the working box diverges. */}
            {savedPrompt.trim() !== '' && savedPrompt !== prompt && (
              <div style={{ marginTop: 12, border: '1px solid var(--rule)', borderRadius: 4, padding: '10px 12px', background: 'var(--surface)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 6 }}>
                  <label style={{ ...labelStyle, marginBottom: 0 }}>Saved prompt <span style={{ textTransform: 'none', letterSpacing: 0, color: 'var(--ink-faint)', fontWeight: 400 }}>— old, for comparison</span></label>
                  <button type="button" className="ghost-btn" disabled={busy} onClick={() => setPrompt(savedPrompt)}>
                    Revert to saved
                  </button>
                </div>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink-dim)', margin: 0, whiteSpace: 'pre-wrap' }}>
                  {savedPrompt}
                </p>
              </div>
            )}
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
              disabled={busy}
              onClick={() => void handleGenerate()}
            >
              <Icon name="sparkle" size={11} />
              {generating ? 'Generating…' : (portraitUrl ? 'Regenerate portrait' : 'Generate portrait')}
            </button>
            <button
              type="button"
              className="ghost-btn"
              disabled={busy}
              onClick={() => setPickerOpen(true)}
            >
              <Icon name="image" size={11} /> Choose existing image
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

      {pickerOpen && (
        <MediaPickerModal
          characterId={char.id}
          characterTitle={char.title}
          currentImageUrl={portraitUrl}
          mediaType={char.characterType === false ? 'npc_portrait' : 'character_portrait'}
          onClose={() => setPickerOpen(false)}
          onSelected={url => { if (url) setResultUrl(url); }}
        />
      )}
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
