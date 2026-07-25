/**
 * CharacterDetailScreen — `characters / view` and `read / r-char`.
 *
 * Data from ConsoleContext only. ctx.charIdx indexes into the
 * playerCharacters() or npcCharacters() list. No mock fallbacks.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData, playerCharacters, npcCharacters } from '../ConsoleContext';
import type { DrupalCampaign, DrupalCharacter } from '../ConsoleContext';
import { drupalAdminUrl } from '../../../utils/drupalLinks';
import { Icon } from '../atoms';
import { ImageLightbox } from '../../atoms/ImageLightbox';

function partyIdsForCampaign(campaigns: DrupalCampaign[], name: string): Set<string> {
  const camp = campaigns.find(c => c.name === name);
  return new Set(camp?.currentPartyIds ?? []);
}

/**
 * Assemble the snake_case profile the sidecar portrait prompt builder reads
 * (see src/ai/portrait_prompt.py). Only the keys it uses are sent; empty
 * fields are omitted so a sparse character still yields a valid, non-generic
 * prompt.
 */
function buildPortraitProfile(char: DrupalCharacter): Record<string, unknown> {
  const profile: Record<string, unknown> = {};
  if (char.species) profile.species = char.species;
  if (char.lineage) profile.lineage = char.lineage;
  if (char.characterClass) profile.character_class = char.characterClass;
  if (char.pronouns) profile.pronouns = char.pronouns;
  if (char.background) profile.background = char.background;
  if (char.personalityTraits.length > 0) profile.personality_traits = char.personalityTraits;
  if (char.arc?.summary) profile.arc_summary = char.arc.summary;
  return profile;
}

/** Successful /api/generate-portrait response. */
interface GeneratePortraitResult {
  imageUrl: string | null;
}

// SD 1.5-class checkpoints render portraits best at 512x768; the sidecar's
// default (832x1216) is SDXL-shaped and degrades on SD 1.5 (doubled faces,
// slower on CPU). If an SDXL checkpoint is ever configured, these should move
// to sidecar config keyed off the checkpoint rather than being fixed here.
const PORTRAIT_WIDTH = 512;
const PORTRAIT_HEIGHT = 768;

export function CharacterDetailScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useConsoleData();
  const isNpc = Boolean(ctx.npcMode);
  const [lightboxOpen, setLightboxOpen] = React.useState(false);
  const [generating, setGenerating] = React.useState(false);
  const [genError, setGenError] = React.useState<string | null>(null);
  // Newly generated portrait URL, shown immediately without a full page reload.
  const [genImageUrl, setGenImageUrl] = React.useState<string | null>(null);
  const allInType = isNpc ? npcCharacters(data) : playerCharacters(data);
  // PCs: filter by the campaign's currentPartyIds.
  // NPCs: show all (their campaign link isn't via currentParty).
  const partyIds = (!isNpc && ctx.activeCampaignName)
    ? partyIdsForCampaign(data.campaigns, ctx.activeCampaignName)
    : null;
  const roster = (partyIds && partyIds.size > 0)
    ? allInType.filter(c => partyIds.has(c.id))
    : allInType;
  const idx = ctx.charIdx ?? 0;
  const char = roster[idx] ?? null;
  const eyebrow = isNpc ? 'NPC Profile' : 'Character Sheet';
  // Prefer a just-generated portrait; fall back to the stored one.
  const portraitUrl = genImageUrl ?? char?.imageUrl ?? null;

  // Reset the generation state whenever the selected character changes so a
  // new portrait or error never bleeds across characters.
  React.useEffect(() => {
    setGenImageUrl(null);
    setGenError(null);
    setGenerating(false);
  }, [char?.id]);

  const handleGenerate = async (): Promise<void> => {
    if (char == null) return;
    setGenerating(true);
    setGenError(null);
    try {
      const res = await fetch('/api/generate-portrait', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          id:      char.id,
          profile: buildPortraitProfile(char),
          width:   PORTRAIT_WIDTH,
          height:  PORTRAIT_HEIGHT,
        }),
      });
      if (!res.ok) {
        const data = (await res.json()) as { error?: string };
        setGenError(data.error ?? `Error ${res.status}`);
        return;
      }
      const data = (await res.json()) as GeneratePortraitResult;
      if (data.imageUrl) setGenImageUrl(data.imageUrl);
    } catch {
      setGenError('Network error — could not reach the server.');
    } finally {
      setGenerating(false);
    }
  };

  const stats: Array<{ label: string; value: string | number }> = [];
  if (char?.maximumHitpoints !== null && char?.maximumHitpoints !== undefined) stats.push({ label: 'HP', value: char.maximumHitpoints });
  if (char?.armorClass !== null && char?.armorClass !== undefined) stats.push({ label: 'AC', value: char.armorClass });
  if (char?.level !== null && char?.level !== undefined) stats.push({ label: 'Level', value: char.level });

  return (
    <div className="screen-chardetails">

      {/* Picker */}
      {roster.length > 0 && (
        <aside className="char-picker">
          <ul className="char-picker-list">
            {roster.map((c, i) => {
              const initials = c.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
              return (
                <li key={c.id}>
                  <button
                    className={`char-picker-item${i === idx ? ' active' : ''}`}
                    onClick={() => setCtx({ ...ctx, charIdx: i })}
                  >
                    <span className="char-pip">{initials}</span>
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
      )}

      {/* Sheet */}
      <div className="char-sheet">
        {char === null ? (
          <div style={{ padding: 32, fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic' }}>
            {roster.length === 0
              ? (isNpc
                ? 'No NPCs in Drupal. Create a Character node with Character Type set to off.'
                : 'No player characters in Drupal. Create a Character node with Character Type set to on.')
              : 'Select a character from the list.'}
          </div>
        ) : (
          <>
            <div className="char-sheet-head">
              <div
                className="char-sheet-portrait"
                onClick={portraitUrl ? () => setLightboxOpen(true) : undefined}
                style={portraitUrl ? { cursor: 'zoom-in' } : undefined}
              >
                {portraitUrl
                  ? <img src={portraitUrl} alt={char.title} style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 2 }} />
                  : <span className="portrait-placeholder">
                    {char.title.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()}
                  </span>
                }
              </div>
              {lightboxOpen && portraitUrl && (
                <ImageLightbox src={portraitUrl} alt={char.title} onClose={() => setLightboxOpen(false)} />
              )}
              <div className="char-sheet-title">
                <span className="reader-eyebrow">{eyebrow}</span>
                <h1>{char.title}</h1>
                {char.nickname && (
                  <p style={{ margin: '2px 0 4px', fontFamily: 'var(--font-body)', fontStyle: 'italic', color: 'var(--ink-dim)', fontSize: 14 }}>
                    {char.nickname}
                  </p>
                )}
                <span className="char-sheet-sub">
                  {[char.pronouns, char.characterClass, char.level !== null ? `Level ${char.level}` : null, char.campaign]
                    .filter(Boolean).join(' · ')}
                </span>
              </div>
              <div className="char-sheet-actions">
                <button
                  type="button"
                  className="ghost-btn"
                  disabled={generating}
                  onClick={() => void handleGenerate()}
                >
                  <Icon name="sparkle" size={11} />
                  {generating ? 'Generating…' : (portraitUrl ? 'Regenerate image' : 'Generate image')}
                </button>
                {char.path && (
                  <Link to={char.path} className="ghost-btn" style={{ textDecoration: 'none' }}>
                    <Icon name="scroll" size={11} /> Full sheet
                  </Link>
                )}
              </div>
            </div>

            {genError != null && (
              <p style={{ margin: '10px 0 0', fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-danger)' }}>
                {genError}
              </p>
            )}
            {generating && (
              <p style={{ margin: '10px 0 0', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-dim)', fontStyle: 'italic' }}>
                Rendering a portrait with ComfyUI — this can take a few minutes on CPU.
              </p>
            )}

            {stats.length > 0 && (
              <div className="char-sheet-body">
                <div className="char-stat-row" style={{ gridTemplateColumns: `repeat(${stats.length}, 1fr)` }}>
                  {stats.map(s => (
                    <div key={s.label} className="stat-cell">
                      <span className="stat-label">{s.label}</span>
                      <span className="stat-val">{s.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
