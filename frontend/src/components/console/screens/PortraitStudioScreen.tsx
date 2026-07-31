/**
 * PortraitStudioScreen — `characters / ascii` ("Customize Portrait").
 *
 * The ComfyUI portrait input setup: pick a character, tune the generation
 * inputs (prompt, negative prompt, seed, size), and generate. Generation is
 * queued (`dnd_portrait`): the host runs it one job at a time, so leaving this
 * screen mid-render no longer loses the work. Replaces the old deprecated
 * ASCII-portrait notice.
 *
 * A finished render is a proposal, not a fact: it is stored in the media library
 * and shown here as a candidate, and only Accept points the character's
 * field_image at it. That is what stops a render finishing in the background
 * from replacing a portrait nobody wanted replaced. The activity drawer links
 * back here for exactly that decision.
 *
 * Generation needs COMFYUI_ENABLED=true on the sidecar; when it is disabled or
 * unreachable the job fails with that reason and this screen shows it.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon, Spinner } from '../atoms';
import { useConsoleData, playerCharacters } from '../ConsoleContext';
import type { DrupalCharacter } from '../ConsoleContext';
import { MediaPickerModal } from '../MediaPickerModal';
import {
  buildPortraitProfile,
  usePortraitReview,
  DEFAULT_PORTRAIT_WIDTH,
  DEFAULT_PORTRAIT_HEIGHT,
  DEFAULT_IDENTITY_WEIGHT,
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

/**
 * Parse the likeness weight, falling back to the shared default so a cleared or
 * nonsensical box still generates rather than sending the sidecar a null it
 * would have to guess about.
 */
function parseWeight(value: string): number {
  const parsed = Number.parseFloat(value.trim());
  if (!Number.isFinite(parsed)) return DEFAULT_IDENTITY_WEIGHT;
  return Math.min(Math.max(parsed, 0), 1.5);
}

interface StudioPanelProps {
  char: DrupalCharacter;
  /** A queued render to pick back up, passed through from an activity row. */
  reviewJobId?: string;
}

function StudioPanel({ char, reviewJobId }: StudioPanelProps): React.ReactElement {
  const [prompt, setPrompt] = React.useState(char.imagePrompt ?? '');
  // The last persisted prompt (the "old" one), shown for comparison whenever the
  // working box diverges. `previousPrompt` is the box value before the last
  // Generate/Enhance/Image->prompt, for a one-step Undo.
  const [savedPrompt, setSavedPrompt] = React.useState(char.imagePrompt ?? '');
  const [previousPrompt, setPreviousPrompt] = React.useState<string | null>(null);
  // What the render must avoid. Pre-filled with the sidecar's standard negative;
  // left blank the sidecar applies that same default.
  const [negative, setNegative] = React.useState('');
  const [seed, setSeed] = React.useState('');
  const [width, setWidth] = React.useState(String(DEFAULT_PORTRAIT_WIDTH));
  const [height, setHeight] = React.useState(String(DEFAULT_PORTRAIT_HEIGHT));
  // Condition the render on the current portrait so the face carries over
  // (IPAdapter). On by default: a regeneration is nearly always meant to be the
  // same character. Turn it off to let the prompt redesign them from scratch.
  const [keepLikeness, setKeepLikeness] = React.useState(true);
  const [likenessWeight, setLikenessWeight] = React.useState(String(DEFAULT_IDENTITY_WEIGHT));

  const [promptBusy, setPromptBusy] = React.useState<null | 'build' | 'enhance' | 'vision' | 'save'>(null);
  const [promptMsg, setPromptMsg] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  // The portrait actually stored on the character right now: what it had, or
  // what a later accept or library pick replaced it with.
  const [storedUrl, setStoredUrl] = React.useState<string | null>(char.imageUrl);
  const [usedSeed, setUsedSeed] = React.useState<number | null>(null);
  const [pickerOpen, setPickerOpen] = React.useState(false);
  // The queue-then-confirm cycle: nothing here touches field_image until accept.
  const review = usePortraitReview(reviewJobId);

  /* Reset the form whenever the selected character changes. Review state is
     deliberately untouched: the panel is keyed by character, so a switch
     remounts it, and a prompt save must not throw away a pending render. */
  React.useEffect(() => {
    setPrompt(char.imagePrompt ?? '');
    setSavedPrompt(char.imagePrompt ?? '');
    setPreviousPrompt(null);
    setNegative('');
    setSeed('');
    setWidth(String(DEFAULT_PORTRAIT_WIDTH));
    setHeight(String(DEFAULT_PORTRAIT_HEIGHT));
    setKeepLikeness(true);
    setLikenessWeight(String(DEFAULT_IDENTITY_WEIGHT));
    setPromptMsg(null);
    setError(null);
    setStoredUrl(char.imageUrl);
    setUsedSeed(null);
    setPickerOpen(false);
  }, [char.id, char.imagePrompt, char.imageUrl]);

  /* Pre-fill the negative box with the sidecar's standard negative. The prompt
     endpoint returns it next to the template positive and makes no model call
     when `enhance` is false, so this is a cheap round trip. If it fails the box
     stays blank and the sidecar applies the same default at generation time. */
  React.useEffect(() => {
    const profile = buildPortraitProfile(char);
    if (Object.keys(profile).length === 0) return undefined;
    let cancelled = false;
    void (async (): Promise<void> => {
      try {
        const res = await fetch('/api/portrait-prompt', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ profile, positive: null, enhance: false }),
        });
        if (!res.ok) return;
        const data = (await res.json()) as { negative?: string };
        const standard = data.negative ?? '';
        if (!cancelled && standard) setNegative(current => (current.trim() === '' ? standard : current));
      } catch {
        /* Leave it blank; generation still applies the sidecar default. */
      }
    })();
    return () => { cancelled = true; };
  }, [char.id]);

  // A pending render is what the preview shows - clearly marked as not attached
  // - so the operator judges the thing they are about to accept.
  const attachedUrl = review.attachedUrl ?? storedUrl;
  const portraitUrl = review.candidate?.imageUrl ?? attachedUrl;
  const busy = review.running || review.reviewing !== null || promptBusy !== null;
  const seedShown = review.candidate?.seed ?? usedSeed;

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

  /* Queue the render. The host runs it whether or not this screen stays open,
     which is also why the result comes back as a candidate rather than a fact. */
  const handleGenerate = async (): Promise<void> => {
    setError(null);
    setPromptMsg(null);
    await review.generate(`Portrait: ${char.title}`, {
      characterId: char.id,
      profile:     buildPortraitProfile(char),
      positive:    prompt.trim() || null,
      negative:    negative.trim() || null,
      seed:        parseIntOrNull(seed),
      width:       parseIntOrNull(width) ?? DEFAULT_PORTRAIT_WIDTH,
      height:      parseIntOrNull(height) ?? DEFAULT_PORTRAIT_HEIGHT,
      // The attached portrait, not the pending candidate: likeness is carried
      // from what the character actually is, not from a render nobody kept.
      referenceImageUrl: keepLikeness ? attachedUrl : null,
      identityWeight:    keepLikeness ? parseWeight(likenessWeight) : null,
    });
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
            className={`char-sheet-portrait${review.candidate ? ' portrait-candidate' : ''}`}
            style={{ width: 220, height: 320, borderRadius: 4, overflow: 'hidden' }}
          >
            {portraitUrl
              ? <img src={portraitUrl} alt={char.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              : <span className="portrait-placeholder">{initials}</span>
            }
          </div>

          {/* The confirm step. Until Accept, the character still shows whatever
              it showed before, and this render is only a file in the library. */}
          {review.candidate && (
            <div className="portrait-review">
              <span className="portrait-review-tag">Not attached yet</span>
              <p className="portrait-review-note">
                This render is stored in the media library. {char.title} keeps the
                portrait it has until you accept it.
              </p>
              <div className="portrait-review-actions">
                <button
                  type="button"
                  className="primary-btn"
                  disabled={review.reviewing !== null}
                  onClick={() => void review.accept()}
                >
                  {review.reviewing === 'accept' ? <Spinner /> : <Icon name="image" size={11} />}
                  {review.reviewing === 'accept' ? 'Attaching…' : 'Accept portrait'}
                </button>
                <button
                  type="button"
                  className="ghost-btn"
                  disabled={review.reviewing !== null}
                  onClick={() => void review.discard()}
                >
                  {review.reviewing === 'discard' ? <Spinner /> : <Icon name="close" size={11} />}
                  {review.reviewing === 'discard' ? 'Discarding…' : 'Discard'}
                </button>
              </div>
              {attachedUrl && (
                <div className="portrait-review-current">
                  <span>Current portrait</span>
                  <img src={attachedUrl} alt={`Current portrait of ${char.title}`} />
                </div>
              )}
            </div>
          )}

          {review.notice != null && (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--color-success)', margin: '8px 0 0' }}>
              {review.notice}
            </p>
          )}
          {review.error != null && (
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--color-danger)', margin: '8px 0 0' }}>
              {review.error}
            </p>
          )}
          {seedShown !== null && (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)', margin: '8px 0 0' }}>
              Seed {seedShown} — reuse it above to reproduce this render.
            </p>
          )}
          {/* Say which render this actually is. Asking to keep the likeness and
              getting it are different things: without IPAdapter installed, or
              with an unreachable reference, the sidecar still renders - just
              from the prompt alone. */}
          {review.candidate !== null && (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-faint)', margin: '4px 0 0' }}>
              {review.candidate.usedReference
                ? 'Likeness matched to the current portrait.'
                : 'Rendered from the prompt alone — no likeness reference applied.'}
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
                {promptBusy === 'build' ? <Spinner /> : <Icon name="sparkle" size={11} />}
                {promptBusy === 'build' ? 'Generating…' : 'Generate prompt'}
              </button>
              <button type="button" className="ghost-btn" disabled={busy || !prompt.trim()} onClick={() => void runPromptEndpoint(true)}>
                {promptBusy === 'enhance' ? <Spinner /> : <Icon name="model" size={11} />}
                {promptBusy === 'enhance' ? 'Enhancing…' : 'Enhance with AI'}
              </button>
              <button type="button" className="ghost-btn" disabled={busy || !portraitUrl} onClick={() => void handleDescribe()}>
                {promptBusy === 'vision' ? <Spinner /> : <Icon name="image" size={11} />}
                {promptBusy === 'vision' ? 'Reading image…' : 'Image → prompt'}
              </button>
              <button type="button" className="ghost-btn" disabled={busy || !prompt.trim()} onClick={() => void handleSavePrompt()}>
                {promptBusy === 'save' ? <Spinner /> : <Icon name="scroll" size={11} />}
                {promptBusy === 'save' ? 'Saving…' : 'Save prompt'}
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

          <div>
            <label style={labelStyle}>Negative prompt <span style={{ textTransform: 'none', letterSpacing: 0, color: 'var(--ink-faint)', fontWeight: 400 }}>— what the render must avoid</span></label>
            <textarea
              rows={2}
              value={negative}
              onChange={e => setNegative(e.target.value)}
              placeholder="Leave blank to use the standard negative."
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

          <div>
            <label style={{ ...labelStyle, display: 'flex', alignItems: 'center', gap: 7, marginBottom: 6 }}>
              <input
                type="checkbox"
                checked={keepLikeness}
                disabled={attachedUrl === null}
                onChange={e => setKeepLikeness(e.target.checked)}
              />
              Keep this character&apos;s likeness
            </label>
            {attachedUrl === null ? (
              <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12, color: 'var(--ink-faint)', margin: 0 }}>
                Nothing to match yet — the first render sets the face, and later
                ones can be held to it.
              </p>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <input
                  type="range"
                  min="0.3"
                  max="1"
                  step="0.05"
                  value={likenessWeight}
                  disabled={!keepLikeness}
                  onChange={e => setLikenessWeight(e.target.value)}
                  style={{ flex: 1, maxWidth: 220, opacity: keepLikeness ? 1 : 0.4 }}
                />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-dim)' }}>
                  {keepLikeness ? `${parseWeight(likenessWeight).toFixed(2)} — prompt freedom ↔ likeness` : 'off — the prompt alone'}
                </span>
              </div>
            )}
          </div>

          <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 12, color: 'var(--ink-faint)', margin: 0 }}>
            Portraits generate on the local ComfyUI (SD 1.5-class); 512×768 suits
            it best. CPU generation takes a few minutes. The render comes back for
            you to accept — nothing replaces the current portrait until you do.
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14, paddingTop: 2 }}>
            <button
              type="button"
              className="primary-btn"
              disabled={busy}
              onClick={() => void handleGenerate()}
            >
              {review.running ? <Spinner /> : <Icon name="sparkle" size={11} />}
              {review.running ? 'Generating…' : (portraitUrl ? 'Regenerate portrait' : 'Generate portrait')}
            </button>
            <button
              type="button"
              className="ghost-btn"
              disabled={busy}
              onClick={() => setPickerOpen(true)}
            >
              <Icon name="image" size={11} /> Choose existing image
            </button>
            {review.running && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-dim)', fontStyle: 'italic' }}>
                Queued on the host — this can take a few minutes on CPU. You can
                leave this screen; the activity drawer will link you back to accept it.
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
          onSelected={url => { if (url) setStoredUrl(url); }}
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
  const reviewJobId = typeof ctx.reviewJobId === 'string' ? ctx.reviewJobId : undefined;

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
      {char != null && <StudioPanel key={char.id} char={char} reviewJobId={reviewJobId} />}
    </div>
  );
}
