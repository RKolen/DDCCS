/**
 * Activity log full-screen overlay.
 *
 * Renders when the user clicks "Expand" on the right-rail activity drawer.
 * Items come from the parent (StatelyLedger), which polls the host job queue —
 * never from MENU_DATA.
 *
 * Rows are grouped by what they ask of the operator, so a finished render that
 * has not been accepted yet leads rather than hiding among the completed ones.
 */

import * as React from 'react';
import type { ActivityItem } from './menuData';
import { Icon, ActivityRow } from './atoms';

interface ActivityFullScreenProps {
  items: ActivityItem[];
  onClose: () => void;
  /** Opens the screen a row points at, so a finished job can be reviewed. */
  onOpen?: (item: ActivityItem) => void;
  /** Puts a stalled job back on the queue. */
  onRequeue?: (item: ActivityItem) => void;
}

export function ActivityFullScreen({
  items, onClose, onOpen, onRequeue,
}: ActivityFullScreenProps): React.ReactElement {
  const running = items.filter(i => i.status === 'running');
  const queued  = items.filter(i => i.status === 'queued');
  const failed  = items.filter(i => i.status === 'failed');
  // A row waiting on a decision is listed under "Waiting on you" only, so the
  // one thing that still needs doing does not read as already finished.
  const done    = items.filter(i => i.status === 'done' && !i.needsReview);
  const review  = items.filter(i => i.needsReview);

  return (
    <div className="activity-fullscreen">
      <div className="activity-full-head">
        <div>
          <span className="reader-eyebrow">Activity log</span>
          <h2>All jobs</h2>
        </div>
        <div className="activity-full-stats">
          {running.length > 0 && <span className="pill pill-running">{running.length} running</span>}
          {queued.length  > 0 && <span className="pill pill-queued">{queued.length} queued</span>}
          {review.length  > 0 && <span className="pill pill-review">{review.length} to review</span>}
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
        {review.length > 0 && (
          <section>
            <h4>Waiting on you</h4>
            {review.map((item, i) => (
              <ActivityRow key={item.jobId ?? i} item={item} onOpen={onOpen} onRequeue={onRequeue} />
            ))}
          </section>
        )}
        {running.length > 0 && (
          <section>
            <h4>Running</h4>
            {running.map((item, i) => (
              <ActivityRow key={item.jobId ?? i} item={item} onOpen={onOpen} onRequeue={onRequeue} />
            ))}
          </section>
        )}
        {queued.length > 0 && (
          <section>
            <h4>Queued</h4>
            {queued.map((item, i) => (
              <ActivityRow key={item.jobId ?? i} item={item} onOpen={onOpen} onRequeue={onRequeue} />
            ))}
          </section>
        )}
        {failed.length > 0 && (
          <section>
            <h4>Failed</h4>
            {failed.map((item, i) => (
              <ActivityRow key={item.jobId ?? i} item={item} onOpen={onOpen} onRequeue={onRequeue} />
            ))}
          </section>
        )}
        {done.length > 0 && (
          <section>
            <h4>Completed</h4>
            {done.map((item, i) => (
              <ActivityRow key={item.jobId ?? i} item={item} onOpen={onOpen} onRequeue={onRequeue} />
            ))}
          </section>
        )}
      </div>
    </div>
  );
}
