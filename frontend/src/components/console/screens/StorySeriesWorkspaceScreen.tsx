/**
 * StorySeriesWorkspaceScreen — `stories/work-series`.
 *
 * Shows the active campaign's story list on the left and an action grid
 * on the right. Stories come from ConsoleContext (Drupal). The action
 * groups are static (they're the CLI's surface, not Drupal data).
 *
 * Port of `StorySeriesWorkspaceScreen` from screens-content.jsx.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData, storiesForCampaign } from '../ConsoleContext';
import { Icon, AiTag, SlowTag } from '../atoms';

interface ActionItem {
  id: string;
  label: string;
  ai?: boolean;
  slow?: boolean;
}

interface ActionGroup {
  title: string;
  items: ActionItem[];
}

const ACTION_GROUPS: ActionGroup[] = [
  {
    title: 'Create',
    items: [
      { id: 's-add', label: 'Add new story', ai: true },
    ],
  },
  {
    title: 'Generate',
    items: [
      { id: 's-session',  label: 'Session results',        ai: true },
      { id: 's-chardev',  label: 'Character development',  ai: true },
      { id: 's-combat',   label: 'Combat to narrative',    ai: true },
    ],
  },
  {
    title: 'Consult',
    items: [
      { id: 's-dc',      label: 'DC suggestions',       ai: true },
      { id: 's-dm',      label: 'DM narrative hints',   ai: true },
      { id: 's-suggest', label: 'AI story suggestions', ai: true },
    ],
  },
  {
    title: 'Analyze',
    items: [
      { id: 's-analyze',    label: 'Analyze single story',  ai: true },
      { id: 's-story-anal', label: 'Series consistency',    ai: true, slow: true },
      { id: 's-char-anal',  label: 'Character analysis',    ai: true, slow: true },
    ],
  },
  {
    title: 'Curate',
    items: [
      { id: 's-view',  label: 'View story details' },
      { id: 's-amend', label: 'Amend story actions' },
      { id: 's-notes', label: 'Session notes' },
    ],
  },
];

export function StorySeriesWorkspaceScreen({ ctx }: ScreenProps): React.ReactElement {
  const data         = useConsoleData();
  const campaignName = (ctx.activeCampaignName as string | null | undefined) ?? data.campaigns[0]?.name ?? null;

  const stories = campaignName
    ? storiesForCampaign(data, campaignName)
    : data.stories;

  const partySize = (() => {
    const camp = data.campaigns.find(c => c.name === campaignName);
    return camp?.currentPartyIds?.length ?? null;
  })();

  return (
    <div className="screen-series">
      <header className="series-head">
        <div>
          <span className="reader-eyebrow">Series</span>
          <h2>{campaignName ?? 'No campaign selected'}</h2>
          {(stories.length > 0 || partySize != null) && (
            <div className="series-stats">
              <span><Icon name="scroll" size={12} /> {stories.length} {stories.length === 1 ? 'story' : 'stories'}</span>
              {partySize != null && (
                <>
                  <span className="dot-sep">·</span>
                  <span><Icon name="char" size={12} /> {partySize} party members</span>
                </>
              )}
            </div>
          )}
        </div>
        <div className="series-head-actions">
          <button type="button" className="ghost-btn">Switch series</button>
          <button type="button" className="primary-btn">
            <Icon name="plus" size={11} /><Icon name="sparkle" size={11} /> New story
          </button>
        </div>
      </header>

      <div className="series-grid">
        <aside className="series-stories">
          <div className="series-stories-head">
            <h4>Stories in series</h4>
            <span className="series-stories-count">{stories.length}</span>
          </div>
          {stories.length === 0 ? (
            <p style={{ padding: '16px 18px', fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', fontSize: 13, margin: 0 }}>
              {data.stories.length === 0
                ? 'No stories in Drupal yet. Sync from the Python CLI first.'
                : 'No stories for this campaign.'}
            </p>
          ) : (
            <ol className="series-story-list">
              {stories.map((s, i) => (
                <li key={s.id}>
                  <button
                    type="button"
                    className={`series-story${i === stories.length - 1 ? ' is-latest' : ''}`}
                  >
                    <span className="story-numeral">
                      {String(s.storyNumber ?? i + 1).padStart(3, '0')}
                    </span>
                    <span className="story-filename">{s.title}</span>
                    {i === stories.length - 1 && <span className="latest-tag">latest</span>}
                  </button>
                </li>
              ))}
            </ol>
          )}
        </aside>

        <section className="series-actions">
          {ACTION_GROUPS.map(g => (
            <div key={g.title} className="action-group">
              <h5 className="action-group-title">{g.title}</h5>
              <div className="action-group-cards">
                {g.items.map(it => (
                  <button key={it.id} type="button" className="series-action-card">
                    <span className="series-action-label">
                      {it.label}
                      {it.ai && <AiTag />}
                      {it.slow && <SlowTag />}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}
