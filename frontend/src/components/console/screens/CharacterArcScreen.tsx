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
import { AiTag, SlowTag, Spinner } from '../atoms';
import { mergeStoryChunks, formatStoryAnalysis } from '../../../utils/arcRun';
import type { ArcDataPointDict, StoryChunks } from '../../../utils/arcRun';

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

/** Stored character_analysis presence for a character, keyed by character id. */
interface StoredInfo {
  storyCount: number;
  hasSummary: boolean;
}

function ArcHub({ ctx, setCtx, characters }: SubScreenProps): React.ReactElement {
  const [stored, setStored]       = React.useState<Map<string, StoredInfo>>(new Map());
  const [synthId, setSynthId]     = React.useState<string | null>(null);
  const [synthErr, setSynthErr]   = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    fetch('/api/list-analyses', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    '{}',
    })
      .then(res => res.json())
      .then((data: { analyses?: Array<{ characterId: string } & StoredInfo> }) => {
        if (!active) return;
        const map = new Map<string, StoredInfo>();
        for (const a of data.analyses ?? []) {
          map.set(a.characterId, { storyCount: a.storyCount, hasSummary: a.hasSummary });
        }
        setStored(map);
      })
      .catch(() => { /* hub still works without stored-analysis hints */ });
    return () => { active = false; };
  }, []);

  const synthesize = async (char: SubScreenProps['characters'][number]): Promise<void> => {
    setSynthId(char.id);
    setSynthErr(null);
    try {
      const arc = await synthesizeFromStored('', char.id, char.title, char.pronouns ?? '');
      // Carry the freshly synthesized arc into the summary screen so its sparkline
      // detail shows immediately (before the next Gatsby rebuild refreshes ctx).
      setCtx({ ...ctx, arcSubAction: 'arc-summary', arcCharId: char.id, arcSynth: { charId: char.id, arc } });
    } catch (err) {
      setSynthErr(err instanceof Error ? err.message : String(err));
    } finally {
      setSynthId(null);
    }
  };

  const analysedCount = characters.filter(
    c => arcForChar(ctx, c) || stored.has(c.id),
  ).length;
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

      {synthErr && (
        <div className="arc-error" style={{ margin: '0 24px' }}>{synthErr}</div>
      )}

      <div className="arc-hub-grid">
        {characters.length === 0 ? (
          <p style={{ gridColumn: '1/-1', fontStyle: 'italic', color: 'var(--ink-dim)', padding: 24 }}>
            No characters found for the active campaign. Add characters to the party first.
          </p>
        ) : (
          characters.map(char => {
            const cardArc = arcForChar(ctx, char);
            const info    = stored.get(char.id);
            return (
            <div
              key={char.id}
              role="button"
              tabIndex={0}
              className={`arc-hub-card${cardArc || info ? '' : ' stale'}`}
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
                  ) : info ? (
                    <span className="stories">{info.storyCount} stories analysed</span>
                  ) : (
                    <span className="stories">Not yet analysed</span>
                  )}
                  <span className="grow" />
                  {info && (
                    <button
                      type="button"
                      className="arc-btn small"
                      disabled={synthId === char.id}
                      onClick={e => {
                        e.stopPropagation();
                        void synthesize(char);
                      }}
                    >
                      {synthId === char.id && <Spinner size={9} />}
                      {synthId === char.id
                        ? 'Synthesizing…'
                        : info.hasSummary ? 'Re-synthesize' : 'Synthesize'}
                      {' '}
                      <AiTag />
                    </button>
                  )}
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

/** One stored per-story analysis (plain prose, as returned by get-analysis). */
interface StoredAnalysis {
  storyNumber: number | null;
  text:        string;
}

/**
 * The character_analysis node's stored record: the synthesized summary plus each
 * story's analysis prose, read live from Drupal, with a Discard action that
 * deletes the node. This mirrors on the console what is stored in the CMS.
 */
function StoredAnalysisPanel({
  campaignId,
  characterId,
  characterName,
  pronouns,
  initialArc,
}: {
  campaignId:    string;
  characterId:   string;
  characterName: string;
  pronouns:      string;
  initialArc:    CharacterArcData | null;
}): React.ReactElement | null {
  const [analyses, setAnalyses]       = React.useState<StoredAnalysis[]>([]);
  const [summary, setSummary]         = React.useState(initialArc?.summary ?? '');
  const [loading, setLoading]         = React.useState(true);
  const [error, setError]             = React.useState<string | null>(null);
  const [discarding, setDiscarding]   = React.useState(false);
  const [discarded, setDiscarded]     = React.useState(false);
  const [synthesizing, setSynthesizing] = React.useState(false);
  const [arc, setArc]                 = React.useState<CharacterArcData | null>(initialArc);

  React.useEffect(() => {
    let active = true;
    if (!characterId) {
      setLoading(false);
      return () => { active = false; };
    }
    setLoading(true);
    setError(null);
    setDiscarded(false);
    fetch('/api/get-analysis', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaignId, characterId }),
    })
      .then(async res => {
        const data = await res.json();
        if (!active) return;
        if (!res.ok) throw new Error(data.error || 'Failed to load analysis');
        setAnalyses(Array.isArray(data.storyAnalyses) ? data.storyAnalyses : []);
        setSummary(typeof data.summary === 'string' ? data.summary : '');
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [campaignId, characterId]);

  const discard = async (): Promise<void> => {
    if (!characterId) return;
    setDiscarding(true);
    setError(null);
    try {
      const res = await fetch('/api/delete-analysis', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ campaignId, characterId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to discard analysis');
      setAnalyses([]);
      setSummary('');
      setDiscarded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDiscarding(false);
    }
  };

  // Re-narrate the summary from the already-stored per-story prose, without
  // re-analysing the stories. Handy whenever a record already exists.
  const synthesize = async (): Promise<void> => {
    if (!characterId) return;
    setSynthesizing(true);
    setError(null);
    try {
      const result = await synthesizeFromStored(campaignId, characterId, characterName, pronouns);
      setArc(result);
      setSummary(result.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSynthesizing(false);
    }
  };

  if (!characterId) return null;
  if (loading) {
    return (
      <div className="arc-card" style={{ margin: 24 }}>
        <p className="obs" style={{ fontStyle: 'italic' }}>Loading stored analysis…</p>
      </div>
    );
  }
  if (discarded) {
    return (
      <div className="arc-card" style={{ margin: 24 }}>
        <p className="obs" style={{ fontStyle: 'italic' }}>Analysis record discarded.</p>
      </div>
    );
  }
  if (!summary && analyses.length === 0) {
    return error ? (
      <div className="arc-card" style={{ margin: 24 }}>
        <div className="arc-error">{error}</div>
      </div>
    ) : null;
  }

  return (
    <div className="arc-card" style={{ margin: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0 }}>Stored analysis record</h4>
        <div style={{ display: 'flex', gap: 8 }}>
          {analyses.length > 0 && (
            <button
              type="button"
              className="arc-btn small"
              onClick={synthesize}
              disabled={synthesizing || discarding}
            >
              {synthesizing && <Spinner size={9} />}
              {synthesizing
                ? 'Synthesizing…'
                : summary ? 'Re-synthesize summary' : 'Synthesize summary'}
            </button>
          )}
          <button
            type="button"
            className="arc-btn danger small"
            onClick={discard}
            disabled={discarding || synthesizing}
          >
            {discarding && <Spinner size={9} />}
            {discarding ? 'Discarding…' : 'Discard analysis'}
          </button>
        </div>
      </div>
      {error && <div className="arc-error" style={{ marginTop: 8 }}>{error}</div>}
      {arc ? (
        <div style={{ marginTop: 12 }}>
          <div className="arc-state" style={{ marginBottom: 8 }}>
            <ArcDirBadge direction={arc.direction} />
            <ArcStageTrack stage={arc.stage} />
          </div>
          <ArcDetailBody arc={arc} />
        </div>
      ) : summary ? (
        <div style={{ marginTop: 12 }}>
          <span className="arc-eyebrow" style={{ display: 'block', marginBottom: 6 }}>Summary</span>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {summary}
          </p>
        </div>
      ) : null}
      {analyses.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <span className="arc-eyebrow" style={{ display: 'block', marginBottom: 6 }}>
            Per-story analyses ({analyses.length})
          </span>
          {analyses.map((a, i) => (
            <details key={a.storyNumber ?? `idx-${i}`} style={{ marginBottom: 8 }}>
              <summary style={{ cursor: 'pointer', fontWeight: 600 }}>
                {a.storyNumber !== null
                  ? `Story ${String(a.storyNumber).padStart(3, '0')}`
                  : 'Story'}
              </summary>
              <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, lineHeight: 1.6, whiteSpace: 'pre-wrap', marginTop: 6 }}>
                {a.text}
              </p>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}

function ArcSummary({ ctx, setCtx, characters }: SubScreenProps): React.ReactElement {
  const charId = ctx.arcCharId as string | undefined;
  const char   = characters.find(c => c.id === charId) ?? characters[0] ?? null;

  const data = useConsoleData();
  const activeCampaign = (ctx.activeCampaignName as string | null | undefined) ?? null;
  const campaignId =
    data.campaigns.find(c => c.name === (activeCampaign ?? char?.campaign))?.id
    ?? char?.campaignId ?? '';

  // An arc freshly synthesized from the hub is carried in via ctx so its detail
  // (sparklines, direction) shows immediately, before the next Gatsby rebuild.
  const synthCarry = ctx.arcSynth as { charId: string; arc: CharacterArcData } | undefined;
  const initialArc = synthCarry && synthCarry.charId === char?.id ? synthCarry.arc : null;

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

      {char && (
        <StoredAnalysisPanel
          campaignId={campaignId}
          characterId={char.id}
          characterName={char.title}
          pronouns={char.pronouns ?? ''}
          initialArc={initialArc}
        />
      )}

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

/** Fetch every story's text split into small analysis chunks (light, no AI). */
async function fetchStoryChunks(storyIds: string[]): Promise<StoryChunks[]> {
  const stories: StoryChunks[] = [];
  for (const storyId of storyIds) {
    try {
      const res = await fetch('/api/arc-story-chunks', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ storyId }),
      });
      const data = await res.json();
      if (res.ok && Array.isArray(data.chunks) && data.chunks.length > 0) {
        stories.push({ title: data.title, storyNumber: data.storyNumber, chunks: data.chunks });
      }
    } catch {
      // Skip a story whose chunks can't be fetched; the rest still run.
    }
  }
  return stories;
}

/** Persist a story analysis / summary to the character_analysis node (best-effort). */
async function persistAnalysis(
  campaignId: string,
  characterId: string,
  fields: {
    storyNumber?: number | null;
    storyText?:   string;
    datapoint?:   string;
    summary?:     string;
  },
): Promise<void> {
  if (!characterId) {
    return;
  }
  try {
    await fetch('/api/upsert-analysis', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaignId, characterId, ...fields }),
    });
  } catch {
    // Persistence is best-effort; a failure never aborts the analysis.
  }
}

/** Story numbers already stored on the node — the resume signal. */
async function fetchDoneStoryNumbers(
  campaignId: string,
  characterId: string,
): Promise<Set<number>> {
  if (!characterId) {
    return new Set<number>();
  }
  try {
    const res = await fetch('/api/get-analysis', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ campaignId, characterId }),
    });
    const data = await res.json();
    if (res.ok && Array.isArray(data.storyNumbers)) {
      return new Set<number>(
        (data.storyNumbers as unknown[]).filter((n): n is number => typeof n === 'number'),
      );
    }
  } catch {
    // No resume data available; every story is analysed.
  }
  return new Set<number>();
}

/**
 * Synthesize the arc from the analyses stored on the node.
 *
 * Reads every persisted per-story analysis (server-side) rather than the
 * in-memory data points, so a resumed run still produces a whole-arc summary
 * from the stories analysed across earlier attempts.
 */
async function synthesizeFromStored(
  campaignId: string,
  characterId: string,
  characterName: string,
  pronouns: string,
): Promise<CharacterArcData> {
  const res = await fetch('/api/synthesize-analysis', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ campaignId, characterId, characterName, pronouns }),
  });
  const raw = await res.text();
  let data: { error?: string } & Partial<CharacterArcData> = {};
  try {
    data = raw ? JSON.parse(raw) : {};
  } catch {
    throw new Error(raw.slice(0, 200) || `Synthesis failed (${res.status})`);
  }
  if (!res.ok) {
    throw new Error(data.error || `Synthesis failed (${res.status})`);
  }
  // The endpoint aggregates the stored data points into a full arc: real metric
  // trend lines, direction, and stage, plus relationships, goals, and summary.
  return {
    direction:       asDirection(data.direction ?? 'stasis'),
    stage:           asStage(data.stage ?? 'introduction'),
    summary:         data.summary ?? '',
    storiesAnalyzed: data.storiesAnalyzed ?? 0,
    lastAnalyzed:    data.lastAnalyzed ?? new Date().toISOString(),
    metrics:         data.metrics ?? {},
    relationships:   data.relationships ?? [],
    goals:           data.goals ?? [],
  };
}

/**
 * Run a character's arc analysis one CHUNK at a time, then aggregate.
 *
 * Every request is a single small chunk (a bounded ~30s model pass), so a large
 * story can never hang in one multi-minute request, and `onProgress` ticks per
 * chunk so the UI always shows movement. A failed chunk is retried once then
 * skipped — one bad passage never aborts the run. Each story's analysis is
 * persisted to a character_analysis node as it completes, and a story already
 * stored there is skipped — so a crashed run resumes where it left off and the
 * final summary is synthesized from every stored story, not just this attempt.
 */
async function runArcAnalysis(
  characterName: string,
  campaignName: string,
  campaignId: string,
  characterId: string,
  pronouns: string,
  storyIds: string[],
  onProgress: (p: ArcProgress) => void,
): Promise<CharacterArcData> {
  const stories = await fetchStoryChunks(storyIds);
  const total = stories.reduce((sum, story) => sum + story.chunks.length, 0);
  if (total === 0) {
    throw new Error('No story text found to analyse.');
  }

  // The character is the key for the analysis record; the campaign is optional
  // metadata, so persistence/resume only need a character id.
  const persisting = Boolean(characterId);
  const doneStoryNumbers = persisting
    ? await fetchDoneStoryNumbers(campaignId, characterId)
    : new Set<number>();

  const dataPoints: ArcDataPointDict[] = [];
  let done = 0;
  onProgress({ done, total });
  for (const story of stories) {
    // Resume: a story already stored on the node is skipped. Its prose is
    // persisted and will be read back during synthesis.
    if (story.storyNumber !== null && doneStoryNumbers.has(story.storyNumber)) {
      done += story.chunks.length;
      onProgress({ done, total });
      continue;
    }
    const storyParts: ArcDataPointDict[] = [];
    for (const chunk of story.chunks) {
      let got = false;
      for (let attempt = 0; attempt < 2 && !got; attempt += 1) {
        try {
          const res = await fetch('/api/arc-analyze-story', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              characterName,
              content:     chunk,
              title:       story.title,
              storyNumber: story.storyNumber,
              pronouns,
            }),
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || `Passage analysis failed (${res.status})`);
          storyParts.push(data.dataPoint as ArcDataPointDict);
          got = true;
        } catch {
          // Swallow: the inner loop retries, and an unrecovered passage is skipped.
        }
      }
      done += 1;
      onProgress({ done, total });
    }
    // Collapse this story's passages into one data point and persist a readable
    // analysis to the character_analysis node so the run is crash-safe.
    if (storyParts.length > 0) {
      const merged = mergeStoryChunks(storyParts, story.title, story.storyNumber);
      dataPoints.push(merged);
      if (persisting) {
        await persistAnalysis(campaignId, characterId, {
          storyNumber: story.storyNumber,
          storyText:   formatStoryAnalysis(merged),
          // Persist the structured data point so synthesis can recompute real
          // metric trends (numbers), not just re-read prose.
          datapoint:   JSON.stringify(merged),
        });
      }
    }
  }

  // Node-backed path: synthesize the arc from every story stored on the node
  // (this attempt plus any prior resumed ones). Reading the persisted prose is
  // what lets a crashed run pick up where it left off.
  if (persisting) {
    if (dataPoints.length === 0 && doneStoryNumbers.size === 0) {
      throw new Error('Every passage failed to analyse — is the sidecar running?');
    }
    return synthesizeFromStored(campaignId, characterId, characterName, pronouns);
  }

  // Fallback (no node to persist to): aggregate the in-memory data points.
  if (dataPoints.length === 0) {
    throw new Error('Every passage failed to analyse — is the sidecar running?');
  }
  let agg: CharacterArcData | null = null;
  let aggError = 'Aggregation failed';
  for (let attempt = 0; attempt < 2 && agg === null; attempt += 1) {
    try {
      const aggRes = await fetch('/api/arc-aggregate', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ characterName, campaignName, pronouns, dataPoints }),
      });
      // Read as text first so a non-JSON error page yields a useful message
      // instead of a raw "JSON.parse: unexpected character".
      const raw = await aggRes.text();
      let data: { error?: string } & Partial<CharacterArcData> = {};
      try {
        data = raw ? JSON.parse(raw) : {};
      } catch {
        throw new Error(raw.slice(0, 200) || `Aggregation failed (${aggRes.status})`);
      }
      if (!aggRes.ok) throw new Error(data.error || `Aggregation failed (${aggRes.status})`);
      agg = data as CharacterArcData;
    } catch (err) {
      aggError = err instanceof Error ? err.message : String(err);
    }
  }
  if (agg === null) throw new Error(aggError);
  return { ...agg, storiesAnalyzed: stories.length };
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

  const data = useConsoleData();
  const activeChar = characters.find(c => c.id === selectedChar) ?? null;
  // When a campaign is active the `stories` prop is already scoped to it, so use
  // it directly — a party member may be a source character whose own `campaign`
  // field is null, which would otherwise filter every story out.
  const activeCampaign = (ctx.activeCampaignName as string | null | undefined) ?? null;
  const campaignId =
    data.campaigns.find(c => c.name === (activeCampaign ?? activeChar?.campaign))?.id
    ?? activeChar?.campaignId ?? '';
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
        campaignId,
        activeChar.id,
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
                <span className="sub">passages</span>
              </div>
              <div className="arc-meter-cell">
                <span className="label">Status</span>
                <span className="value" style={{ fontSize: 13, color: 'var(--color-gold-mid)' }}>
                  {progress.total > 0 && progress.done >= progress.total ? 'Aggregating' : 'Analysing'}
                </span>
              </div>
            </div>
            <div className="arc-progress-bar" aria-hidden="true">
              <i style={{ width: `${progress.total ? (progress.done / progress.total) * 100 : 0}%` }} />
            </div>
            <p>
              {progress.total > 0 && progress.done >= progress.total
                ? 'Aggregating the passage analyses into the character arc…'
                : `Analysing passage ${progress.done + 1} of ${progress.total || '…'} — each passage is a short, separate model pass.`}
              {' '}
              <span className="arc-an-cursor" />
            </p>
          </div>
          <div className="arc-card">
            <h4>Working</h4>
            <ul className="arc-an-events">
              <li>{progress.done} of {progress.total} passages analysed</li>
              <li>{progress.total > 0 && progress.done >= progress.total ? 'Aggregating arc, relationships, and goals…' : 'One short model call per passage — bounded and resumable.'}</li>
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
                  {saving && <Spinner />}
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
  const data = useConsoleData();
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
    const campaignId =
      data.campaigns.find(c => c.name === (activeCampaign ?? char.campaign))?.id
      ?? char.campaignId ?? '';
    const arc = await runArcAnalysis(
      char.title,
      activeCampaign ?? char.campaign ?? '',
      campaignId,
      char.id,
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
            {running && <Spinner />}
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
            ? (p.done >= p.total ? 'Aggregating…' : `Passage ${p.done + 1}/${p.total}`)
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
