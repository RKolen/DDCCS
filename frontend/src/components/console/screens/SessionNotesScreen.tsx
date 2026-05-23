/**
 * SessionNotesScreen — `stories/work-series` > s-notes.
 *
 * Three-column layout:
 *   Left  — sessions list (which session are we viewing notes for)
 *   Center — chronological tagged timeline + note composer
 *   Right  — tag counts, linked characters, linked items, AI assists
 *
 * Port of work-series/session-notes.jsx (standalone design)
 * and _canonical_source/ work-series session notes variant.
 *
 * Production wiring:
 *   - Session list from Drupal node--story ordered by field_order
 *   - Notes from node--session_note filtered by field_story reference
 *   - Note composer dispatches to POST /api/notes endpoint
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';
import { useConsoleData, storiesForCampaign } from '../ConsoleContext';

/* ─────────────────────────────────────────────────────────────
   Types
───────────────────────────────────────────────────────────── */

type NoteTag = 'combat' | 'RP' | 'lore' | 'loot' | 'check' | 'rule';

interface NoteEntry {
  id: string;
  t: string;
  sess: number;
  tag: NoteTag;
  author: string;
  text: string;
  linked?: { story: string; char?: string };
}

interface StorySummary {
  id: string;
  title: string;
  played: string;
  noteCount: number;
}

/* ─────────────────────────────────────────────────────────────
   Demo data (sourced from game_data/campaigns/Example_Campaign)
   Production reads from Drupal.
───────────────────────────────────────────────────────────── */

const DEMO_STORIES: StorySummary[] = [
  { id: '001', title: 'Prancing Pony Warning',   played: '8 weeks ago', noteCount: 3 },
  { id: '002', title: 'Mysteries of Trollshaws', played: '6 weeks ago', noteCount: 8 },
  { id: '003', title: 'The Bell of Vellishar',   played: '3 days ago',  noteCount: 6 },
];

const DEMO_NOTES: NoteEntry[] = [
  {
    id: 'n01', t: '14:02', sess: 2, tag: 'lore', author: 'DM',
    text: 'Trollshaws — old place. Frodo recalls whispers of "ancient powers." Lay the foreshadowing thicker than last session — tie back to Bree letter.',
    linked: { story: '002', char: 'Frodo' },
  },
  {
    id: 'n02', t: '14:18', sess: 2, tag: 'check', author: 'Gandalf',
    text: 'Cast Detect Magic (1st-level, ritual). Subtle ripples deeper in the forest — agreed it\'s a homing pulse, not local. No spell slot spent.',
    linked: { story: '002', char: 'Gandalf' },
  },
  {
    id: 'n03', t: '14:51', sess: 2, tag: 'RP', author: 'DM',
    text: 'Aragorn reassuring touch on Frodo\'s shoulder — first real warmth between them since Bree. Note this for character arc.',
    linked: { story: '002', char: 'Aragorn' },
  },
  {
    id: 'n04', t: '15:30', sess: 2, tag: 'combat', author: 'DM',
    text: 'Goblin ambush — initiative order: G(scouts) 19, Aragorn 17, Gandalf 12, Frodo 11. Surprise round granted, archers won it.',
    linked: { story: '002' },
  },
  {
    id: 'n05', t: '15:38', sess: 2, tag: 'combat', author: 'Gandalf',
    text: 'Burned a 3rd-level slot on Fireball — six goblins crowded together, easy call. DM ruled DC 15 Dex.',
    linked: { story: '002', char: 'Gandalf' },
  },
  {
    id: 'n06', t: '15:46', sess: 2, tag: 'combat', author: 'Frodo',
    text: 'Natural 20 with Sting against the flanker — sneak attack triggered. Total 11 damage, instakill.',
    linked: { story: '002', char: 'Frodo' },
  },
  {
    id: 'n07', t: '16:04', sess: 2, tag: 'loot', author: 'DM',
    text: 'Looted goblin captain — bone whistle (unknown function), 14 gp, crude map fragment pointing east toward Weathertop.',
    linked: { story: '002' },
  },
  {
    id: 'n08', t: '16:22', sess: 2, tag: 'lore', author: 'DM',
    text: 'Map fragment — players noticed the rune in the corner matches the seal on the Bree letter. Plant pays off next session.',
    linked: { story: '002' },
  },
];

const NOTE_TAGS: NoteTag[] = ['combat', 'RP', 'lore', 'loot', 'check', 'rule'];

/* ─────────────────────────────────────────────────────────────
   SessionNotesScreen
───────────────────────────────────────────────────────────── */

export function SessionNotesScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data      = useConsoleData();
  const campaign  = (ctx.activeCampaignName as string | null | undefined) ?? data.campaigns[0]?.name ?? null;
  const stories   = campaign ? storiesForCampaign(data, campaign) : data.stories;

  const sessionList: StorySummary[] = stories.length > 0
    ? stories.map((s, i) => ({
        id: String(s.storyNumber ?? i + 1).padStart(3, '0'),
        title: s.title,
        played: '',
        noteCount: 0,
      }))
    : DEMO_STORIES;

  const [activeSessId, setActiveSessId]   = React.useState<string>(sessionList[1]?.id ?? sessionList[0]?.id ?? '002');
  const [activeTags, setActiveTags]       = React.useState<NoteTag[]>(NOTE_TAGS.slice());
  const [composerText, setComposerText]   = React.useState('');
  const [composerTag, setComposerTag]     = React.useState<NoteTag>('RP');

  const activeStory = sessionList.find(s => s.id === activeSessId) ?? sessionList[0];
  const notes = DEMO_NOTES.filter(n => String(n.sess) === activeSessId.replace(/^0+/, '') || activeSessId === '002');

  const toggleTag = (t: NoteTag): void => {
    setActiveTags(curr =>
      curr.includes(t) ? curr.filter(x => x !== t) : [...curr, t],
    );
  };

  const filtered = notes.filter(n => activeTags.includes(n.tag));

  const tagCounts = NOTE_TAGS.map(t => ({
    tag: t,
    count: notes.filter(n => n.tag === t).length,
  }));

  const linkedChars = (() => {
    const map: Record<string, number> = {};
    notes.forEach(n => {
      if (n.linked?.char !== undefined) {
        map[n.linked.char] = (map[n.linked.char] ?? 0) + 1;
      }
    });
    return Object.entries(map).map(([name, count]) => ({ name, count }));
  })();

  const goBack = (): void => {
    setCtx({ ...ctx, workSeriesAction: null });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <header className="ws-notes-head">
        <div>
          <span className="ws-eyebrow">Session notes &middot; {campaign ?? 'Campaign'}</span>
          <h2 className="ws-title" style={{ fontSize: 22 }}>
            {activeStory !== undefined ? `Story ${activeStory.id} — ${activeStory.title}` : 'Notes'}
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: 'var(--color-text-tertiary)', marginLeft: 12, fontWeight: 400 }}>
              {notes.length} notes
            </span>
          </h2>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button type="button" className="action-back" onClick={goBack} style={{ marginRight: 4 }}>
            <Icon name="chevronLeft" size={11} /> Back
          </button>
          <button type="button" className="ghost-btn">Export</button>
          <button type="button" className="ghost-btn">
            <Icon name="sparkle" size={11} /> Summarize as recap
          </button>
          <button type="button" className="primary-btn">
            <Icon name="plus" size={11} /> Add note
          </button>
        </div>
      </header>

      <div className="ws-notes-grid">
        <aside className="ws-notes-sessions">
          <h4>Sessions</h4>
          {sessionList.map(s => (
            <div
              key={s.id}
              className={`ws-notes-sess-row${s.id === activeSessId ? ' active' : ''}`}
              onClick={() => { setActiveSessId(s.id); }}
              role="button"
              tabIndex={0}
              onKeyDown={e => { if (e.key === 'Enter') setActiveSessId(s.id); }}
            >
              <span className="num">SESSION {s.id}</span>
              <strong>{s.title}</strong>
              {s.noteCount > 0 && (
                <span className="info">{s.played} &middot; {s.noteCount} notes</span>
              )}
            </div>
          ))}
          <div style={{ padding: '14px 16px 0', borderTop: '1px solid var(--color-gold-rule)', marginTop: 12 }}>
            <button type="button" className="ghost-btn" style={{ width: '100%', justifyContent: 'center' }}>
              <Icon name="plus" size={10} /> Begin next session
            </button>
          </div>
        </aside>

        <section className="ws-notes-stream">
          <div className="ws-notes-filters">
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 10, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'var(--color-text-tertiary)', marginRight: 6 }}>
              Filter
            </span>
            {NOTE_TAGS.map(t => (
              <span
                key={t}
                className={`ws-tag-chip${activeTags.includes(t) ? ' active' : ''}`}
                onClick={() => { toggleTag(t); }}
                role="checkbox"
                aria-checked={activeTags.includes(t)}
                tabIndex={0}
                onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') toggleTag(t); }}
              >
                <span className={`swatch tag-${t}`} />
                {t}
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9.5, color: 'var(--color-text-tertiary)', marginLeft: 2 }}>
                  {notes.filter(n => n.tag === t).length}
                </span>
              </span>
            ))}
            <span className="ws-spacer" />
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--color-text-tertiary)' }}>
              showing {filtered.length}/{notes.length}
            </span>
          </div>

          <div className="ws-note-timeline">
            {filtered.length === 0 && (
              <p style={{ padding: '20px 0', fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', fontSize: 13 }}>
                No notes match the active tag filters.
              </p>
            )}
            {filtered.map(n => (
              <div key={n.id} className={`ws-note-row tag-${n.tag}`}>
                <div className="ws-note-header">
                  <span className="t">{n.t}</span>
                  <span className="author">{n.author}</span>
                  <span className={`tag-pill tag-${n.tag}`}>{n.tag}</span>
                </div>
                <div className="ws-note-body">
                  {n.text}
                  {n.linked !== undefined && (
                    <div className="linked">
                      <span><span className="pin">&#8618;</span> story <span className="ws-mono">{n.linked.story}</span></span>
                      {n.linked.char !== undefined && (
                        <span><span className="pin">&#8618;</span> {n.linked.char}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="ws-note-composer">
            <div className="ws-note-composer-card">
              <textarea
                rows={2}
                placeholder="Add a note about this session — what just happened, what the players said, what to remember next time..."
                value={composerText}
                onChange={e => { setComposerText(e.target.value); }}
              />
              <div className="ws-note-composer-bottom">
                <div className="ws-note-composer-tags">
                  {NOTE_TAGS.map(t => (
                    <span
                      key={t}
                      className={`ws-tag-chip${t === composerTag ? ' active' : ''}`}
                      onClick={() => { setComposerTag(t); }}
                      role="radio"
                      aria-checked={t === composerTag}
                      tabIndex={0}
                      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') setComposerTag(t); }}
                    >
                      <span className={`swatch tag-${t}`} />{t}
                    </span>
                  ))}
                </div>
                <span className="help">Cmd+Enter to save</span>
                <button
                  type="button"
                  className="primary-btn"
                  disabled={composerText.trim() === ''}
                  onClick={() => { setComposerText(''); }}
                  style={{ fontSize: 12, padding: '4px 12px' }}
                >
                  Save note
                </button>
              </div>
            </div>
          </div>
        </section>

        <aside className="ws-notes-side">
          <div>
            <h4>By tag</h4>
            {tagCounts.map(({ tag, count }) => (
              <div key={tag} className="ws-notes-tagcount">
                <div className="left">
                  <span className="swatch" style={{ background: `var(--tag-${tag}, var(--color-gold-muted))` }} />
                  <span style={{ textTransform: 'lowercase' }}>{tag}</span>
                </div>
                <span style={{ color: count > 0 ? 'var(--color-text-primary)' : 'var(--color-text-disabled)' }}>
                  {count}
                </span>
              </div>
            ))}
          </div>

          {linkedChars.length > 0 && (
            <div>
              <h4>Linked characters</h4>
              <ul className="ws-linked-list">
                {linkedChars.map(c => (
                  <li key={c.name}>
                    <strong>{c.name}</strong>
                    <span className="n">{c.count} {c.count === 1 ? 'note' : 'notes'}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div style={{ marginTop: 'auto', paddingTop: 14, borderTop: '1px solid var(--color-gold-rule)' }}>
            <h4>AI assists</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              <button type="button" className="ghost-btn" style={{ justifyContent: 'flex-start', fontSize: 12 }}>
                <Icon name="sparkle" size={9} /> Extract notes from story
              </button>
              <button type="button" className="ghost-btn" style={{ justifyContent: 'flex-start', fontSize: 12 }}>
                <Icon name="sparkle" size={9} /> Suggest missing combat notes
              </button>
              <button type="button" className="ghost-btn" style={{ justifyContent: 'flex-start', fontSize: 12 }}>
                <Icon name="sparkle" size={9} /> Tag untagged notes
              </button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
