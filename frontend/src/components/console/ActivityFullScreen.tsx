/**
 * Activity log full-screen overlay.
 *
 * Renders when the user clicks "Expand" on the right-rail activity
 * drawer. A larger view of all jobs in the `MENU_DATA.activityLog` channel.
 *
 * Canonical reference: /menu/variant-ledger.jsx + /menu/screens-admin.jsx
 */

import * as React from 'react';
import { MENU_DATA } from './menuData';
import { Icon, ActivityRow } from './atoms';

export function ActivityFullScreen({ onClose }: { onClose: () => void }): React.ReactElement {
  const log = MENU_DATA.activityLog;
  const running = log.filter(i => i.status === 'running');
  const done    = log.filter(i => i.status === 'done');
  const failed  = log.filter(i => i.status === 'failed');

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
        <button className="ghost-btn" onClick={onClose}>
          <Icon name="close" size={12} /> Close
        </button>
      </div>
      <div className="activity-full-body">
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
