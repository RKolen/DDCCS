/* ============================================================
   Story Series AI action template — shared screen for 11 of the
   13 work-series submenu items (s-add, s-session, s-chardev,
   s-combat, s-dc, s-dm, s-suggest, s-analyze, s-story-anal,
   s-char-anal, s-amend).

   Two variations (selected via Tweaks panel):
     - 'workbench' (V1): form left, live result right, parallel
     - 'forge'     (V2): full-canvas three-phase progression

   Both share the same useAiRun hook and ACTION_PRESETS data.
   ============================================================ */

const { useState, useEffect, useMemo, useRef } = React;

/* ────────────────────────────────────────────────────────────
   Mock streamed outputs — three "shapes" matching what each
   work-series action returns. Real wiring will replace these
   with AI streams from the worker.
   ──────────────────────────────────────────────────────────── */

const MOCK_NARRATIVE = `
The party reached the foot of Weathertop just as the wind began to pull at their cloaks. **Aragorn** crouched low beside the cairn-stones, one gloved hand pressed flat to the earth as though listening for footsteps the rest of them could not feel.

"We rest here," he said. "Not above."

**Pippin** opened his mouth — to protest, by the look of him — and **Sam** caught his elbow without saying anything. **Frodo** stood a little apart, fingers worrying at the chain beneath his shirt. He had not spoken since the river.

### The watchfire and what answered it

They made a low fire in the bowl below the summit, ringed it with stones, and ate cold pork and apples. *Strider* would not eat. He sat on the lip of the dell, eyes fixed northward, and one by one the hobbits dropped into uneasy sleep.

It was Merry who saw them first — five shapes that were a different kind of dark than the night around them, moving in single file along the ridge. He did not cry out. He simply touched Aragorn's wrist, and Aragorn was already on his feet, sword drawn.

"Stay close," he said. "Do not draw blade unless I tell you. Do not look at their faces. And whatever you do, *do not put on the Ring.*"

### A wound that did not bleed

Frodo did not mean to. He would say so afterwards, to anyone who would listen, and Gandalf would say *I know, my lad, I know* — but the truth, the truth he could feel even as the chain slid from his neck, was that the Ring had wanted to be put on. And he had let it.

The world went grey, and the riders had faces.

The blade that took him in the shoulder was the colour of cold iron. He felt nothing at first. Then he felt everything, all at once, and the cry that left him was not a cry his friends could answer — not on this side of the Veil.

Aragorn was already swinging the brand from the fire, and *Sting* was loose in Sam's hand, and Merry was screaming Frodo's name into the dark, and *the riders had drawn back as though the firelight burned them.* But Frodo lay on the stones with the Ring still warm against his palm, and a chill spreading from his shoulder like ink in still water.
`.trim();

const MOCK_ANALYSIS = `
### Consistency check — *Whispers of the Sundered Crown*

**Cross-references scanned:** 12 stories · 4 character profiles · 7 NPC files · 2 location notes.

#### Findings

**1. Bell of Vellishar — naming drift.** The bell is called *the Bell of Vellishar* in stories 003 and 007, but rendered as *the Vellishar Bell* in 004 and 009. Suggest canonical form: **Bell of Vellishar**. Auto-fix available.

**2. Vesper's sister — unresolved foreshadowing.** Introduced in story 002 (line 47, "Mira, before the smoke") and again referenced in 005, 008. No story file has yet *resolved* whether she is alive, dead, or — per Vesper's fear in the consultation transcripts — bait left by the Cult. Suggest tagging this thread for next session's hooks.

**3. Aragorn's blade.** In 004 you write *"Andúril"*; in 006 you write *"the broken blade"*. If the reforging has happened, 006 should be amended. If it has not, 004 is the contradiction.

#### Themes (frequency, last-5 sessions)

- ${'`'}bargain${'`'} — 9 mentions, rising
- ${'`'}silence${'`'} — 14 mentions, dominant
- ${'`'}price already paid${'`'} — 6 mentions, accelerating
- ${'`'}sister${'`'} — 11 mentions, plateaued
- ${'`'}bell${'`'} — 22 mentions, central

#### Pace

Series is averaging **1,840 words / session**, with the last three sessions trending up (2,100 / 2,400 / 2,640). This is typical of a campaign approaching its mid-arc reveal. *Recommend* one shorter session (≤1,200 words) before the next major beat to let the party breathe.
`.trim();

const MOCK_SUGGESTIONS = `
Three directions for the next session — pick one (or none, the campaign is yours):

**1. The Ledger names a name.**  Vesper, alone in the inn at Bree, opens *A Ledger of Names* and finds her sister's handwriting on a page that was blank yesterday. The page reads simply: *I am still here. He hears the bells.* This is the cheapest scene to run — it costs you only a quiet room and a candle, but the party's next argument is essentially forced for you.

**2. Smoke at the Northgate, revisited.**  The party returns to find the gate intact, the smoke gone, and the *guards* gone — every one of them, *replaced* by men in identical dark cloaks who all answer to the same name. This is the most dramatic and most expensive option; you'll need NPC stat blocks for the substitutes and a clear escape route the party can find under pressure.

**3. The bell answers a question it was not asked.**  At a moment of the party's choice — *not yours* — a bell rings in the distance. Whoever they were just talking to falls silent, looks toward the sound, and says *"It heard you."* Cheap to set up; expensive to follow through, because you'll need to decide *what* it heard. Strongest if their last conversation was a secret.

— My read: **(2)** if the players are restless, **(1)** if they are tired, **(3)** if they are clever and you trust them with rope.
`.trim();

const MOCK_DC = `
**Situation:** *Pippin attempting to lift a sleeping cave troll's keyring without waking it.*

Recommended check: **DEX (Sleight of Hand)** — DC **18** *(hard)*.

**Why this DC:**
- A cave troll has passive perception 8 (sleeping: 6).
- The keyring is iron, heavy, and on a belt that rises and falls with breath.
- Pippin has prof + DEX expertise from Thief subclass — net +9. A DC 18 means a 65% success rate with a single die, which feels right for "the heroes can do it, but it's not a foregone conclusion."

**Failure consequences (suggested):**
- *Fail by 1–4:* the keys jingle. Troll snores deeper, then stills. Pippin has one round to retreat before WIS (Perception) DC 12 from the troll.
- *Fail by 5+:* troll wakes mid-grab. Combat begins with the troll having advantage on its first attack; party rolls initiative.

**Critical success:** Pippin lifts the keys *and* something he didn't expect to see — a small bone whistle on the same ring, carved with a single rune (*sí-*, "silence"). The rune is Quenya. Investigation later.
`.trim();

/* Different "shape" presets for the 13 work-series actions.
   `inputs` describes the setup form. `model`, `output`, etc.
   are read by the screen for the streaming + result display. */
const ACTION_PRESETS = {
  's-add': {
    label: 'Add new story to series',
    group: 'Authoring',
    blurb: 'Drafts a session-shaped story from a list of beats. Lands as the next numbered file in the series.',
    model: { name: 'Sonnet · Narrative', task: 'story_generation', tone: 'creative' },
    duration: 16000,
    inputs: [
      { id: 'series',    label: 'Series',        kind: 'select', options: ['Whispers of the Sundered Crown', 'The Ironroot Pact', 'Mistveil Quest'] },
      { id: 'order',     label: 'Slot in series', kind: 'select', options: ['006 — next story', '003 — between Trollshaws and Weathertop', '— end of series'] },
      { id: 'beats',     label: 'Story beats (one per line)', kind: 'textarea', rows: 7,
        placeholder: '- Party reaches Weathertop at dusk\n- Aragorn refuses the summit; they camp in the dell\n- Five riders cross the ridge\n- Frodo puts on the Ring; Morgul wound\n- Aragorn drives them back with fire' },
      { id: 'length',    label: 'Length',        kind: 'segment', options: ['Short (800)', 'Medium (1600)', 'Long (3000)'], default: 'Long (3000)' },
      { id: 'pov',       label: 'POV',           kind: 'segment', options: ['Omniscient', 'Per-character', 'DM voice'], default: 'Omniscient' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--story', path: 'campaigns/whispers/006_weathertop.md' },
    eventsLog: [
      { t: '00:01', msg: 'Loaded series context (12 stories, 1.84M chars)' },
      { t: '00:02', msg: 'Loaded party state from session 14' },
      { t: '00:03', msg: 'Activated profile: Sonnet · Narrative' },
      { t: '00:04', msg: 'Streaming first paragraph…' },
      { t: '00:07', msg: 'Beat 2/5 covered — Aragorn refuses summit' },
      { t: '00:11', msg: 'Beat 3/5 covered — riders crossing ridge' },
      { t: '00:14', msg: 'Beat 4/5 — Morgul blade strike' },
    ],
  },
  's-session': {
    label: 'Generate session results',
    group: 'Generation',
    blurb: 'Reads raw session notes and produces a polished session writeup with combat resolution, key events, and per-character development hooks.',
    model: { name: 'Sonnet · Narrative', task: 'story_generation', tone: 'creative' },
    duration: 14000,
    inputs: [
      { id: 'series',  label: 'Series',  kind: 'select', options: ['Whispers of the Sundered Crown', 'The Ironroot Pact', 'Mistveil Quest'] },
      { id: 'session', label: 'Session #', kind: 'select', options: ['14 — Weathertop', '15 — Flight to the Ford'] },
      { id: 'rawnotes', label: 'Raw session notes', kind: 'textarea', rows: 6,
        placeholder: 'rough notes, bullet points, dice results, who said what…' },
      { id: 'tone',    label: 'Tone',    kind: 'segment', options: ['Dark', 'Heroic', 'Mystery', 'Comic'], default: 'Dark' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--story', path: 'campaigns/whispers/014_weathertop.md' },
  },
  's-chardev': {
    label: 'Generate character development',
    group: 'Generation',
    blurb: 'Drafts an arc-aware character development note: how they changed this session, what they fear, what they want next.',
    model: { name: 'Sonnet · Narrative', task: 'character_development', tone: 'creative' },
    duration: 10000,
    inputs: [
      { id: 'char',    label: 'Character', kind: 'select', options: ['Aragorn', 'Frodo', 'Gandalf', 'Legolas', 'Samwise', 'Merry', 'Pippin', 'Boromir'] },
      { id: 'session', label: 'Session', kind: 'select', options: ['14 — Weathertop', '13 — Bree', '12 — Trollshaws'] },
      { id: 'focus',   label: 'Focus', kind: 'segment', options: ['Inner change', 'Relationships', 'Goals', 'Trauma'], default: 'Inner change' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--character_development', path: 'campaigns/whispers/dev/014-frodo.md' },
  },
  's-combat': {
    label: 'Combat → narrative',
    group: 'Generation',
    blurb: 'Converts a dice-log + initiative order into prose. Preserves who hit, who missed, and what mattered.',
    model: { name: 'Sonnet · Narrative', task: 'combat_narrative', tone: 'creative' },
    duration: 9000,
    inputs: [
      { id: 'log',   label: 'Combat log (one entry per line)', kind: 'textarea', rows: 8,
        placeholder: 'R1 Aragorn longsword vs Rider1 -> 17 hit 8 dmg\nR1 Frodo Sting -> miss\nR1 Rider1 Morgul blade vs Frodo -> 19 hit 5 dmg + WIS save DC 15 fail\n…' },
      { id: 'style', label: 'Style', kind: 'segment', options: ['Tight', 'Cinematic', 'Pulpy'], default: 'Cinematic' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--story · section', path: '014_weathertop.md#combat' },
  },
  's-dc': {
    label: 'DC suggestions',
    group: 'Consult',
    blurb: 'Recommends a difficulty class for an open situation, with rationale and failure consequences.',
    model: { name: 'Haiku · Analysis', task: 'dc_evaluation', tone: 'fast' },
    duration: 6000,
    inputs: [
      { id: 'situation', label: 'Situation', kind: 'textarea', rows: 5,
        placeholder: 'Pippin wants to lift a key off a sleeping cave troll…' },
      { id: 'ability',   label: 'Suggested ability', kind: 'segment', options: ['Auto', 'STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'], default: 'Auto' },
    ],
    outputKind: 'analysis',
    mock: MOCK_DC,
    target: null,
  },
  's-dm': {
    label: 'DM narrative suggestions',
    group: 'Consult',
    blurb: 'Three beats you could play this scene as, with cost-of-running notes for each.',
    model: { name: 'Sonnet · Narrative', task: 'dm_narrative', tone: 'creative' },
    duration: 8000,
    inputs: [
      { id: 'scene', label: 'Scene', kind: 'textarea', rows: 5,
        placeholder: 'The party has just returned to Bree; the gate is unguarded…' },
      { id: 'mood',  label: 'Mood',  kind: 'segment', options: ['Tense', 'Eerie', 'Hopeful', 'Comedic'], default: 'Eerie' },
    ],
    outputKind: 'suggestions',
    mock: MOCK_SUGGESTIONS,
    target: null,
  },
  's-suggest': {
    label: 'AI story suggestions',
    group: 'Consult',
    blurb: 'Three plot directions the campaign could take next session, each with a cheap and a dramatic version.',
    model: { name: 'Sonnet · Narrative', task: 'story_suggestion', tone: 'creative' },
    duration: 8000,
    inputs: [
      { id: 'series', label: 'Series', kind: 'select', options: ['Whispers of the Sundered Crown', 'The Ironroot Pact', 'Mistveil Quest'] },
      { id: 'mood',   label: 'Where the party left off', kind: 'segment', options: ['Restless', 'Tired', 'Clever', 'Wounded'], default: 'Restless' },
    ],
    outputKind: 'suggestions',
    mock: MOCK_SUGGESTIONS,
    target: null,
  },
  's-analyze': {
    label: 'Analyze single story',
    group: 'Analysis',
    blurb: 'Pulls themes, character beats, and consistency notes out of one story file.',
    model: { name: 'Haiku · Analysis', task: 'story_analysis', tone: 'fast' },
    duration: 7000,
    inputs: [
      { id: 'story', label: 'Story', kind: 'select', options: ['014 — Weathertop', '013 — Bree', '012 — Trollshaws'] },
      { id: 'depth', label: 'Depth', kind: 'segment', options: ['Shallow', 'Standard', 'Deep'], default: 'Standard' },
    ],
    outputKind: 'analysis',
    mock: MOCK_ANALYSIS,
    target: { kind: 'node--analysis_report', path: 'cache/analysis/014_weathertop.json' },
  },
  's-story-anal': {
    label: 'Series consistency analysis',
    group: 'Analysis',
    slow: true,
    blurb: 'Reads every story in the series and looks for naming drift, contradictions, unresolved foreshadowing, and theme drift.',
    model: { name: 'Sonnet · Deep Arc', task: 'series_analysis', tone: 'deep' },
    duration: 22000,
    inputs: [
      { id: 'series', label: 'Series', kind: 'select', options: ['Whispers of the Sundered Crown', 'The Ironroot Pact', 'Mistveil Quest'] },
      { id: 'scope',  label: 'Scope',  kind: 'segment', options: ['Last 5', 'Last 10', 'All'], default: 'All' },
    ],
    outputKind: 'analysis',
    mock: MOCK_ANALYSIS,
    target: { kind: 'node--series_report', path: 'cache/analysis/whispers-series.json' },
  },
  's-char-anal': {
    label: 'Character analysis',
    group: 'Analysis',
    slow: true,
    blurb: 'Builds an arc report across every appearance: how they have changed, what they want, where the player has driven them.',
    model: { name: 'Sonnet · Deep Arc', task: 'character_analysis', tone: 'deep' },
    duration: 24000,
    inputs: [
      { id: 'char',   label: 'Character', kind: 'select', options: ['Aragorn', 'Frodo', 'Gandalf', 'Legolas', 'Samwise', 'Merry', 'Pippin', 'Boromir'] },
      { id: 'scope',  label: 'Scope',     kind: 'segment', options: ['Recent arc', 'Full campaign'], default: 'Full campaign' },
    ],
    outputKind: 'analysis',
    mock: MOCK_ANALYSIS,
    target: { kind: 'node--character_report', path: 'cache/analysis/frodo-arc.json' },
  },
  's-amend': {
    label: 'Amend story actions',
    group: 'Authoring',
    blurb: 'Edit who did what in a session — change a name, correct a roll, swap a beat. AI can rewrite affected prose to match.',
    model: { name: 'Sonnet · Narrative', task: 'story_amend', tone: 'creative' },
    duration: 9000,
    inputs: [
      { id: 'story',  label: 'Story',  kind: 'select', options: ['014 — Weathertop', '013 — Bree'] },
      { id: 'find',   label: 'Find',   kind: 'textarea', rows: 3, placeholder: 'It was Sam who saw them first' },
      { id: 'change', label: 'Change to', kind: 'textarea', rows: 3, placeholder: 'It was Merry who saw them first' },
      { id: 'sweep',  label: 'AI rewrite sweep', kind: 'segment', options: ['None', 'Affected paragraph', 'Whole scene'], default: 'Affected paragraph' },
    ],
    outputKind: 'narrative',
    target: { kind: 'node--story', path: 'campaigns/whispers/014_weathertop.md' },
  },
};

/* Choose the mock prose for an action's outputKind. */
function mockForAction(actionId) {
  const p = ACTION_PRESETS[actionId];
  if (!p) return MOCK_NARRATIVE;
  if (p.mock) return p.mock;
  if (p.outputKind === 'analysis') return MOCK_ANALYSIS;
  if (p.outputKind === 'suggestions') return MOCK_SUGGESTIONS;
  return MOCK_NARRATIVE;
}

/* ────────────────────────────────────────────────────────────
   useAiRun — simulates a phased AI run.
     phases: 'setup' → 'running' → 'done'
     start() begins the stream. cancel() aborts mid-stream.
     reset() returns to setup (for "tweak prompt → re-run").
   ──────────────────────────────────────────────────────────── */
function useAiRun(actionId, opts = {}) {
  const preset = ACTION_PRESETS[actionId] || {};
  const totalDuration = opts.duration ?? preset.duration ?? 12000;
  const tickMs = 50;
  const fullText = mockForAction(actionId);

  const [phase, setPhase] = useState('setup');
  const [streamed, setStreamed] = useState('');
  const [progress, setProgress] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [tokens, setTokens] = useState(0);
  const [tokensPerSec, setTokensPerSec] = useState(0);
  const [events, setEvents] = useState([]);
  const timerRef = useRef(null);

  // Speed multiplier from Tweaks (1 = normal, 2 = 2x, 0.5 = slower).
  const speedRef = useRef(opts.speed ?? 1);
  useEffect(() => { speedRef.current = opts.speed ?? 1; }, [opts.speed]);

  const stopTimer = () => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  };

  useEffect(() => stopTimer, []);

  const start = () => {
    stopTimer();
    setPhase('running');
    setStreamed('');
    setProgress(0);
    setElapsed(0);
    setTokens(0);
    setTokensPerSec(0);
    setEvents([]);
    const t0 = Date.now();
    const presetEvents = (preset.eventsLog || []).slice();
    timerRef.current = setInterval(() => {
      const eMs = (Date.now() - t0) * speedRef.current;
      const eSec = eMs / 1000;
      setElapsed(eSec);
      const p = Math.min(1, eMs / totalDuration);
      setProgress(p);
      const target = Math.floor(p * fullText.length);
      const slice = fullText.slice(0, target);
      setStreamed(slice);
      // ~4.5 chars per token for English prose.
      const toks = Math.floor(target / 4.5);
      setTokens(toks);
      setTokensPerSec(eSec > 0.1 ? Math.floor(toks / eSec) : 0);
      // Flush event log on schedule.
      while (presetEvents.length) {
        const next = presetEvents[0];
        const [mm, ss] = next.t.split(':').map(Number);
        const whenSec = mm * 60 + ss;
        if (whenSec <= eSec) {
          presetEvents.shift();
          setEvents(ev => [...ev, next]);
        } else break;
      }
      if (p >= 1) {
        stopTimer();
        setPhase('done');
      }
    }, tickMs);
  };

  const cancel = () => {
    stopTimer();
    setPhase('setup');
    setStreamed('');
    setProgress(0);
    setElapsed(0);
    setTokens(0);
    setTokensPerSec(0);
  };

  const reset = () => {
    stopTimer();
    setPhase('setup');
    setStreamed('');
  };

  return { phase, setPhase, start, cancel, reset, streamed, progress, elapsed, tokens, tokensPerSec, events, preset, fullText };
}

window.useAiRun = useAiRun;
window.ACTION_PRESETS = ACTION_PRESETS;
window.mockForAction = mockForAction;
