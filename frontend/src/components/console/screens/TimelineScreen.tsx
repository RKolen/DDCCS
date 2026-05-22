/**
 * TimelineScreen — `stories/timeline`.
 *
 * Timeline events are in-world dates attached to story nodes in Drupal.
 * Until that field is available in the GraphQL schema, shows an empty
 * state that points to the data source.
 *
 * Port of `TimelineScreen` from screens-content.jsx.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';

export function TimelineScreen({ ctx }: ScreenProps): React.ReactElement {
  const campaignName = ctx.activeCampaignName as string | null | undefined;

  return (
    <div className="screen-timeline">
      <header className="timeline-head">
        <div>
          <span className="reader-eyebrow">Campaign timeline</span>
          <h2>{campaignName ?? 'Timeline'}</h2>
        </div>
        <div className="timeline-actions">
          <button type="button" className="ghost-btn">Filter</button>
          <button type="button" className="ghost-btn">Add event</button>
        </div>
      </header>

      <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', fontSize: 14 }}>
        Timeline events are stored as in-world dates on story nodes in Drupal.
        Enable the <code>field_in_world_date</code> field on the Story content type and sync to populate this view.
      </p>
    </div>
  );
}
