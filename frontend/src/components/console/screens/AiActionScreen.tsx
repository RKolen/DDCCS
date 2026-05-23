/**
 * AiActionScreen — covers 11 of the 13 work-series sub-items.
 *
 * Two layout variants (stored in ctx.aiLayout):
 *   'workbench' (default) — form left, streaming result right, both visible.
 *   'forge'               — 3-phase stepper: Setup → Stream → Artifact.
 *
 * Port of:
 *   _canonical_source/screens-series-helpers.jsx  (AiFormControl, AiStreamBody)
 *   _canonical_source/screens-series-data.jsx     (ACTION_PRESETS, useAiRun)
 *   _canonical_source/screens-series-forge.jsx    (AiActionForge)
 *   _canonical_source/screens-series-workbench.jsx (AiActionWorkbench)
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon, AiTag, SlowTag } from '../atoms';

/* ─────────────────────────────────────────────────────────────
   Types
───────────────────────────────────────────────────────────── */

type InputKind = 'select' | 'textarea' | 'segment' | 'text';

interface InputSpec {
  id: string;
  label: string;
  kind: InputKind;
  options?: string[];
  rows?: number;
  placeholder?: string;
  default?: string;
}

interface ModelSpec {
  name: string;
  task: string;
  tone: string;
}

interface TargetSpec {
  kind: string;
  path: string;
}

interface EventEntry {
  t: string;
  msg: string;
}

interface ActionPreset {
  label: string;
  group: string;
  blurb: string;
  model: ModelSpec;
  duration: number;
  inputs: InputSpec[];
  outputKind: 'narrative' | 'analysis' | 'suggestions';
  slow?: boolean;
  mock?: string;
  target: TargetSpec | null;
  eventsLog?: EventEntry[];
}

/* ─────────────────────────────────────────────────────────────
   Mock outputs
───────────────────────────────────────────────────────────── */

const MOCK_NARRATIVE = `The party reached the foot of Weathertop just as the wind began to pull at their cloaks. **Aragorn** crouched low beside the cairn-stones, one gloved hand pressed flat to the earth as though listening for footsteps the rest of them could not feel.

"We rest here," he said. "Not above."

**Pippin** opened his mouth — to protest, by the look of him — and **Sam** caught his elbow without saying anything. **Frodo** stood a little apart, fingers worrying at the chain beneath his shirt. He had not spoken since the river.

### The watchfire and what answered it

They made a low fire in the bowl below the summit, ringed it with stones, and ate cold pork and apples. *Strider* would not eat. He sat on the lip of the dell, eyes fixed northward, and one by one the hobbits dropped into uneasy sleep.

It was Merry who saw them first — five shapes that were a different kind of dark than the night around them, moving in single file along the ridge. He did not cry out. He simply touched Aragorn's wrist, and Aragorn was already on his feet, sword drawn.

### A wound that did not bleed

Frodo did not mean to. He would say so afterwards, to anyone who would listen, and Gandalf would say *I know, my lad, I know* — but the truth he could feel even as the chain slid from his neck, was that the Ring had wanted to be put on. And he had let it.

The world went grey, and the riders had faces.`;

const MOCK_ANALYSIS = `### Consistency check

**Cross-references scanned:** 3 stories, 3 character profiles, 2 NPC files.

#### Findings

**1. Character consistency.** Aragorn is consistently written as decisive and watchful across all three story files. No naming drift detected.

**2. Foreshadowing threads.** The letter from Bree (introduced in 001) is explicitly referenced in 002 and resolves in 003. The map fragment (002) is unresolved — flagged for next session.

#### Themes (frequency, last 3 sessions)

- \`silence\` — 8 mentions, dominant
- \`bell\` — 11 mentions, central
- \`ring\` — 14 mentions, accelerating

#### Pace

Series is averaging **1,600 words / session**. Last session (003) ran longer at 2,400 words — typical of a campaign approaching a mid-arc reveal.`;

const MOCK_SUGGESTIONS = `Three directions for the next session:

**1. The letter is answered.** Gandalf receives a reply to the Bree letter — in a hand none of them recognise, written in a script that the paper seems to absorb rather than hold. Cheapest to run: a quiet moment at camp. Forces the party into a decision before morning.

**2. The map fragment leads somewhere.** The bone whistle found on the goblin captain resonates when held near the map fragment. It points east. This is the most dramatic option — you will need a destination and what waits there.

**3. The ring goes quiet.** For exactly one night, Frodo cannot feel the Ring at all. No weight, no whisper, no pull. He tells no one. It starts again at dawn. Strongest if the players are clever — they will know something changed, and so will you.

My read: **(1)** if the party needs direction, **(2)** if they are restless, **(3)** if you trust them with ambiguity.`;

const MOCK_DC = `**Situation:** Pippin attempting to lift a keyring off a sleeping cave troll.

Recommended check: **DEX (Sleight of Hand)** — DC **18** *(hard)*.

**Why this DC:** A cave troll has passive perception 8 (sleeping: reduced to 6). The keyring is iron and heavy. Pippin's Thief subclass nets +9 — a DC 18 means roughly 65% success, appropriate for "possible but not certain."

**Failure consequences:**
- *Fail by 1–4:* keys jingle; troll stirs but does not wake. One round to retreat before a DC 12 WIS check from the troll.
- *Fail by 5+:* troll wakes mid-grab. Combat begins; troll has advantage on first attack.

**Critical success:** Pippin lifts the keys and finds a bone whistle on the same ring — one rune carved into it (*si-*, Quenya for "silence").`;

function mockForAction(id: string, preset: ActionPreset): string {
  if (preset.mock) return preset.mock;
  if (id === 's-dc') return MOCK_DC;
  if (preset.outputKind === 'analysis') return MOCK_ANALYSIS;
  if (preset.outputKind === 'suggestions') return MOCK_SUGGESTIONS;
  return MOCK_NARRATIVE;
}

/* ─────────────────────────────────────────────────────────────
   ACTION_PRESETS — one entry per work-series AI action
───────────────────────────────────────────────────────────── */

const ACTION_PRESETS: Record<string, ActionPreset> = {
  's-add': {
    label: 'Add new story to series', group: 'Authoring',
    blurb: 'Drafts a session-shaped story from a list of beats. Lands as the next numbered file in the series.',
    model: { name: 'Sonnet · Narrative', task: 'story_generation', tone: 'creative' },
    duration: 16000,
    inputs: [
      { id: 'series', label: 'Series', kind: 'select',
        options: ['Whispers of the Sundered Crown', 'The Ironroot Pact', 'Mistveil Quest'] },
      { id: 'order', label: 'Slot in series', kind: 'select',
        options: ['006 — next story', '003 — between Trollshaws and Weathertop', '— end of series'] },
      { id: 'beats', label: 'Story beats (one per line)', kind: 'textarea', rows: 7,
        placeholder: '- Party reaches Weathertop at dusk\n- Aragorn refuses the summit; they camp in the dell\n- Five riders cross the ridge\n- Frodo puts on the Ring; Morgul wound\n- Aragorn drives them back with fire' },
      { id: 'length', label: 'Length', kind: 'segment',
        options: ['Short (800)', 'Medium (1600)', 'Long (3000)'], default: 'Long (3000)' },
      { id: 'pov', label: 'POV', kind: 'segment',
        options: ['Omniscient', 'Per-character', 'DM voice'], default: 'Omniscient' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--story', path: 'campaigns/example/006_weathertop.md' },
    eventsLog: [
      { t: '00:01', msg: 'Loaded series context (3 stories)' },
      { t: '00:02', msg: 'Loaded party state' },
      { t: '00:03', msg: 'Activated profile: Sonnet · Narrative' },
      { t: '00:04', msg: 'Streaming first paragraph...' },
      { t: '00:07', msg: 'Beat 2/5 covered' },
    ],
  },
  's-session': {
    label: 'Generate session results', group: 'Generation',
    blurb: 'Reads raw session notes and produces a polished session writeup with combat resolution, key events, and per-character development hooks.',
    model: { name: 'Sonnet · Narrative', task: 'story_generation', tone: 'creative' },
    duration: 14000,
    inputs: [
      { id: 'series', label: 'Series', kind: 'select',
        options: ['Whispers of the Sundered Crown', 'The Ironroot Pact', 'Mistveil Quest'] },
      { id: 'session', label: 'Session #', kind: 'select',
        options: ['003 — Trollshaws', '002 — Bree', '001 — Start'] },
      { id: 'rawnotes', label: 'Raw session notes', kind: 'textarea', rows: 6,
        placeholder: 'rough notes, bullet points, dice results, who said what...' },
      { id: 'tone', label: 'Tone', kind: 'segment',
        options: ['Dark', 'Heroic', 'Mystery', 'Comic'], default: 'Dark' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--story', path: 'campaigns/example/003_end.md' },
  },
  's-chardev': {
    label: 'Generate character development', group: 'Generation',
    blurb: 'Drafts an arc-aware character development note: how they changed this session, what they fear, what they want next.',
    model: { name: 'Sonnet · Narrative', task: 'character_development', tone: 'creative' },
    duration: 10000,
    inputs: [
      { id: 'char', label: 'Character', kind: 'select',
        options: ['Aragorn', 'Frodo', 'Gandalf'] },
      { id: 'session', label: 'Session', kind: 'select',
        options: ['003 — Trollshaws', '002 — Bree', '001 — Start'] },
      { id: 'focus', label: 'Focus', kind: 'segment',
        options: ['Inner change', 'Relationships', 'Goals', 'Trauma'], default: 'Inner change' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--character_development', path: 'campaigns/example/dev/003-frodo.md' },
  },
  's-combat': {
    label: 'Combat to narrative', group: 'Generation',
    blurb: 'Converts a dice-log and initiative order into prose. Preserves who hit, who missed, and what mattered.',
    model: { name: 'Sonnet · Narrative', task: 'combat_narrative', tone: 'creative' },
    duration: 9000,
    inputs: [
      { id: 'log', label: 'Combat log (one entry per line)', kind: 'textarea', rows: 8,
        placeholder: 'R1 Aragorn longsword vs Rider1 -> 17 hit 8 dmg\nR1 Frodo Sting -> miss\nR1 Rider1 Morgul blade vs Frodo -> 19 hit 5 dmg\n...' },
      { id: 'style', label: 'Style', kind: 'segment',
        options: ['Tight', 'Cinematic', 'Pulpy'], default: 'Cinematic' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--story section', path: '003_end.md#combat' },
  },
  's-dc': {
    label: 'DC suggestions', group: 'Consult',
    blurb: 'Recommends a difficulty class for an open situation, with rationale and failure consequences.',
    model: { name: 'Haiku · Analysis', task: 'dc_evaluation', tone: 'fast' },
    duration: 6000,
    inputs: [
      { id: 'situation', label: 'Situation', kind: 'textarea', rows: 5,
        placeholder: 'Pippin wants to lift a key off a sleeping cave troll...' },
      { id: 'ability', label: 'Suggested ability', kind: 'segment',
        options: ['Auto', 'STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'], default: 'Auto' },
    ],
    outputKind: 'analysis',
    target: null,
  },
  's-dm': {
    label: 'DM narrative suggestions', group: 'Consult',
    blurb: 'Three beats you could play this scene as, with cost-of-running notes for each.',
    model: { name: 'Sonnet · Narrative', task: 'dm_narrative', tone: 'creative' },
    duration: 8000,
    inputs: [
      { id: 'scene', label: 'Scene', kind: 'textarea', rows: 5,
        placeholder: 'The party has just returned to Bree; the gate is unguarded...' },
      { id: 'mood', label: 'Mood', kind: 'segment',
        options: ['Tense', 'Eerie', 'Hopeful', 'Comedic'], default: 'Eerie' },
    ],
    outputKind: 'suggestions',
    target: null,
  },
  's-suggest': {
    label: 'AI story suggestions', group: 'Consult',
    blurb: 'Three plot directions the campaign could take next session, each with a cheap and a dramatic version.',
    model: { name: 'Sonnet · Narrative', task: 'story_suggestion', tone: 'creative' },
    duration: 8000,
    inputs: [
      { id: 'series', label: 'Series', kind: 'select',
        options: ['Whispers of the Sundered Crown', 'The Ironroot Pact', 'Mistveil Quest'] },
      { id: 'mood', label: 'Where the party left off', kind: 'segment',
        options: ['Restless', 'Tired', 'Clever', 'Wounded'], default: 'Restless' },
    ],
    outputKind: 'suggestions',
    target: null,
  },
  's-analyze': {
    label: 'Analyze single story', group: 'Analysis',
    blurb: 'Pulls themes, character beats, and consistency notes out of one story file.',
    model: { name: 'Haiku · Analysis', task: 'story_analysis', tone: 'fast' },
    duration: 7000,
    inputs: [
      { id: 'story', label: 'Story', kind: 'select',
        options: ['003 — Trollshaws', '002 — Bree', '001 — Start'] },
      { id: 'depth', label: 'Depth', kind: 'segment',
        options: ['Shallow', 'Standard', 'Deep'], default: 'Standard' },
    ],
    outputKind: 'analysis',
    target: { kind: 'node--analysis_report', path: 'cache/analysis/003_end.json' },
  },
  's-story-anal': {
    label: 'Series consistency analysis', group: 'Analysis', slow: true,
    blurb: 'Reads every story in the series and looks for naming drift, contradictions, unresolved foreshadowing, and theme drift.',
    model: { name: 'Sonnet · Deep Arc', task: 'series_analysis', tone: 'deep' },
    duration: 22000,
    inputs: [
      { id: 'series', label: 'Series', kind: 'select',
        options: ['Whispers of the Sundered Crown', 'The Ironroot Pact', 'Mistveil Quest'] },
      { id: 'scope', label: 'Scope', kind: 'segment',
        options: ['Last 5', 'Last 10', 'All'], default: 'All' },
    ],
    outputKind: 'analysis',
    target: { kind: 'node--series_report', path: 'cache/analysis/example-series.json' },
  },
  's-char-anal': {
    label: 'Character analysis', group: 'Analysis', slow: true,
    blurb: 'Builds an arc report across every appearance: how they have changed, what they want, where the player has driven them.',
    model: { name: 'Sonnet · Deep Arc', task: 'character_analysis', tone: 'deep' },
    duration: 24000,
    inputs: [
      { id: 'char', label: 'Character', kind: 'select',
        options: ['Aragorn', 'Frodo', 'Gandalf'] },
      { id: 'scope', label: 'Scope', kind: 'segment',
        options: ['Recent arc', 'Full campaign'], default: 'Full campaign' },
    ],
    outputKind: 'analysis',
    target: { kind: 'node--character_report', path: 'cache/analysis/frodo-arc.json' },
  },
  's-amend': {
    label: 'Amend story actions', group: 'Authoring',
    blurb: 'Edit who did what in a session — change a name, correct a roll, swap a beat. AI can rewrite affected prose to match.',
    model: { name: 'Sonnet · Narrative', task: 'story_amend', tone: 'creative' },
    duration: 9000,
    inputs: [
      { id: 'story', label: 'Story', kind: 'select',
        options: ['003 — Trollshaws', '002 — Bree', '001 — Start'] },
      { id: 'find', label: 'Find', kind: 'textarea', rows: 3,
        placeholder: 'It was Sam who saw them first' },
      { id: 'change', label: 'Change to', kind: 'textarea', rows: 3,
        placeholder: 'It was Merry who saw them first' },
      { id: 'sweep', label: 'AI rewrite sweep', kind: 'segment',
        options: ['None', 'Affected paragraph', 'Whole scene'], default: 'Affected paragraph' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--story', path: 'campaigns/example/003_end.md' },
  },
};

/* ─────────────────────────────────────────────────────────────
   useAiRun — simulated phased streaming (setup → running → done)
───────────────────────────────────────────────────────────── */

type RunPhase = 'setup' | 'running' | 'done';

interface AiRunState {
  phase: RunPhase;
  streamed: string;
  progress: number;
  elapsed: number;
  tokens: number;
  tokensPerSec: number;
  events: EventEntry[];
  start: () => void;
  cancel: () => void;
  reset: () => void;
}

function useAiRun(actionId: string): AiRunState {
  const preset = ACTION_PRESETS[actionId];
  const totalDuration = preset?.duration ?? 10000;
  const fullText = preset ? mockForAction(actionId, preset) : MOCK_NARRATIVE;
  const tickMs = 50;

  const [phase, setPhase]                 = React.useState<RunPhase>('setup');
  const [streamed, setStreamed]           = React.useState('');
  const [progress, setProgress]           = React.useState(0);
  const [elapsed, setElapsed]             = React.useState(0);
  const [tokens, setTokens]               = React.useState(0);
  const [tokensPerSec, setTPS]            = React.useState(0);
  const [events, setEvents]               = React.useState<EventEntry[]>([]);
  const timerRef                           = React.useRef<ReturnType<typeof setInterval> | null>(null);

  const stopTimer = (): void => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  React.useEffect(() => stopTimer, []);

  const start = React.useCallback((): void => {
    stopTimer();
    setPhase('running');
    setStreamed('');
    setProgress(0);
    setElapsed(0);
    setTokens(0);
    setTPS(0);
    setEvents([]);

    const t0 = Date.now();
    const presetEvents = (preset?.eventsLog ?? []).slice();

    timerRef.current = setInterval(() => {
      const eMs  = Date.now() - t0;
      const eSec = eMs / 1000;
      setElapsed(eSec);
      const p = Math.min(1, eMs / totalDuration);
      setProgress(p);
      const target = Math.floor(p * fullText.length);
      setStreamed(fullText.slice(0, target));
      const toks = Math.floor(target / 4.5);
      setTokens(toks);
      setTPS(eSec > 0.1 ? Math.floor(toks / eSec) : 0);

      while (presetEvents.length > 0) {
        const next = presetEvents[0];
        const [mm, ss] = next.t.split(':').map(Number);
        if ((mm ?? 0) * 60 + (ss ?? 0) <= eSec) {
          presetEvents.shift();
          setEvents(ev => [...ev, next]);
        } else {
          break;
        }
      }

      if (p >= 1) {
        stopTimer();
        setPhase('done');
      }
    }, tickMs);
  }, [actionId, fullText, preset, totalDuration]);

  const cancel = React.useCallback((): void => {
    stopTimer();
    setPhase('setup');
    setStreamed('');
    setProgress(0);
    setElapsed(0);
    setTokens(0);
    setTPS(0);
  }, []);

  const reset = React.useCallback((): void => {
    stopTimer();
    setPhase('setup');
    setStreamed('');
  }, []);

  return { phase, streamed, progress, elapsed, tokens, tokensPerSec, events, start, cancel, reset };
}

/* ─────────────────────────────────────────────────────────────
   AiFormControl — select / textarea / segment / text
───────────────────────────────────────────────────────────── */

interface FormControlProps {
  input: InputSpec;
  value: string | undefined;
  onChange: (v: string) => void;
}

function AiFormControl({ input, value, onChange }: FormControlProps): React.ReactElement {
  if (input.kind === 'select') {
    const opts = input.options ?? [];
    return (
      <select
        value={value ?? opts[0] ?? ''}
        onChange={e => { onChange(e.target.value); }}
      >
        {opts.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    );
  }

  if (input.kind === 'textarea') {
    return (
      <textarea
        rows={input.rows ?? 4}
        placeholder={input.placeholder}
        value={value ?? ''}
        onChange={e => { onChange(e.target.value); }}
      />
    );
  }

  if (input.kind === 'segment') {
    const opts = input.options ?? [];
    const active = value ?? input.default ?? opts[0] ?? '';
    return (
      <div className="seg-control">
        {opts.map(o => (
          <button
            key={o}
            type="button"
            className={`seg${active === o ? ' active' : ''}`}
            onClick={() => { onChange(o); }}
          >
            {o}
          </button>
        ))}
      </div>
    );
  }

  return (
    <input
      type="text"
      value={value ?? ''}
      onChange={e => { onChange(e.target.value); }}
      placeholder={input.placeholder}
    />
  );
}

/* ─────────────────────────────────────────────────────────────
   AiStreamBody — renders markdown-ish streamed text
───────────────────────────────────────────────────────────── */

interface StreamBodyProps {
  text: string;
  caret: boolean;
}

function renderInline(s: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const re = /\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`/g;
  let m: RegExpExecArray | null;
  let last = 0;
  while ((m = re.exec(s)) !== null) {
    if (m.index > last) parts.push(s.slice(last, m.index));
    if (m[1] !== undefined) parts.push(<strong key={parts.length}>{m[1]}</strong>);
    else if (m[2] !== undefined) parts.push(<em key={parts.length}>{m[2]}</em>);
    else if (m[3] !== undefined) parts.push(<span key={parts.length} className="ai-mono">{m[3]}</span>);
    last = re.lastIndex;
  }
  if (last < s.length) parts.push(s.slice(last));
  return parts;
}

function AiStreamBody({ text, caret }: StreamBodyProps): React.ReactElement {
  const blocks = text.split(/\n{2,}/).filter(Boolean);
  return (
    <div className="ai-stream">
      {blocks.map((blk, i) => {
        const isLast = i === blocks.length - 1;
        if (blk.startsWith('### ')) {
          return (
            <h3 key={i}>
              {renderInline(blk.slice(4))}
              {caret && isLast && <span className="caret" />}
            </h3>
          );
        }
        if (blk.startsWith('#### ')) {
          return (
            <h3 key={i} style={{ fontSize: 12 }}>
              {renderInline(blk.slice(5))}
              {caret && isLast && <span className="caret" />}
            </h3>
          );
        }
        return (
          <p key={i}>
            {renderInline(blk)}
            {caret && isLast && <span className="caret" />}
          </p>
        );
      })}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   AiActionWorkbench — V1: form left, streaming result right
───────────────────────────────────────────────────────────── */

interface ActionScreenProps {
  actionId: string;
  ctx: ScreenProps['ctx'];
  setCtx: ScreenProps['setCtx'];
  entry: string;
}

function AiActionWorkbench({ actionId, ctx, setCtx, entry }: ActionScreenProps): React.ReactElement {
  const preset = ACTION_PRESETS[actionId];
  const [formValues, setFormValues] = React.useState<Record<string, string>>({});
  const [toast, setToast]           = React.useState<{ tag: string; path: string } | null>(null);
  const run = useAiRun(actionId);

  if (preset === undefined) {
    return <div className="screen-blurb">Unknown action: {actionId}</div>;
  }

  const setField = (id: string, v: string): void => {
    setFormValues(o => ({ ...o, [id]: v }));
  };

  const goBack = (): void => {
    setCtx({ ...ctx, workSeriesAction: null });
  };

  const onAccept = (): void => {
    setToast({ tag: 'Saved to Drupal', path: preset.target?.path ?? 'campaigns/example/' });
    setTimeout(() => { setToast(null); }, 4200);
  };

  const statusClass = run.phase === 'running' ? 'running' : run.phase === 'done' ? 'done' : 'idle';
  const statusLabel = run.phase === 'running' ? 'Streaming' : run.phase === 'done' ? 'Complete' : 'Ready';

  return (
    <div className="screen-aiaction">
      <div className="action-back-row">
        <button type="button" className="action-back" onClick={goBack}>
          <Icon name="chevronLeft" size={11} /> Back to series workspace
        </button>
        <span className="action-entry-pip">
          <span className="dot" />
          Opened from {entry === 'session' ? 'Session Reader - End of chronicle' : 'Series workspace'}
        </span>
      </div>

      <header className="screen-head" style={{ marginBottom: 16, paddingBottom: 12 }}>
        <div>
          <span className="reader-eyebrow">
            {preset.group} <AiTag />
          </span>
          <h2>
            {preset.label}
            {preset.slow === true && <SlowTag />}
          </h2>
          <p className="screen-blurb">{preset.blurb}</p>
        </div>
      </header>

      <div className="ai-workbench">
        <aside className="ai-form-pane">
          <h3><Icon name="gear" size={11} /> Setup</h3>

          {preset.inputs.map(inp => (
            <div key={inp.id} className="ai-form-row">
              <label>{inp.label}</label>
              <AiFormControl
                input={inp}
                value={formValues[inp.id]}
                onChange={v => { setField(inp.id, v); }}
              />
            </div>
          ))}

          <dl className="ai-model-readout">
            <dt>Model</dt><dd>{preset.model.name}</dd>
            <dt>Task</dt><dd><em>{preset.model.task}</em></dd>
            {preset.target !== null && <><dt>Lands as</dt><dd>{preset.target.kind}</dd></>}
            {preset.target !== null && <><dt>Path</dt><dd className="mono">{preset.target.path}</dd></>}
          </dl>

          <div className="ai-form-foot">
            {run.phase === 'setup' && (
              <button type="button" className="ai-run-btn" onClick={run.start}>
                <Icon name="sparkle" size={11} /> Run
              </button>
            )}
            {run.phase === 'running' && (
              <button
                type="button"
                className="ai-run-btn"
                onClick={run.cancel}
                style={{ background: 'var(--color-danger)', borderColor: 'var(--color-danger)', color: 'var(--parchment)' }}
              >
                <Icon name="close" size={11} /> Cancel
              </button>
            )}
            {run.phase === 'done' && (
              <button type="button" className="ai-run-btn" onClick={run.start}>
                <Icon name="sparkle" size={11} /> Re-run with same inputs
              </button>
            )}
            <p className="ai-form-tip">
              Edits to inputs apply on next run. Result is not saved until you accept it.
            </p>
          </div>
        </aside>

        <section className="ai-result-pane">
          <div className="ai-result-bar">
            <div className="ai-result-status">
              <span className={`ai-status-dot ${statusClass}`} />
              <span className="ai-status-label">{statusLabel}</span>
            </div>
            <div className="ai-status-meta">
              {run.phase !== 'setup' && <span>elapsed <b>{run.elapsed.toFixed(1)}s</b></span>}
              {run.phase !== 'setup' && <span>tokens <b>{run.tokens.toLocaleString()}</b></span>}
              {run.phase === 'running' && <span><b>{run.tokensPerSec}</b>/s</span>}
              {run.phase === 'running' && <span>progress <b>{Math.round(run.progress * 100)}%</b></span>}
            </div>
          </div>

          <div className="ai-result-canvas">
            {run.phase === 'setup' ? (
              <div className="ai-result-empty">
                <span className="glyph"><Icon name="sparkle" size={22} /></span>
                <h4>Ready when you are</h4>
                <p>
                  Fill the form on the left and hit <b>Run</b>. The result will stream in here.
                  Nothing is written to your campaign until you accept it.
                </p>
              </div>
            ) : (
              <AiStreamBody text={run.streamed} caret={run.phase === 'running'} />
            )}
          </div>

          {run.phase === 'done' && (
            <div className="ai-result-foot">
              <div className="ai-result-foot-left">
                <span className="ai-result-foot-target">
                  {preset.target !== null
                    ? <>Will save as <b>{preset.target.kind}</b> &middot; <span className="mono">{preset.target.path}</span></>
                    : 'Consult-only — not saved to Drupal'}
                </span>
                <span className="ai-result-foot-hint">
                  {preset.target !== null
                    ? 'Discard to throw it away. Accept to push to Drupal and add to the chronicle.'
                    : 'You can copy this into your notes.'}
                </span>
              </div>
              <div className="ai-result-foot-right">
                <button type="button" className="ghost-btn" onClick={run.reset}>Discard</button>
                <button type="button" className="ghost-btn" onClick={run.start}>
                  <Icon name="sparkle" size={11} /> Regenerate
                </button>
                {preset.target !== null && (
                  <button type="button" className="ai-accept-btn" onClick={onAccept}>
                    <Icon name="plus" size={11} /> Accept &amp; save
                  </button>
                )}
              </div>
            </div>
          )}
        </section>
      </div>

      {toast !== null && (
        <div className="ai-toast">
          <span className="toast-tag">&#10003; {toast.tag}</span>
          <span className="toast-path">{toast.path}</span>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   AiActionForge — V2: 3-phase stepper (Setup / Stream / Artifact)
───────────────────────────────────────────────────────────── */

function AiActionForge({ actionId, ctx, setCtx, entry }: ActionScreenProps): React.ReactElement {
  const preset = ACTION_PRESETS[actionId];
  const [formValues, setFormValues] = React.useState<Record<string, string>>({});
  const [toast, setToast]           = React.useState<{ tag: string; path: string } | null>(null);
  const run = useAiRun(actionId);

  if (preset === undefined) {
    return <div className="screen-blurb">Unknown action: {actionId}</div>;
  }

  const setField = (id: string, v: string): void => {
    setFormValues(o => ({ ...o, [id]: v }));
  };

  const goBack = (): void => {
    setCtx({ ...ctx, workSeriesAction: null });
  };

  const onAccept = (): void => {
    setToast({ tag: 'Saved to Drupal', path: preset.target?.path ?? 'campaigns/example/' });
    setTimeout(() => { setToast(null); }, 4200);
  };

  const stepClass = (id: 'setup' | 'stream' | 'result'): string => {
    if (run.phase === 'setup') return id === 'setup' ? 'is-active' : '';
    if (run.phase === 'running') {
      if (id === 'setup') return 'is-done';
      if (id === 'stream') return 'is-active';
      return '';
    }
    if (id === 'setup') return 'is-done';
    if (id === 'stream') return 'is-done';
    return 'is-active';
  };

  return (
    <div className="screen-aiaction">
      <div className="action-back-row">
        <button type="button" className="action-back" onClick={goBack}>
          <Icon name="chevronLeft" size={11} /> Back to series workspace
        </button>
        <span className="action-entry-pip">
          <span className="dot" />
          Opened from {entry === 'session' ? 'Session Reader - End of chronicle' : 'Series workspace'}
        </span>
      </div>

      <header className="screen-head" style={{ marginBottom: 12, paddingBottom: 10 }}>
        <div>
          <span className="reader-eyebrow">
            {preset.group} <AiTag />
          </span>
          <h2>
            {preset.label}
            {preset.slow === true && <SlowTag />}
          </h2>
          <p className="screen-blurb">{preset.blurb}</p>
        </div>
      </header>

      <div className="ai-forge">
        <div className="forge-stepper">
          <div className={`forge-step ${stepClass('setup')}`}><span className="num">1</span> Setup</div>
          <div className="step-rule" />
          <div className={`forge-step ${stepClass('stream')}`}><span className="num">2</span> Generate</div>
          <div className="step-rule" />
          <div className={`forge-step ${stepClass('result')}`}><span className="num">3</span> Review &amp; accept</div>
        </div>

        <div className="forge-canvas">
          {run.phase === 'setup' && (
            <div className="forge-setup">
              <span className="reader-eyebrow">Step 1 &middot; {preset.group}</span>
              <h3>{preset.label}</h3>
              <p className="forge-blurb">{preset.blurb}</p>

              {preset.inputs.map(inp => (
                <div key={inp.id} className="ai-form-row">
                  <label>{inp.label}</label>
                  <AiFormControl
                    input={inp}
                    value={formValues[inp.id]}
                    onChange={v => { setField(inp.id, v); }}
                  />
                </div>
              ))}

              <dl className="ai-model-readout" style={{ marginTop: 8 }}>
                <dt>Model</dt><dd>{preset.model.name}</dd>
                <dt>Task</dt><dd><em>{preset.model.task}</em></dd>
                {preset.target !== null && (
                  <><dt>Lands as</dt><dd>{preset.target.kind} &middot; <span className="mono">{preset.target.path}</span></dd></>
                )}
              </dl>

              <div className="forge-launch">
                <p className="ai-form-tip" style={{ margin: 0 }}>
                  The model is chosen automatically by task. Result is not saved until you accept it.
                </p>
                <button type="button" className="ai-run-btn" onClick={run.start}>
                  <Icon name="sparkle" size={12} /> Forge
                </button>
              </div>
            </div>
          )}

          {run.phase === 'running' && (
            <div className="forge-stream">
              <div className="forge-stream-body">
                <AiStreamBody text={run.streamed} caret />
              </div>
              <aside className="forge-meter">
                <h4>Live</h4>
                <div className="meter-row">
                  <span className="meter-label">Progress</span>
                  <div className="meter-progress">
                    <span className="meter-progress-fill" style={{ width: `${Math.round(run.progress * 100)}%` }} />
                  </div>
                  <span className="meter-sub">{Math.round(run.progress * 100)}% &middot; {run.elapsed.toFixed(1)}s</span>
                </div>
                <div className="meter-row">
                  <span className="meter-label">Tokens</span>
                  <span className="meter-val">{run.tokens.toLocaleString()}</span>
                  <span className="meter-sub">{run.tokensPerSec}/s</span>
                </div>
                <div className="meter-row">
                  <span className="meter-label">Model</span>
                  <span className="meter-sub" style={{ color: 'var(--color-gold-bright)', fontSize: 12 }}>
                    {preset.model.name}
                  </span>
                </div>
                <h4 style={{ marginTop: 6 }}>Events</h4>
                <ul className="meter-events">
                  {run.events.length === 0 && (
                    <li style={{ fontStyle: 'italic' }}><span className="t">—</span> waiting on first token...</li>
                  )}
                  {run.events.map((ev, i) => (
                    <li key={i}><span className="t">{ev.t}</span>{ev.msg}</li>
                  ))}
                </ul>
                <button type="button" className="meter-cancel" onClick={run.cancel}>Cancel run</button>
              </aside>
            </div>
          )}

          {run.phase === 'done' && (
            <div className="forge-artifact">
              <header className="forge-artifact-head">
                <div>
                  <span className="reader-eyebrow">Step 3 &middot; Ready to review</span>
                  <h3>{preset.label}</h3>
                  <div className="forge-artifact-meta">
                    <span><b>{run.tokens.toLocaleString()}</b> tokens</span>
                    <span><b>{run.elapsed.toFixed(1)}s</b> elapsed</span>
                    <span>model &middot; <b>{preset.model.name}</b></span>
                    {preset.target !== null && <span>target &middot; <b>{preset.target.kind}</b></span>}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <button type="button" className="ghost-btn ghost-small" onClick={run.reset}>Edit inputs</button>
                </div>
              </header>
              <div className="forge-artifact-body">
                <AiStreamBody text={run.streamed} caret={false} />
              </div>
              <div className="ai-result-foot">
                <div className="ai-result-foot-left">
                  <span className="ai-result-foot-target">
                    {preset.target !== null
                      ? <>Will save as <b>{preset.target.kind}</b> &middot; <span className="mono">{preset.target.path}</span></>
                      : 'Consult-only — not saved to Drupal'}
                  </span>
                  <span className="ai-result-foot-hint">
                    {preset.target !== null
                      ? 'Discard to throw it away. Accept to push to Drupal and add to the chronicle.'
                      : 'You can copy this into your notes.'}
                  </span>
                </div>
                <div className="ai-result-foot-right">
                  <button type="button" className="ghost-btn" onClick={run.reset}>Discard</button>
                  <button type="button" className="ghost-btn" onClick={run.start}>
                    <Icon name="sparkle" size={11} /> Regenerate
                  </button>
                  {preset.target !== null && (
                    <button type="button" className="ai-accept-btn" onClick={onAccept}>
                      <Icon name="plus" size={11} /> Accept &amp; save
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {toast !== null && (
        <div className="ai-toast">
          <span className="toast-tag">&#10003; {toast.tag}</span>
          <span className="toast-path">{toast.path}</span>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   AiActionScreen — dispatcher (chooses variant from ctx.aiLayout)
───────────────────────────────────────────────────────────── */

export function AiActionScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const actionId = (ctx.workSeriesAction as string | undefined) ?? 's-session';
  const variant  = (ctx.aiLayout as string | undefined) ?? 'workbench';
  const entry    = (ctx._entryFrom as string | undefined) ?? 'workspace';

  if (variant === 'forge') {
    return <AiActionForge actionId={actionId} ctx={ctx} setCtx={setCtx} entry={entry} />;
  }
  return <AiActionWorkbench actionId={actionId} ctx={ctx} setCtx={setCtx} entry={entry} />;
}
