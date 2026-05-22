/**
 * ToolsScreen — `tools/*` routes.
 *
 * Handles all Tools & Batch items via ctx._itemId:
 *   t-recent | t-search  → history list
 *   t-stats              → statistics view
 *   t-clear              → confirmation dialog
 *   t-level | t-item     → batch operation form
 *
 * Port of `ToolsHistoryScreen` + `BatchOpScreen` from screens-admin.jsx.
 * Uses real character data from ConsoleContext for batch targets.
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

/* ── History entries (static — from CLI history file, not Drupal) ── */
const HISTORY_ENTRIES = [
  { date: '2026-05-12', status: 'ok',   cmd: 'story generate --series fellowship --prompt "the cairn stirs"' },
  { date: '2026-05-12', status: 'ok',   cmd: 'characters consult aragorn --question "What does he fear most?"' },
  { date: '2026-05-12', status: 'fail', cmd: 'reindex --vector-db' },
  { date: '2026-05-11', status: 'ok',   cmd: 'session-results generate --story 003_weathertop' },
  { date: '2026-05-11', status: 'ok',   cmd: 'batch level-up --all +1' },
  { date: '2026-05-10', status: 'ok',   cmd: 'story add --series fellowship' },
  { date: '2026-05-09', status: 'ok',   cmd: 'npc validate' },
];

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
      <ol className="history-list" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
        {HISTORY_ENTRIES.map((e, i) => (
          <li key={i} className={`history-row status-${e.status}`}>
            <span className="history-date mono">{e.date}</span>
            <span className={`history-status status-${e.status}`}>{e.status === 'ok' ? '[OK]' : '[FAIL]'}</span>
            <code className="history-cmd">{e.cmd}</code>
            <button type="button" className="ghost-btn ghost-small">Re-run</button>
          </li>
        ))}
      </ol>
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
      <div className="stat-cards">
        {([
          ['Total commands', '1,284'],
          ['Sessions', '47'],
          ['Avg / session', '27.3'],
          ['Failures', '38', 'danger'],
        ] as Array<[string, string, string?]>).map(([l, v, tone]) => (
          <div key={l} className={`big-stat${tone ? ` tone-${tone}` : ''}`}>
            <span className="big-stat-val">{v}</span>
            <span className="big-stat-label">{l}</span>
          </div>
        ))}
      </div>
      <section className="stat-list-section">
        <h4>Most used commands</h4>
        <ul className="stat-bars">
          {([
            ['story generate', 184],
            ['consult', 142],
            ['session-results generate', 98],
            ['npc view', 72],
            ['reindex', 24],
          ] as Array<[string, number]>).map(([cmd, n]) => (
            <li key={cmd}>
              <span className="bar-label mono">{cmd}</span>
              <span className="bar-track"><span className="bar-fill" style={{ width: `${(n / 184) * 100}%` }} /></span>
              <span className="bar-val">{n}</span>
            </li>
          ))}
        </ul>
      </section>
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
        <p>This will permanently delete <strong>1,284 history entries</strong> across <strong>47 sessions</strong>.</p>
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
                Each character will roll for new HP using their class's hit die. ASIs at levels 4, 8, 12, 16, 19 will be queued for review.
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
