/**
 * CharacterDetailScreen — `characters / view` (and `npcs / n-view`).
 *
 * Data from ConsoleContext only. ctx.charIdx indexes into the
 * playerCharacters() or npcCharacters() list. No mock fallbacks.
 *
 * Portrait generation is queued, and a finished render is offered for review
 * rather than attached: the sheet previews the candidate and Accept is what
 * actually replaces the character's portrait.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData, playerCharacters, npcCharacters } from '../ConsoleContext';
import type { DrupalCampaign } from '../ConsoleContext';
import { drupalAdminUrl } from '../../../utils/drupalLinks';
import { Icon, Spinner } from '../atoms';
import { ImageLightbox } from '../../atoms/ImageLightbox';
import { CharacterRelationsTab } from '../CharacterRelationsTab';
import {
  buildPortraitProfile,
  usePortraitReview,
  DEFAULT_PORTRAIT_WIDTH,
  DEFAULT_PORTRAIT_HEIGHT,
} from '../../../utils/portraitProfile';

function partyIdsForCampaign(campaigns: DrupalCampaign[], name: string): Set<string> {
  const camp = campaigns.find(c => c.name === name);
  return new Set(camp?.currentPartyIds ?? []);
}

export function CharacterDetailScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useConsoleData();
  const isNpc = Boolean(ctx.npcMode);
  const [lightboxOpen, setLightboxOpen] = React.useState(false);
  // The queue-then-confirm cycle. Nothing here writes field_image until accept.
  const review = usePortraitReview(typeof ctx.reviewJobId === 'string' ? ctx.reviewJobId : undefined);
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
  // Sheet vs Relations. Relations reads across every arc this character is in,
  // so it is a view of the sheet rather than a separate screen.
  const [tab, setTab] = React.useState<'sheet' | 'relations'>('sheet');
  // What the character actually shows: the stored portrait, or one accepted here.
  const attachedUrl = review.attachedUrl ?? char?.imageUrl ?? null;
  // A pending render takes over the preview, labelled as not yet attached.
  const portraitUrl = review.candidate?.imageUrl ?? attachedUrl;

  // Clear the review state whenever the selected character changes so a render
  // or error never bleeds across characters. Guarded on an actual change: on the
  // first render there is nothing to clear, and clearing would race the pickup
  // of the job an activity row sent us here to review.
  const charId = char?.id;
  const resetReview = review.reset;
  const shownCharId = React.useRef(charId);
  React.useEffect(() => {
    if (shownCharId.current === charId) return;
    shownCharId.current = charId;
    resetReview();
  }, [charId, resetReview]);

  const handleGenerate = async (): Promise<void> => {
    if (char == null) return;
    await review.generate(`Portrait: ${char.title}`, {
      characterId: char.id,
      profile:     buildPortraitProfile(char),
      positive:    char.imagePrompt ?? null,
      width:       DEFAULT_PORTRAIT_WIDTH,
      height:      DEFAULT_PORTRAIT_HEIGHT,
      // Regenerating from here is always "another picture of this character",
      // so the attached portrait conditions the render (IPAdapter) and the face
      // carries over. Ignored by the sidecar when IPAdapter is not installed.
      // The Portrait Studio is where that can be turned off deliberately.
      referenceImageUrl: attachedUrl,
    });
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
                className={`char-sheet-portrait${review.candidate ? ' portrait-candidate' : ''}`}
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
                {review.candidate ? (
                  <>
                    <button
                      type="button"
                      className="primary-btn"
                      disabled={review.reviewing !== null}
                      onClick={() => void review.accept()}
                    >
                      {review.reviewing === 'accept' ? <Spinner /> : <Icon name="image" size={11} />}
                      {review.reviewing === 'accept' ? 'Attaching…' : 'Accept image'}
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
                  </>
                ) : (
                  <button
                    type="button"
                    className="ghost-btn"
                    disabled={review.running}
                    onClick={() => void handleGenerate()}
                  >
                    {review.running ? <Spinner /> : <Icon name="sparkle" size={11} />}
                    {review.running ? 'Generating…' : (portraitUrl ? 'Regenerate image' : 'Generate image')}
                  </button>
                )}
                {char.path && (
                  <Link to={char.path} className="ghost-btn" style={{ textDecoration: 'none' }}>
                    <Icon name="scroll" size={11} /> Full sheet
                  </Link>
                )}
              </div>
            </div>

            {review.candidate && (
              <p style={{ margin: '10px 0 0', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--color-warning)' }}>
                Showing a new render, not attached yet — {char.title} keeps the
                current portrait unless you accept it.
              </p>
            )}
            {review.error != null && (
              <p style={{ margin: '10px 0 0', fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--color-danger)' }}>
                {review.error}
              </p>
            )}
            {review.notice != null && (
              <p style={{ margin: '10px 0 0', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--color-success)' }}>
                {review.notice}
              </p>
            )}
            {review.running && (
              <p style={{ margin: '10px 0 0', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-dim)', fontStyle: 'italic' }}>
                Rendering a portrait with ComfyUI — this can take a few minutes on
                CPU. You can leave this screen; the activity drawer links back here
                to accept the result.
              </p>
            )}

            <div className="arc-tab-row char-sheet-tabs">
              <button
                type="button"
                className={`arc-tab${tab === 'sheet' ? ' active' : ''}`}
                onClick={() => setTab('sheet')}
              >
                Sheet
              </button>
              <button
                type="button"
                className={`arc-tab${tab === 'relations' ? ' active' : ''}`}
                onClick={() => setTab('relations')}
              >
                Relations
              </button>
            </div>

            {tab === 'sheet' && stats.length > 0 && (
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

            {tab === 'relations' && <CharacterRelationsTab char={char} />}
          </>
        )}
      </div>
    </div>
  );
}
