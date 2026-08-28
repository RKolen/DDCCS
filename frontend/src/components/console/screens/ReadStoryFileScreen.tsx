/**
 * ReadStoryFileScreen — `stories / read`.
 *
 * Story list comes from ConsoleContext (real Drupal stories).
 * Filtered to the active campaign from ctx.activeCampaignName.
 * No mock fallbacks — empty state when Drupal has no stories.
 *
 * The body is fetched per story rather than carried in the console's page
 * data: a campaign's stories run to hundreds of thousands of characters, and
 * baking all of them into every console load to read one is not worth it. It
 * renders in the same unfurling scroll the story page uses, from the same
 * component, so the two cannot drift apart.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import {
  useConsoleData, storiesForCampaign, charactersForCampaign, npcCharacters,
} from '../ConsoleContext';
import { Icon, Spinner } from '../atoms';
import { StoryScroll } from '../../molecules/StoryScroll';
import { StoryImageWizard } from '../StoryImageWizard';
import { rosterPersonFromCharacter } from '../../../utils/storyImage';

function NarrateMedallion(): React.ReactElement {
  const [active, setActive] = React.useState(false);
  return (
    <button className={`big-medallion${active ? ' is-active' : ''}`} onClick={() => setActive(!active)}>
      <Icon name={active ? 'pause' : 'play'} size={15} />
      <span className="medallion-label">{active ? 'Pause' : 'Narrate'}</span>
    </button>
  );
}

/**
 * Load one story's body, refetching whenever the selection changes.
 *
 * A story picked while an earlier fetch is still running must not be
 * overwritten by that earlier answer, so a stale response is dropped.
 */
function useStoryBody(storyId: string | null): { html: string; loading: boolean; error: string | null } {
  const [html, setHtml] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!storyId) {
      setHtml('');
      setError(null);
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);

    void (async () => {
      try {
        const res = await fetch('/api/story-body', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ storyId }),
        });
        const payload = (await res.json()) as { body?: string; error?: string };
        if (cancelled) return;
        if (!res.ok || payload.error) {
          throw new Error(payload.error ?? `Request failed (${res.status})`);
        }
        setHtml(payload.body ?? '');
      } catch (err) {
        if (!cancelled) {
          setHtml('');
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [storyId]);

  return { html, loading, error };
}

export function ReadStoryFileScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data   = useConsoleData();
  const reviewJobId = typeof ctx.reviewJobId === 'string' ? ctx.reviewJobId : null;

  /* Filter to active campaign, or show all if no campaign selected. An activity
     row that names a story outside that filter still has to open it. */
  const campaignStories = ctx.activeCampaignName
    ? storiesForCampaign(data, ctx.activeCampaignName)
    : data.stories;
  const pinnedId = typeof ctx.storyId === 'string' ? ctx.storyId : null;
  const stories = pinnedId && !campaignStories.some(s => s.id === pinnedId)
    ? data.stories
    : campaignStories;

  const pinnedIdx = pinnedId ? stories.findIndex(s => s.id === pinnedId) : -1;
  const activeIdx = pinnedIdx >= 0 ? pinnedIdx : (ctx.storyIdx ?? 0);

  const story   = stories[activeIdx] ?? null;
  const { html, loading, error } = useStoryBody(story?.id ?? null);

  const roster = React.useMemo(() => {
    const campaign = story?.campaign ?? ctx.activeCampaignName ?? null;
    const pcs = campaign ? charactersForCampaign(data, campaign) : [];
    const npcs = npcCharacters(data);
    return [...pcs, ...npcs].map(rosterPersonFromCharacter);
  }, [data, story?.campaign, ctx.activeCampaignName]);

  if (stories.length === 0) {
    return (
      <div className="screen-readstory">
        <div style={{ padding: 40, fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic' }}>
          {data.stories.length === 0
            ? 'No stories in Drupal yet. Sync from the Python CLI first.'
            : 'No stories for this campaign.'}
        </div>
      </div>
    );
  }

  return (
    <div className="screen-readstory">
      <aside className="reader-picker">
        <div className="reader-picker-head">
          <span className="reader-eyebrow">Stories</span>
          <h3>{ctx.activeCampaignName ?? 'All campaigns'}</h3>
        </div>
        <ol className="reader-picker-list">
          {stories.map((s, i) => (
            <li key={s.id}>
              <button
                className={`reader-picker-item${i === activeIdx ? ' active' : ''}`}
                onClick={() => setCtx({ ...ctx, storyIdx: i })}
              >
                <span className="picker-num">{String(s.storyNumber ?? i + 1).padStart(3, '0')}</span>
                <span className="picker-meta">
                  <strong>{s.title}</strong>
                  <span>{s.sessionDate ?? s.campaign ?? ''}</span>
                </span>
              </button>
            </li>
          ))}
        </ol>
      </aside>

      <article className="reader-page">
        {story && (
          <>
            <header className="reader-head">
              <span className="reader-chip">
                Story {String(story.storyNumber ?? activeIdx + 1).padStart(3, '0')}
              </span>
              <h1>{story.title}</h1>
              <div className="reader-meta-row">
                <span><Icon name="book" size={11} /> {story.campaign ?? ''}</span>
                {story.sessionDate && (
                  <>
                    <span className="dot-sep">·</span>
                    <span>{story.sessionDate}</span>
                  </>
                )}
              </div>
            </header>

            <div className="reader-body">
              {loading && <Spinner label="Unrolling" />}
              {error && <p className="arc-error">{error}</p>}
              {!loading && !error && html.trim() === '' && (
                <p style={{ fontStyle: 'italic', color: 'var(--ink-dim)' }}>
                  This story has no text yet.
                </p>
              )}
              {!loading && !error && <StoryScroll html={html} />}
            </div>

            <footer className="reader-foot">
              <div className="reader-foot-ornament">* · * · *</div>
              <div className="reader-actions">
                <NarrateMedallion />
                {story && (
                  <StoryImageWizard
                    key={story.id}
                    storyId={story.id}
                    storyTitle={story.title}
                    roster={roster}
                    presentIds={story.charactersPresentIds}
                    reviewJobId={reviewJobId}
                  />
                )}
                {activeIdx < stories.length - 1 && (
                  <button className="reader-action-btn" onClick={() => setCtx({ ...ctx, storyIdx: activeIdx + 1 })}>
                    <Icon name="chevron" size={12} /> Next: {stories[activeIdx + 1].title}
                  </button>
                )}
              </div>
            </footer>
          </>
        )}
      </article>
    </div>
  );
}
