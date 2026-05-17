/**
 * ReadStoryFileScreen — `read / r-story` default landing.
 *
 * Story list comes from ConsoleContext (real Drupal stories).
 * Filtered to the active campaign from ctx.activeCampaignName.
 * No mock fallbacks — empty state when Drupal has no stories.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData, storiesForCampaign } from '../ConsoleContext';
import { Icon, AiTag } from '../atoms';

function NarrateMedallion(): React.ReactElement {
  const [active, setActive] = React.useState(false);
  return (
    <button className={`big-medallion${active ? ' is-active' : ''}`} onClick={() => setActive(!active)}>
      <Icon name={active ? 'pause' : 'play'} size={15} />
      <span className="medallion-label">{active ? 'Pause' : 'Narrate'}</span>
    </button>
  );
}

function ImageGenMedallion(): React.ReactElement {
  const [running, setRunning] = React.useState(false);
  return (
    <button
      className={`big-medallion big-medallion--ai${running ? ' state-running' : ''}`}
      onClick={() => setRunning(r => !r)}
    >
      <AiTag label="" />
      <Icon name="image" size={14} />
      <span className="medallion-label">{running ? 'Generating...' : 'Generate image'}</span>
    </button>
  );
}

export function ReadStoryFileScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data   = useConsoleData();
  const activeIdx = ctx.storyIdx ?? 0;

  /* Filter to active campaign, or show all if no campaign selected */
  const allStories = ctx.activeCampaignName
    ? storiesForCampaign(data, ctx.activeCampaignName)
    : data.stories;

  const stories = allStories;
  const story   = stories[activeIdx] ?? null;

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
              <p style={{ fontStyle: 'italic', color: 'var(--ink-dim)' }}>
                Open the full story page to read the content.
              </p>
            </div>

            <footer className="reader-foot">
              <div className="reader-foot-ornament">* · * · *</div>
              <div className="reader-actions">
                <NarrateMedallion />
                <ImageGenMedallion />
                {story.path && (
                  <Link to={story.path} className="reader-action-btn" style={{ textDecoration: 'none' }}>
                    <Icon name="book" size={12} /> Read full story
                  </Link>
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
