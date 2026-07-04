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
  type DrupalCharacterArc,
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

const ARC_DIRECTIONS: ArcDirection[] = [
  'growth', 'decline', 'stasis', 'fluctuation', 'transformation',
];
const GOAL_STATUSES: ArcGoal['status'][] = ['active', 'dormant', 'completed'];

function asDirection(value: string): ArcDirection {
  return (ARC_DIRECTIONS as string[]).includes(value)
    ? (value as ArcDirection)
    : 'stasis';
}

function asStage(value: string): ArcStage {
  return (STAGES as string[]).includes(value) ? (value as ArcStage) : 'introduction';
}

function asGoalStatus(value: string): ArcGoal['status'] {
  return (GOAL_STATUSES as string[]).includes(value)
    ? (value as ArcGoal['status'])
    : 'active';
}

/** Coerce a saved (loose-typed) Drupal arc into the strict console shape. */
function toArcData(arc: DrupalCharacterArc): CharacterArcData {
  const metrics: Record<string, ArcMetric> = {};
  for (const [key, m] of Object.entries(arc.metrics)) {
    metrics[key] = {
      label:     m.label,
      series:    m.series,
      direction: asDirection(m.direction),
      obs:       m.obs,
    };
  }
  return {
    direction:       asDirection(arc.direction),
    stage:           asStage(arc.stage),
    summary:         arc.summary,
    storiesAnalyzed: arc.storiesAnalyzed,
    lastAnalyzed:    arc.lastAnalyzed,
    metrics,
    relationships:   arc.relationships,
    goals:           arc.goals.map(g => ({
      description: g.description,
      status:      asGoalStatus(g.status),
      progress:    g.progress,
    })),
  };
}

/**
 * Resolve a character's arc for display: prefer a just-analysed result cached
 * in ctx (immediate feedback before the static query refetches), else the arc
 * saved on the character record.
 */
function arcForChar(
  ctx: ScreenProps['ctx'],
  char: DrupalCharacter | null,
): CharacterArcData | null {
  if (!char) {
    return null;
  }
  const cache = ctx.arcResults as Record<string, CharacterArcData> | undefined;
  if (cache?.[char.id]) {
    return cache[char.id];
  }
  return char.arc ? toArcData(char.arc) : null;
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
  imageUrl,
}: {
  name: string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  imageUrl?: string | null;
}): React.ReactElement {
  const cls = `arc-portrait${size !== 'md' ? ` ${size}` : ''}`;
  if (imageUrl) {
    return (
      <div className={cls}>
        <img
          src={imageUrl}
          alt={name}
          style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'inherit' }}
        />
      </div>
    );
  }
  const initials = name
    .split(' ')
    .map(w => w[0] ?? '')
    .join('')
    .slice(0, 2)
    .toUpperCase();
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
  const analysedCount = characters.filter(c => arcForChar(ctx, c)).length;
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
            disabled={characters.length === 0}
            onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-analyze', arcBatch: true })}
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
          <strong>{analysedCount}</strong>
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
            No characters found for the active campaign. Add characters to the party first.
          </p>
        ) : (
          characters.map(char => {
            const cardArc = arcForChar(ctx, char);
            return (
            <div
              key={char.id}
              role="button"
              tabIndex={0}
              className={`arc-hub-card${cardArc ? '' : ' stale'}`}
              onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-summary', arcCharId: char.id })}
              onKeyDown={e => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setCtx({ ...ctx, arcSubAction: 'arc-summary', arcCharId: char.id });
                }
              }}
            >
              <ArcPortrait name={char.title} imageUrl={char.imageUrl} />
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
                  {cardArc ? (
                    <span className="stories" style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
                      <ArcDirBadge direction={cardArc.direction} />
                      {cardArc.storiesAnalyzed} stories
                    </span>
                  ) : (
                    <span className="stories">Not yet analysed</span>
                  )}
                  <span className="grow" />
                  <button
                    type="button"
                    className="arc-btn small primary"
                    onClick={e => {
                      e.stopPropagation();
                      setCtx({ ...ctx, arcSubAction: 'arc-analyze', arcCharId: char.id, arcBatch: false });
                    }}
                  >
                    Analyse
                    {' '}
                    <AiTag />
                  </button>
                </div>
              </div>
            </div>
            );
          })
        )}
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   Shared arc detail body (summary + metrics + goals + relationships)
   ──────────────────────────────────────────────────────────── */

function ArcDetailBody({ arc }: { arc: CharacterArcData }): React.ReactElement {
  return (
    <>
      <div className="arc-sum-summary">
        <h4>Arc summary</h4>
        <p>{arc.summary}</p>
      </div>
      <div className="arc-sum-grid">
        <div className="arc-sum-section">
          <h4>
            Metrics
            <span className="meta">
              {arc.storiesAnalyzed}
              {' '}
              stories · last
              {' '}
              {arc.lastAnalyzed}
            </span>
          </h4>
          <div className="arc-dim-grid">
            {Object.values(arc.metrics).map(m => {
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
            {Object.keys(arc.metrics).length === 0 && (
              <p className="obs" style={{ fontStyle: 'italic' }}>No metric data.</p>
            )}
          </div>
        </div>

        <div>
          <div className="arc-sum-section" style={{ marginBottom: 14 }}>
            <h4>Goals</h4>
            {arc.goals.map((g, i) => (
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
            {arc.goals.length === 0 && (
              <p className="obs" style={{ fontStyle: 'italic' }}>No goals identified.</p>
            )}
          </div>

          <div className="arc-sum-section">
            <h4>Relationships</h4>
            <ul className="arc-rel-list">
              {arc.relationships.map((r, i) => (
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
            {arc.relationships.length === 0 && (
              <p className="obs" style={{ fontStyle: 'italic' }}>No relationships identified.</p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

/* ────────────────────────────────────────────────────────────
   2. ArcSummary — one character's arc detail
   ──────────────────────────────────────────────────────────── */

function ArcSummary({ ctx, setCtx, characters }: SubScreenProps): React.ReactElement {
  const charId = ctx.arcCharId as string | undefined;
  const char   = characters.find(c => c.id === charId) ?? characters[0] ?? null;

  const arcData = arcForChar(ctx, char);

  return (
    <div className="arc-action">
      <div className="arc-sum-head">
        {char ? <ArcPortrait name={char.title} size="lg" imageUrl={char.imageUrl} /> : <div className="arc-portrait lg" />}

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
            onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-analyze', arcCharId: char?.id, arcBatch: false })}
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
        <ArcDetailBody arc={arcData} />
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
   Two-step analysis runner (per-story, then aggregate)
   ──────────────────────────────────────────────────────────── */

interface ArcProgress {
  done:  number;
  total: number;
}

/**
 * Run a character's arc analysis one story at a time, then aggregate.
 *
 * Each story is a single model call (its own request), so no request runs long
 * enough to trip the fetch timeout, and `onProgress` drives a live counter.
 */
async function runArcAnalysis(
  characterName: string,
  campaignName: string,
  pronouns: string,
  storyIds: string[],
  onProgress: (p: ArcProgress) => void,
): Promise<CharacterArcData> {
  const dataPoints: unknown[] = [];
  for (let i = 0; i < storyIds.length; i += 1) {
    onProgress({ done: i, total: storyIds.length });
    // Sequential by design: one model call at a time keeps the sidecar sane.
    const res = await fetch('/api/arc-analyze-story', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ characterName, storyId: storyIds[i], pronouns }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `Story analysis failed (${res.status})`);
    dataPoints.push(data.dataPoint);
  }
  onProgress({ done: storyIds.length, total: storyIds.length });

  const aggRes = await fetch('/api/arc-aggregate', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ characterName, campaignName, pronouns, dataPoints }),
  });
  const agg = await aggRes.json();
  if (!aggRes.ok) throw new Error(agg.error || `Aggregation failed (${aggRes.status})`);
  return agg as CharacterArcData;
}

/* ────────────────────────────────────────────────────────────
   3. ArcAnalyze — 3-phase AI analysis
   ──────────────────────────────────────────────────────────── */

function ArcAnalyze({ ctx, setCtx, characters, stories }: SubScreenProps): React.ReactElement {
  const charId = ctx.arcCharId as string | undefined;
  const char   = characters.find(c => c.id === charId) ?? characters[0] ?? null;

  const [phase, setPhase]     = React.useState<AnalyzePhase>('setup');
  const [selectedChar, setSelectedChar] = React.useState(char?.id ?? '');
  const [selectedStory, setSelectedStory] = React.useState('');
  const [result, setResult]   = React.useState<CharacterArcData | null>(null);
  const [error, setError]     = React.useState<string | null>(null);
  const [saving, setSaving]   = React.useState(false);
  const [saved, setSaved]     = React.useState(false);
  const [progress, setProgress] = React.useState<ArcProgress>({ done: 0, total: 0 });

  const activeChar = characters.find(c => c.id === selectedChar) ?? null;
  // When a campaign is active the `stories` prop is already scoped to it, so use
  // it directly — a party member may be a source character whose own `campaign`
  // field is null, which would otherwise filter every story out.
  const activeCampaign = (ctx.activeCampaignName as string | null | undefined) ?? null;
  const campaignStories = activeCampaign
    ? stories
    : stories.filter(s => s.campaign === (activeChar?.campaign ?? null));

  const runAnalysis = async (): Promise<void> => {
    if (!activeChar) return;
    const storyIds = selectedStory ? [selectedStory] : campaignStories.map(s => s.id);
    if (storyIds.length === 0) {
      setError('No stories found for this character’s campaign.');
      return;
    }
    setError(null);
    setSaved(false);
    setResult(null);
    setProgress({ done: 0, total: storyIds.length });
    setPhase('running');
    try {
      const arc = await runArcAnalysis(
        activeChar.title,
        activeCampaign ?? activeChar.campaign ?? '',
        activeChar.pronouns ?? '',
        storyIds,
        setProgress,
      );
      setResult(arc);
      setPhase('result');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setPhase('setup');
    }
  };

  const acceptResult = async (): Promise<void> => {
    if (!activeChar || !result) return;
    setSaving(true);
    setError(null);
    try {
      const res = await fetch('/api/save-arc', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: activeChar.id, arc: result }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `Save failed (${res.status})`);
      const prev = (ctx.arcResults as Record<string, CharacterArcData> | undefined) ?? {};
      setCtx({ ...ctx, arcResults: { ...prev, [activeChar.id]: result }, arcCharId: activeChar.id });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

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
              {activeChar?.title ?? 'Character'}
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
                <span className="value">
                  {progress.done}
                  {' / '}
                  {progress.total}
                </span>
                <span className="sub">stories</span>
              </div>
              <div className="arc-meter-cell">
                <span className="label">Status</span>
                <span className="value" style={{ fontSize: 13, color: 'var(--color-gold-mid)' }}>
                  {progress.done >= progress.total ? 'Aggregating' : 'Analysing'}
                </span>
              </div>
            </div>
            <div className="arc-progress-bar" aria-hidden="true">
              <i style={{ width: `${progress.total ? (progress.done / progress.total) * 100 : 0}%` }} />
            </div>
            <p>
              {progress.done >= progress.total
                ? 'Aggregating the per-story analyses into the character arc…'
                : `Analysing story ${progress.done + 1} of ${progress.total} — each story is a separate model pass, so this can take a while.`}
              {' '}
              <span className="arc-an-cursor" />
            </p>
          </div>
          <div className="arc-card">
            <h4>Working</h4>
            <ul className="arc-an-events">
              <li>{progress.done} of {progress.total} stories analysed</li>
              <li>{progress.done >= progress.total ? 'Aggregating arc, relationships, and goals…' : 'One model call per story on the sidecar…'}</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  if (phase === 'result' && result) {
    return (
      <div className="arc-action">
        <div className="arc-an-head">
          <div>
            <div className="crumbs">Arc Analysis · Review</div>
            <h2>{saved ? 'Arc saved' : 'Analysis complete'}</h2>
            <div className="target">
              {saved
                ? `${activeChar?.title ?? 'Character'}’s arc has been saved.`
                : 'Review the proposed arc update and accept or discard.'}
            </div>
            {error && <div className="arc-error">{error}</div>}
          </div>
          <div className="actions">
            {saved ? (
              <button
                type="button"
                className="arc-btn primary"
                onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-summary', arcCharId: activeChar?.id })}
              >
                View summary
              </button>
            ) : (
              <>
                <button
                  type="button"
                  className="arc-btn danger"
                  onClick={() => { setPhase('setup'); setResult(null); }}
                  disabled={saving}
                >
                  Discard
                </button>
                <button
                  type="button"
                  className="arc-btn primary"
                  onClick={acceptResult}
                  disabled={saving}
                >
                  {saving ? 'Saving…' : 'Accept & save'}
                </button>
              </>
            )}
          </div>
        </div>
        <ArcPhaseRail phase="result" />
        <div className="arc-sum-head" style={{ borderTop: 'none' }}>
          <div className="identity">
            <div className="arc-state">
              <ArcDirBadge direction={result.direction} />
              <ArcStageTrack stage={result.stage} />
            </div>
          </div>
        </div>
        <ArcDetailBody arc={result} />
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
          {error && <div className="arc-error">{error}</div>}
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
              onChange={e => { setSelectedChar(e.target.value); setSelectedStory(''); }}
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
              disabled={!selectedChar || campaignStories.length === 0}
              onClick={runAnalysis}
            >
              Run analysis
              {' '}
              <AiTag />
            </button>
          </div>
          {selectedChar && campaignStories.length === 0 && (
            <p className="obs" style={{ fontStyle: 'italic', marginTop: 8 }}>
              No stories in this character’s campaign to analyse yet.
            </p>
          )}
        </div>
        <div className="arc-card">
          <h4>About arc analysis</h4>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.6, fontStyle: 'italic' }}>
            Arc analysis reads the selected character across all story appearances
            and computes development metrics: confidence, trauma, relationship strength,
            goal progress, and more.
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
   3b. ArcBatch — sequential "analyse all" runner
   ──────────────────────────────────────────────────────────── */

type BatchStatus = 'pending' | 'running' | 'done' | 'error' | 'skipped';

function ArcBatch({ ctx, setCtx, characters, stories }: SubScreenProps): React.ReactElement {
  const [status, setStatus] = React.useState<Record<string, BatchStatus>>({});
  const [progress, setProgress] = React.useState<Record<string, ArcProgress>>({});
  const [running, setRunning] = React.useState(false);
  const [done, setDone] = React.useState(false);

  const activeCampaign = (ctx.activeCampaignName as string | null | undefined) ?? null;

  const analyseOne = async (char: DrupalCharacter): Promise<CharacterArcData | null> => {
    const scoped = activeCampaign
      ? stories
      : stories.filter(s => s.campaign === (char.campaign ?? null));
    const storyIds = scoped.map(s => s.id);
    if (storyIds.length === 0) {
      return null;
    }
    const arc = await runArcAnalysis(
      char.title,
      activeCampaign ?? char.campaign ?? '',
      char.pronouns ?? '',
      storyIds,
      p => setProgress(prev => ({ ...prev, [char.id]: p })),
    );
    const saveRes = await fetch('/api/save-arc', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: char.id, arc }),
    });
    const saveData = await saveRes.json();
    if (!saveRes.ok) throw new Error(saveData.error || `Save failed (${saveRes.status})`);
    return arc;
  };

  const runAll = async (): Promise<void> => {
    setRunning(true);
    setDone(false);
    const results: Record<string, CharacterArcData> = {};
    for (const char of characters) {
      setStatus(prev => ({ ...prev, [char.id]: 'running' }));
      try {
        // Sequential by design: one model call at a time keeps the sidecar sane.
        const arc = await analyseOne(char);
        if (arc) {
          results[char.id] = arc;
          setStatus(prev => ({ ...prev, [char.id]: 'done' }));
        } else {
          setStatus(prev => ({ ...prev, [char.id]: 'skipped' }));
        }
      } catch {
        setStatus(prev => ({ ...prev, [char.id]: 'error' }));
      }
    }
    const prev = (ctx.arcResults as Record<string, CharacterArcData> | undefined) ?? {};
    setCtx({ ...ctx, arcResults: { ...prev, ...results } });
    setRunning(false);
    setDone(true);
  };

  const label: Record<BatchStatus, string> = {
    pending: 'Queued',
    running: 'Analysing…',
    done:    'Analysed',
    error:   'Failed',
    skipped: 'No stories',
  };

  return (
    <div className="arc-action">
      <div className="arc-an-head">
        <div>
          <div className="crumbs">Arc Analysis · Analyse all</div>
          <h2>
            Analyse all characters
            {' '}
            <AiTag />
            {' '}
            <SlowTag />
          </h2>
          <div className="target">
            Runs arc analysis for every character in the active campaign, one at a
            time, and saves each result.
          </div>
        </div>
        <div className="actions">
          <button
            type="button"
            className="arc-btn"
            onClick={() => setCtx({ ...ctx, arcSubAction: undefined, arcBatch: false })}
            disabled={running}
          >
            {done ? 'Back to hub' : 'Cancel'}
          </button>
          <button
            type="button"
            className="arc-btn primary"
            onClick={runAll}
            disabled={running || characters.length === 0}
          >
            {running ? 'Running…' : done ? 'Run again' : 'Start'}
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
          <strong>{Object.values(status).filter(s => s === 'done').length}</strong>
          {' '}
          analysed
        </span>
      </div>
      <div style={{ padding: '8px 24px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        {characters.map(c => {
          const st = status[c.id] ?? 'pending';
          const p  = progress[c.id];
          const runningLabel = p && p.total > 0
            ? (p.done >= p.total ? 'Aggregating…' : `Story ${p.done + 1}/${p.total}`)
            : label.running;
          return (
            <div key={c.id} className="arc-rel-row" style={{ alignItems: 'center' }}>
              <ArcPortrait name={c.title} size="xs" imageUrl={c.imageUrl} />
              <div style={{ flex: 1 }}>
                <span className="who">{c.title}</span>
              </div>
              <span className={`status ${st === 'done' ? 'completed' : st === 'error' ? 'active' : 'dormant'}`}>
                {st === 'running' ? runningLabel : label[st]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────
   4. ArcOverview — campaign-wide comparison
   ──────────────────────────────────────────────────────────── */

function ArcOverview({ ctx, setCtx, characters }: SubScreenProps): React.ReactElement {
  const data         = useConsoleData();
  const campaignName = (ctx.activeCampaignName as string | null | undefined) ?? null;
  const campaign     = campaignName
    ? data.campaigns.find(c => c.name === campaignName) ?? null
    : null;
  const overview     = campaign?.campaignOverview ?? null;

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

      <div className="arc-story-so-far">
        <span className="arc-eyebrow">The story so far</span>
        {overview ? (
          <div className="arc-overview-prose" dangerouslySetInnerHTML={{ __html: overview }} />
        ) : (
          <p className="blurb">
            {campaignName
              ? 'No campaign overview yet. It is generated automatically as sessions are created, or run the summary backfill to build it from existing sessions.'
              : 'Select a campaign to see its synthesized story so far.'}
          </p>
        )}
      </div>

      <div className="arc-hub-toolbar">
        <span className="stat">
          <strong>{characters.length}</strong>
          {' '}
          characters
        </span>
        <span className="arc-dot-sep">·</span>
        <span>
          <strong>{characters.filter(c => arcForChar(ctx, c)).length}</strong>
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
              onClick={() => setCtx({ ...ctx, arcSubAction: 'arc-analyze', arcCharId: c.id, arcBatch: false })}
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
  if (subAction === 'arc-analyze') {
    return ctx.arcBatch ? <ArcBatch {...props} /> : <ArcAnalyze {...props} />;
  }
  if (subAction === 'arc-overview') return <ArcOverview {...props} />;
  if (subAction === 'arc-export')   return <ArcExport   {...props} />;
  return <ArcHub {...props} />;
}
