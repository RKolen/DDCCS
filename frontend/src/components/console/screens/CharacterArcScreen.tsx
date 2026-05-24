/**
 * CharacterArcScreen — `characters/arc` and arc sub-screens.
 *
 * Sub-screens dispatched via ctx.arcSubAction:
 *   arc-summary  → character arc summary (metrics, timeline)
 *   arc-analyze  → AI analysis — 3-phase: setup → stream → result
 *   arc-overview → campaign-wide arc comparison
 *   arc-export   → export arc report to file
 *   (none)       → arc hub — all characters at a glance
 *
 * All character/story data comes from ConsoleContext (Drupal).
 * Arc analysis output (direction, stage, metrics, etc.) is produced by
 * the Python CLI's arc analysis commands and is not yet in Drupal; screens
 * show an empty state until analysis has been run.
 *
 * Canonical CSS: src/styles/arcs.css
 * Canonical atoms: _canonical_source/arc-atoms.jsx
 * Canonical data shapes: _canonical_source/arc-data.jsx
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import {
  useConsoleData,
  playerCharacters,
  charactersForCampaign,
  storiesForCampaign,
  type DrupalCharacter,
  type DrupalStory,
} from '../ConsoleContext';
import { AiTag, SlowTag } from '../atoms';

/* ────────────────────────────────────────────────────────────
   Arc type definitions (output of the Python arc analysis CLI)
   ──────────────────────────────────────────────────────────── */

type ArcDirection = 'growth' | 'decline' | 'stasis' | 'fluctuation' | 'transformation';
type ArcStage =
  | 'introduction' | 'establishment' | 'challenge' | 'development'
  | 'climax' | 'resolution' | 'aftermath';

interface ArcMetric {
  label: string;
  series: number[];
  direction: ArcDirection;
  obs: string;
}

interface ArcRelationship {
  target: string;
  type: string;
  strength: number;
  trust: number;
  note: string;
}

interface ArcGoal {
  description: string;
  status: 'active' | 'dormant' | 'completed';
  progress: number;
}

interface CharacterArcData {
  direction: ArcDirection;
  stage: ArcStage;
  summary: string;
  storiesAnalyzed: number;
  lastAnalyzed: string;
  metrics: Record<string, ArcMetric>;
  relationships: ArcRelationship[];
  goals: ArcGoal[];
}

/* ────────────────────────────────────────────────────────────
   Small atoms (match arcs.css class contracts)
   ──────────────────────────────────────────────────────────── */

const DIR_META: Record<ArcDirection, { label: string; arrow: string }> = {
  growth:         { label: 'Growth',         arrow: '↗' },
  decline:        { label: 'Decline',        arrow: '↘' },
  stasis:         { label: 'Stasis',         arrow: '→' },
  fluctuation:    { label: 'Flux',           arrow: '↕' },
  transformation: { label: 'Transformation', arrow: '⇧' },
};

function ArcDirBadge({ direction }: { direction: ArcDirection }): React.ReactElement {
  const { label, arrow } = DIR_META[direction];
  return (
    <span className={`arc-dir ${direction}`}>
      <span className="arrow">{arrow}</span>
      {label}
    </span>
  );
}

const STAGES: ArcStage[] = [
  'introduction', 'establishment', 'challenge', 'development',
  'climax', 'resolution', 'aftermath',
];

function ArcStageTrack({ stage }: { stage: ArcStage }): React.ReactElement {
  const idx = STAGES.indexOf(stage);
  return (
    <span className="arc-stage">
      {STAGES.map((s, i) => (
        <React.Fragment key={s}>
          <span className={`pip${i < idx ? ' done' : i === idx ? ' current' : ''}`} />
          {i < STAGES.length - 1 && (
            <span className={`pip-bar${i < idx ? ' done' : ''}`} />
          )}
        </React.Fragment>
      ))}
      <span className="arc-stage-label">{stage}</span>
    </span>
  );
}

function ArcSpark({
  series,
  direction,
  width = 80,
  height = 24,
}: {
  series: number[];
  direction: ArcDirection;
  width?: number;
  height?: number;
}): React.ReactElement {
  if (series.length < 2) {
    return <svg className={`arc-spark ${direction}`} width={width} height={height} />;
  }
  const min = Math.min(...series);
  const max = Math.max(...series);
  const range = Math.max(max - min, 0.05);
  const pad = 3;
  const w = width - pad * 2;
  const h = height - pad * 2;
  const pts: [number, number][] = series.map((v, i) => [
    pad + (series.length === 1 ? 0 : (i * w) / (series.length - 1)),
    pad + h - ((v - min) / range) * h,
  ]);
  const linePath = pts
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`)
    .join(' ');
  const areaPath = `${linePath} L ${pts[pts.length - 1][0].toFixed(1)} ${height - pad} L ${pts[0][0].toFixed(1)} ${height - pad} Z`;
  const [lx, ly] = pts[pts.length - 1];
  return (
    <svg
      className={`arc-spark ${direction}`}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
    >
      <path className="area" d={areaPath} />
      <path className="line" d={linePath} />
      <circle className="end-dot" cx={lx} cy={ly} r={2} />
    </svg>
  );
}

function ArcPortrait({
  name,
  size = 'md',
}: {
  name: string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
}): React.ReactElement {
  const initials = name
    .split(' ')
    .map(w => w[0] ?? '')
    .join('')
    .slice(0, 2)
    .toUpperCase();
  const cls = `arc-portrait${size !== 'md' ? ` ${size}` : ''}`;
  return <div className={cls}>{initials}</div>;
}

/* ────────────────────────────────────────────────────────────
   Phase rail (reused across analyze sub-screens)
   ──────────────────────────────────────────────────────────── */

type AnalyzePhase = 'setup' | 'running' | 'result';

function ArcPhaseRail({ phase }: { phase: AnalyzePhase }): React.ReactElement {
  const steps: { id: AnalyzePhase; label: string }[] = [
    { id: 'setup',   label: 'Configure' },
    { id: 'running', label: 'Analysing' },
    { id: 'result',  label: 'Review' },
  ];
  const currentIdx = steps.findIndex(s => s.id === phase);
  return (
    <div className="arc-phase-rail">
      {steps.map((s, i) => {
        const done    = i < currentIdx;
        const current = i === currentIdx;
        return (
          <React.Fragment key={s.id}>
            <span className={`step${done ? ' done' : current ? ' current' : ''}`}>
              <span className="pip">{done ? '✓' : i + 1}</span>
              {s.label}
            </span>
            {i < steps.length - 1 && (
              <span className={`rule${done ? ' done' : ''}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   1. ArcHub — all characters at a glance
   ──────────────────────────────────────────────────────────── */

interface SubScreenProps extends ScreenProps {
  characters: DrupalCharacter[];
  stories:    DrupalStory[];
}

function ArcHub({ ctx, setCtx, characters }: SubScreenProps): React.ReactElement {
  return (
    <div className="arc-action">
      <div className="arc-hub-head">
        <div>
          <span className="arc-eyebrow">Character Arc Analysis</span>
          <h2>
            Arc Hub
            {' '}
            <AiTag />
          </h2>
          <p className="blurb">
            AI-powered character arc tracking. Select a character to view their arc
            summary or run a new analysis across their story appearances.
          </p>
        </div>
        <div className="actions">
          <button
            type="button"
            className="arc-btn"
            onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-overview' })}
          >
            Campaign overview
          </button>
          <button
            type="button"
            className="arc-btn primary"
            onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-analyze' })}
          >
            Analyze all
            {' '}
            <AiTag />
            {' '}
            <SlowTag />
          </button>
        </div>
      </div>

      <div className="arc-hub-toolbar">
        <span className="stat">
          <strong>{characters.length}</strong>
          {' '}
          characters
        </span>
        <span className="arc-dot-sep">·</span>
        <span className="stat">
          <strong>0</strong>
          {' '}
          analysed
        </span>
        <span className="arc-dot-sep">·</span>
        <span>Run arc analysis to populate development data</span>
        <span className="grow" />
        <button
          type="button"
          className="arc-btn small"
          onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-export' })}
        >
          Export
        </button>
      </div>

      <div className="arc-hub-grid">
        {characters.length === 0 ? (
          <p style={{ gridColumn: '1/-1', fontStyle: 'italic', color: 'var(--ink-dim)', padding: 24 }}>
            No characters found for the active campaign. Sync from the Python CLI first.
          </p>
        ) : (
          characters.map(char => (
            <button
              key={char.id}
              type="button"
              className="arc-hub-card stale"
              onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-summary', arcCharId: char.id })}
            >
              <ArcPortrait name={char.title} />
              <div className="arc-hub-card-body">
                <div className="name-row">
                  <span className="name">{char.title}</span>
                  {char.nickname && <span className="role">{char.nickname}</span>}
                </div>
                <p className="summary">
                  {char.characterClass
                    ? `${char.characterClass} · Level ${char.level ?? '?'}`
                    : `Level ${char.level ?? '?'}`}
                  {char.campaign ? ` · ${char.campaign}` : ''}
                </p>
                <div className="arc-hub-card-foot">
                  <span className="stories">
                    Not yet analysed
                  </span>
                  <span className="grow" />
                  <button
                    type="button"
                    className="arc-btn small primary"
                    onClick={e => {
                      e.stopPropagation();
                      setCtx({ ...ctx, arcSubAction: 'arc-analyze', arcCharId: char.id });
                    }}
                  >
                    Analyse
                    {' '}
                    <AiTag />
                  </button>
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   2. ArcSummary — one character's arc detail
   ──────────────────────────────────────────────────────────── */

function ArcSummary({ ctx, setCtx, characters }: SubScreenProps): React.ReactElement {
  const charId = ctx.arcCharId as string | undefined;
  const char   = characters.find(c => c.id === charId) ?? characters[0] ?? null;

  const arcData = null as CharacterArcData | null;

  return (
    <div className="arc-action">
      <div className="arc-sum-head">
        {char ? <ArcPortrait name={char.title} size="lg" /> : <div className="arc-portrait lg" />}

        <div className="identity">
          <span className="arc-eyebrow">Character Arc</span>
          <h2>{char?.title ?? 'No character selected'}</h2>
          <div className="role">
            {char?.characterClass && <em>{char.characterClass}</em>}
            {char?.level != null && ` · Level ${char.level}`}
            {char?.pronouns && ` · ${char.pronouns}`}
          </div>
          {arcData ? (
            <div className="arc-state">
              <ArcDirBadge direction={arcData.direction} />
              <ArcStageTrack stage={arcData.stage} />
            </div>
          ) : (
            <div style={{ marginTop: 10, fontStyle: 'italic', color: 'var(--ink-dim)', fontSize: 13 }}>
              No arc analysis data yet. Run an analysis to generate arc metrics.
            </div>
          )}
        </div>

        <div className="actions">
          <button
            type="button"
            className="arc-btn primary"
            onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-analyze', arcCharId: char?.id })}
          >
            Analyse arc
            {' '}
            <AiTag />
          </button>
          <button
            type="button"
            className="arc-btn"
            onClick={() => setCtx({ ...ctx, arcSubAction: undefined })}
          >
            Back to hub
          </button>
        </div>
      </div>

      {arcData ? (
        <>
          <div className="arc-sum-summary">
            <h4>Arc summary</h4>
            <p>{arcData.summary}</p>
          </div>
          <div className="arc-sum-grid">
            <div className="arc-sum-section">
              <h4>
                Metrics
                <span className="meta">
                  {arcData.storiesAnalyzed}
                  {' '}
                  stories · last
                  {' '}
                  {arcData.lastAnalyzed}
                </span>
              </h4>
              <div className="arc-dim-grid">
                {Object.values(arcData.metrics).map(m => {
                  const last  = m.series[m.series.length - 1] ?? 0;
                  const first = m.series[0] ?? 0;
                  const delta = last - first;
                  const deltaClass = delta > 0.1 ? 'up' : delta < -0.1 ? 'down' : 'flat';
                  return (
                    <div key={m.label} className="arc-dim-card">
                      <div>
                        <div className="metric">{m.label}</div>
                        <div className="obs">{m.obs}</div>
                      </div>
                      <div className="spark-block">
                        <ArcSpark series={m.series} direction={m.direction} />
                        <span className={`spark-delta ${deltaClass}`}>
                          {delta > 0 ? '+' : ''}
                          {delta.toFixed(1)}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="arc-sum-section" style={{ marginBottom: 14 }}>
                <h4>Goals</h4>
                {arcData.goals.map((g, i) => (
                  <div key={i} className="arc-goal">
                    <div className="top">
                      <span className="desc">{g.description}</span>
                      <span className={`status ${g.status}`}>{g.status}</span>
                    </div>
                    <div className="progress-row">
                      <div className="progress-bar">
                        <i style={{ width: `${g.progress}%` }} />
                      </div>
                      <span>{g.progress}%</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="arc-sum-section">
                <h4>Relationships</h4>
                <ul className="arc-rel-list">
                  {arcData.relationships.map((r, i) => (
                    <li key={i} className="arc-rel-row">
                      <ArcPortrait name={r.target} size="xs" />
                      <div>
                        <span className="who">{r.target}</span>
                        <span className="type">{r.type}</span>
                        <div className="note">{r.note}</div>
                      </div>
                      <div className="meters">
                        <span className="meter">
                          <span className="lbl">Bond</span>
                          <span className="bar">
                            <i style={{ width: `${r.strength * 10}%` }} />
                          </span>
                        </span>
                        <span className="meter">
                          <span className="lbl">Trust</span>
                          <span className="bar">
                            <i style={{ width: `${r.trust * 10}%` }} />
                          </span>
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div style={{ padding: 24, display: 'flex', gap: 10 }}>
          {characters.length > 1 && (
            <div>
              <span
                className="arc-eyebrow"
                style={{ display: 'block', marginBottom: 8 }}
              >
                Switch character
              </span>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {characters.map(c => (
                  <button
                    key={c.id}
                    type="button"
                    className={`arc-btn small${c.id === char?.id ? ' primary' : ''}`}
                    onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-summary', arcCharId: c.id })}
                  >
                    {c.title}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   3. ArcAnalyze — 3-phase AI analysis
   ──────────────────────────────────────────────────────────── */

function ArcAnalyze({ ctx, setCtx, characters, stories }: SubScreenProps): React.ReactElement {
  const charId = ctx.arcCharId as string | undefined;
  const char   = characters.find(c => c.id === charId) ?? characters[0] ?? null;

  const [phase, setPhase]       = React.useState<AnalyzePhase>('setup');
  const [progress, setProgress] = React.useState(0);
  const [selectedChar, setSelectedChar] = React.useState(char?.id ?? '');
  const [selectedStory, setSelectedStory] = React.useState('');

  React.useEffect(() => {
    if (phase !== 'running') return;
    let cancelled = false;
    const tick = (): void => {
      setProgress(p => {
        if (cancelled || p >= 1) return p;
        const next = p + 0.025;
        if (next >= 1) {
          setTimeout(() => { if (!cancelled) setPhase('result'); }, 200);
          return 1;
        }
        setTimeout(tick, 160);
        return next;
      });
    };
    setTimeout(tick, 160);
    return () => { cancelled = true; };
  }, [phase]);

  const campaignStories = stories.filter(
    s => s.campaign === (characters.find(c => c.id === selectedChar)?.campaign ?? null),
  );

  if (phase === 'running') {
    return (
      <div className="arc-action">
        <div className="arc-an-head">
          <div>
            <div className="crumbs">Arc Analysis · Analysing</div>
            <h2>
              Analysing arc
              {' '}
              <AiTag />
            </h2>
            <div className="target">
              {characters.find(c => c.id === selectedChar)?.title ?? 'Character'}
              {selectedStory
                ? ` · ${stories.find(s => s.id === selectedStory)?.title ?? 'Story'}`
                : ' · All stories'}
            </div>
          </div>
        </div>
        <ArcPhaseRail phase="running" />
        <div className="arc-an-body">
          <div className="arc-an-stream">
            <div className="arc-meter-row">
              <div className="arc-meter-cell">
                <span className="label">Progress</span>
                <span className="value">{Math.round(progress * 100)}%</span>
              </div>
              <div className="arc-meter-cell">
                <span className="label">Stories</span>
                <span className="value">{campaignStories.length}</span>
              </div>
              <div className="arc-meter-cell">
                <span className="label">Metrics</span>
                <span className="value">6</span>
                <span className="sub">dimensions</span>
              </div>
              <div className="arc-meter-cell">
                <span className="label">Status</span>
                <span className="value" style={{ fontSize: 13, color: 'var(--color-gold-mid)' }}>
                  Running
                </span>
              </div>
            </div>
            <p>
              Analysing character appearances across story files and extracting arc
              metrics… <span className="arc-an-cursor" />
            </p>
          </div>
          <div className="arc-card">
            <h4>Proposed changes</h4>
            <ul className="arc-an-events">
              <li>Reading story appearances…</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  if (phase === 'result') {
    return (
      <div className="arc-action">
        <div className="arc-an-head">
          <div>
            <div className="crumbs">Arc Analysis · Review</div>
            <h2>Analysis complete</h2>
            <div className="target">
              Review the proposed arc update and accept or discard.
            </div>
          </div>
          <div className="actions">
            <button
              type="button"
              className="arc-btn danger"
              onClick={() => { setPhase('setup'); setProgress(0); }}
            >
              Discard
            </button>
            <button type="button" className="arc-btn primary">
              Accept &amp; save
            </button>
          </div>
        </div>
        <ArcPhaseRail phase="result" />
        <div className="arc-an-body">
          <div className="arc-card scroll">
            <h4>Arc update preview</h4>
            <p style={{ fontStyle: 'italic', color: 'var(--ink-dim)', fontSize: 13 }}>
              Arc analysis result would appear here once the Python CLI is wired
              to this endpoint. Accept saves the result back to the character record.
            </p>
          </div>
          <div className="arc-card">
            <h4>Actions</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button
                type="button"
                className="arc-btn"
                onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-summary', arcCharId: selectedChar })}
              >
                View summary
              </button>
              <button
                type="button"
                className="arc-btn"
                onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-export', arcCharId: selectedChar })}
              >
                Export report
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="arc-action">
      <div className="arc-an-head">
        <div>
          <div className="crumbs">Arc Analysis · Configure</div>
          <h2>
            Analyse Character Arc
            {' '}
            <AiTag />
          </h2>
          <div className="target">
            Select a character and optionally a specific story. The model reads
            the story files and produces arc metric updates.
          </div>
        </div>
        <div className="actions">
          <button
            type="button"
            className="arc-btn"
            onClick={() => setCtx({ ...ctx, arcSubAction: undefined })}
          >
            Cancel
          </button>
        </div>
      </div>
      <ArcPhaseRail phase="setup" />
      <div className="arc-an-body">
        <div className="arc-card">
          <h4>Configuration</h4>
          <label className="arc-label">
            <span className="arc-label-text">Character</span>
            <select
              className="arc-select"
              value={selectedChar}
              onChange={e => setSelectedChar(e.target.value)}
            >
              <option value="">Select character…</option>
              {characters.map(c => (
                <option key={c.id} value={c.id}>{c.title}</option>
              ))}
            </select>
          </label>
          <label className="arc-label">
            <span className="arc-label-text">Story scope</span>
            <select
              className="arc-select"
              value={selectedStory}
              onChange={e => setSelectedStory(e.target.value)}
            >
              <option value="">All stories in campaign</option>
              {campaignStories.map(s => (
                <option key={s.id} value={s.id}>
                  {s.storyNumber != null
                    ? `${String(s.storyNumber).padStart(3, '0')} · `
                    : ''}
                  {s.title}
                </option>
              ))}
            </select>
          </label>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button
              type="button"
              className="arc-btn primary"
              disabled={!selectedChar}
              onClick={() => { setPhase('running'); setProgress(0); }}
            >
              Run analysis
              {' '}
              <AiTag />
            </button>
          </div>
        </div>
        <div className="arc-card">
          <h4>About arc analysis</h4>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.6, fontStyle: 'italic' }}>
            Arc analysis reads the selected character across all story appearances
            and computes development metrics: confidence, trauma, relationship strength,
            goal progress, moral alignment, and more.
          </p>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.6, fontStyle: 'italic' }}>
            Results are staged for review before being accepted to the character
            record. Use
            {' '}
            <em>All stories</em>
            {' '}
            for a full arc view or a single story
            for a targeted update.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   4. ArcOverview — campaign-wide comparison
   ──────────────────────────────────────────────────────────── */

function ArcOverview({ ctx, setCtx, characters }: SubScreenProps): React.ReactElement {
  return (
    <div className="arc-action">
      <div className="arc-hub-head">
        <div>
          <span className="arc-eyebrow">Campaign Arc Overview</span>
          <h2>All character arcs</h2>
          <p className="blurb">
            Side-by-side arc comparison for all characters in the active campaign.
            Run arc analysis on each character to populate this view.
          </p>
        </div>
        <div className="actions">
          <button
            type="button"
            className="arc-btn"
            onClick={() => setCtx({ ...ctx, arcSubAction: undefined })}
          >
            Back to hub
          </button>
        </div>
      </div>

      <div className="arc-hub-toolbar">
        <span className="stat">
          <strong>{characters.length}</strong>
          {' '}
          characters
        </span>
        <span className="arc-dot-sep">·</span>
        <span>
          <strong>0</strong>
          {' '}
          analysed
        </span>
      </div>

      <div style={{ padding: 24, fontStyle: 'italic', color: 'var(--ink-dim)', fontFamily: 'var(--font-body)', fontSize: 14 }}>
        {characters.length === 0
          ? 'No characters found for the active campaign.'
          : `${characters.length} character${characters.length !== 1 ? 's' : ''} found. Run arc analysis on each to see comparative development data here.`}
      </div>

      {characters.length > 0 && (
        <div style={{ padding: '0 24px', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {characters.map(c => (
            <button
              key={c.id}
              type="button"
              className="arc-btn small primary"
              onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-analyze', arcCharId: c.id })}
            >
              Analyse {c.title}
              {' '}
              <AiTag />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   5. ArcExport — export arc report
   ──────────────────────────────────────────────────────────── */

type ExportFormat = 'markdown' | 'json';

function ArcExport({ ctx, setCtx, characters }: SubScreenProps): React.ReactElement {
  const charId = ctx.arcCharId as string | undefined;
  const [selectedChar, setSelectedChar] = React.useState(charId ?? '');
  const [format, setFormat] = React.useState<ExportFormat>('markdown');

  const char = characters.find(c => c.id === selectedChar) ?? null;

  return (
    <div className="arc-action">
      <div className="arc-an-head">
        <div>
          <div className="crumbs">Arc Analysis · Export</div>
          <h2>Export arc report</h2>
          <div className="target">
            Export arc analysis data to a file for sharing or archiving.
          </div>
        </div>
        <div className="actions">
          <button
            type="button"
            className="arc-btn"
            onClick={() => setCtx({ ...ctx, arcSubAction: undefined })}
          >
            Cancel
          </button>
        </div>
      </div>

      <div className="arc-exp-grid">
        <div className="arc-exp-setup">
          <div className="head">
            <span className="arc-eyebrow">Export options</span>
            <h2>Configure</h2>
          </div>
          <div style={{ padding: '16px 22px', display: 'flex', flexDirection: 'column', gap: 14 }}>
            <label className="arc-label">
              <span className="arc-label-text">Character</span>
              <select
                className="arc-select"
                value={selectedChar}
                onChange={e => setSelectedChar(e.target.value)}
              >
                <option value="">All characters</option>
                {characters.map(c => (
                  <option key={c.id} value={c.id}>{c.title}</option>
                ))}
              </select>
            </label>
            <label className="arc-label">
              <span className="arc-label-text">Format</span>
              <select
                className="arc-select"
                value={format}
                onChange={e => setFormat(e.target.value as ExportFormat)}
              >
                <option value="markdown">Markdown (.md)</option>
                <option value="json">JSON (.json)</option>
              </select>
            </label>
            <button type="button" className="arc-btn primary">
              Export
              {' '}
              {char ? char.title : 'all characters'}
            </button>
          </div>
        </div>

        <div style={{ padding: 24, fontStyle: 'italic', color: 'var(--ink-dim)', fontFamily: 'var(--font-body)', fontSize: 13 }}>
          {selectedChar
            ? `Export will include the arc report for ${char?.title ?? 'selected character'}.`
            : 'Export will include arc reports for all characters in the active campaign.'}
          {' '}
          Run arc analysis first to generate data for export.
        </div>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Root export — dispatches to sub-screens via ctx.arcSubAction
   ──────────────────────────────────────────────────────────── */

export function CharacterArcScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data         = useConsoleData();
  const campaignName = (ctx.activeCampaignName as string | null | undefined) ?? null;

  const characters = campaignName
    ? charactersForCampaign(data, campaignName)
    : playerCharacters(data);

  const stories = campaignName
    ? storiesForCampaign(data, campaignName)
    : data.stories;

  const subAction = ctx.arcSubAction as string | undefined;
  const props     = { ctx, setCtx, characters, stories };

  if (subAction === 'arc-summary')  return <ArcSummary  {...props} />;
  if (subAction === 'arc-analyze')  return <ArcAnalyze  {...props} />;
  if (subAction === 'arc-overview') return <ArcOverview {...props} />;
  if (subAction === 'arc-export')   return <ArcExport   {...props} />;
  return <ArcHub {...props} />;
}
