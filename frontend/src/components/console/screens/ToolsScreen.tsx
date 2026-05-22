/**
 * ToolsScreen — `tools/*` routes.
 *
 * Handles all Tools & Batch items via ctx._itemId:
 *   t-recent | t-search  → history list
 *   t-stats              → statistics view
 *   t-clear              → confirmation dialog
 *   t-level | t-item     → batch operation form
 *
 * History data comes from the Python CLI backend (not available here yet).
 * Batch targets come from ConsoleContext (Drupal characters).
 *
 * Port of `ToolsHistoryScreen` + `BatchOpScreen` from screens-admin.jsx.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData, playerCharacters } from '../ConsoleContext';

/* ── Toggle atom (local) ── */
function Toggle({ defaultOn = false }: { defaultOn?: boolean }): React.ReactElement {
  const [on, setOn] = React.useState(defaultOn);
  return (
    <button
      type="button"
      className={`toggle${on ? ' on' : ''}`}
      onClick={() => setOn(v => !v)}
      aria-pressed={on}
    >
      <span className="toggle-knob" />
    </button>
  );
}

function HistoryView({ variant }: { variant: string }): React.ReactElement {
  return (
    <div className="screen-history">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">History</span>
          <h2>{variant === 't-search' ? 'Search history' : 'Recent commands'}</h2>
        </div>
        <div className="screen-head-actions">
          {variant === 't-search'
            ? <input className="screen-search" type="text" placeholder="Search history..." />
            : (
              <select className="ghost-btn">
                <option>Last 10</option>
                <option>Last 50</option>
                <option>All</option>
              </select>
            )}
          <button type="button" className="ghost-btn">Export</button>
        </div>
      </header>
      <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', fontSize: 14 }}>
        Command history is stored by the Python CLI backend. Connect the history API endpoint to populate this view.
      </p>
    </div>
  );
}

function StatsView(): React.ReactElement {
  return (
    <div className="screen-stats">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">History</span>
          <h2>History statistics</h2>
        </div>
      </header>
      <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', fontSize: 14 }}>
        Statistics are calculated from the Python CLI history file. Connect the history API endpoint to populate this view.
      </p>
    </div>
  );
}

function ClearView(): React.ReactElement {
  return (
    <div className="screen-confirm">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Tools</span>
          <h2>Clear command history</h2>
        </div>
      </header>
      <div className="confirm-card danger">
        <p>This will permanently delete all command history entries stored by the Python CLI backend.</p>
        <p>This cannot be undone. Consider exporting history first.</p>
        <div className="confirm-actions">
          <button type="button" className="ghost-btn">Export first</button>
          <button type="button" className="danger-btn">Clear all history</button>
        </div>
      </div>
    </div>
  );
}

function BatchView({ isLevel }: { isLevel: boolean }): React.ReactElement {
  const data = useConsoleData();
  const pcs  = playerCharacters(data);

  return (
    <div className="screen-batch">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Batch operation</span>
          <h2>{isLevel ? 'Batch level-up characters' : 'Batch add item to characters'}</h2>
        </div>
      </header>
      <div className="batch-body">
        <section className="batch-targets">
          <h4>Targets</h4>
          {pcs.length === 0 ? (
            <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', fontSize: 13 }}>
              No player characters in Drupal yet.
            </p>
          ) : (
            <>
              <ul className="batch-target-list">
                {pcs.map(c => (
                  <li key={c.id}>
                    <label className="batch-target">
                      <input type="checkbox" defaultChecked />
                      <span className="target-name">{c.title}</span>
                      <span className="target-meta">
                        {[c.characterClass, c.level != null ? `L${c.level}` : null].filter(Boolean).join(' · ')}
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
              <button type="button" className="ghost-btn ghost-small">Select all party members</button>
            </>
          )}
        </section>

        <section className="batch-config">
          <h4>Parameters</h4>
          {isLevel ? (
            <>
              <label className="form-row">
                <span>Levels to add</span>
                <input type="number" defaultValue="1" min="1" max="20" />
              </label>
              <p className="caption">
                Each character will roll for new HP using their class hit die. ASIs at levels 4, 8, 12, 16, 19 will be queued for review.
              </p>
            </>
          ) : (
            <>
              <label className="form-row">
                <span>Item name</span>
                <input type="text" placeholder="e.g. Potion of Healing" />
              </label>
              <label className="form-row">
                <span>Quantity</span>
                <input type="number" defaultValue="1" min="1" />
              </label>
              <label className="form-row toggle-row">
                <span>Identified</span>
                <Toggle defaultOn={true} />
              </label>
            </>
          )}
          <div className="batch-foot">
            <button type="button" className="ghost-btn">Dry run</button>
            <button type="button" className="primary-btn">
              Apply to {pcs.length} character{pcs.length !== 1 ? 's' : ''}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}

/* ── Main export ── */

export function ToolsScreen({ ctx }: ScreenProps): React.ReactElement {
  const itemId = ctx._itemId as string | undefined;

  if (itemId === 't-stats') return <StatsView />;
  if (itemId === 't-clear') return <ClearView />;
  if (itemId === 't-level') return <BatchView isLevel={true} />;
  if (itemId === 't-item')  return <BatchView isLevel={false} />;

  return <HistoryView variant={itemId ?? 't-recent'} />;
}
