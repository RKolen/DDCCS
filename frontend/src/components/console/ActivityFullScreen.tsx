/**
 * Activity log full-screen overlay.
 *
 * Renders when the user clicks "Expand" on the right-rail activity drawer.
 * Items come from the parent (StatelyLedger) which receives them from the
 * live SSE/websocket channel — never from MENU_DATA.
 */

import * as React from 'react';
import type { ActivityItem } from './menuData';
import { Icon, ActivityRow } from './atoms';

interface ActivityFullScreenProps {
  items: ActivityItem[];
  onClose: () => void;
}

export function ActivityFullScreen({ items, onClose }: ActivityFullScreenProps): React.ReactElement {
  const running = items.filter(i => i.status === 'running');
  const failed  = items.filter(i => i.status === 'failed');
  const done    = items.filter(i => i.status === 'done');

  return (
    <div className="activity-fullscreen">
      <div className="activity-full-head">
        <div>
          <span className="reader-eyebrow">Activity log</span>
          <h2>All jobs</h2>
        </div>
        <div className="activity-full-stats">
          {running.length > 0 && <span className="pill pill-running">{running.length} running</span>}
          {failed.length  > 0 && <span className="pill pill-failed">{failed.length} failed</span>}
          {done.length    > 0 && <span className="pill pill-done">{done.length} done</span>}
        </div>
        <button type="button" className="ghost-btn" onClick={onClose}>
          <Icon name="close" size={12} /> Close
        </button>
      </div>

      <div className="activity-full-body">
        {items.length === 0 && (
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', fontSize: 14, padding: '16px 0' }}>
            No activity yet. Jobs dispatched from the console will appear here.
          </p>
        )}
        {running.length > 0 && (
          <section>
            <h4>Running</h4>
            {running.map((item, i) => <ActivityRow key={i} item={item} />)}
          </section>
        )}
        {failed.length > 0 && (
          <section>
            <h4>Failed</h4>
            {failed.map((item, i) => <ActivityRow key={i} item={item} />)}
          </section>
        )}
        {done.length > 0 && (
          <section>
            <h4>Completed</h4>
            {done.map((item, i) => <ActivityRow key={i} item={item} />)}
          </section>
        )}
      </div>
    </div>
  );
}
