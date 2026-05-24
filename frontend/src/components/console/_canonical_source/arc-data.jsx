/* DDCCS — Arc analysis mock data
   Inspired by the Fellowship campaign roster. Maps to the
   src/character_arc/arc_data.py schema:
   - CharacterArc: character_name, campaign_name, baseline, data_points,
                   relationships, goals, state(direction, stage, summary)
   - ArcDataPoint: story_file, session_id, timestamp, metric_values,
                   observations, key_events, ai_analysis
   - Standard metrics: relationship_strength, trust_level, combat_effectiveness,
                       moral_alignment, confidence, trauma_level, goal_progress,
                       reputation
*/
/* global window, React */

/* Helper — synthesize a metric series (data_point.metric_values) for a
   character given desired endpoints and arc shape. Returns array of values
   per session, used for sparklines + diff rows. */
const series = (n, start, end, shape = 'linear') => {
  const out = [];
  for (let i = 0; i < n; i++) {
    const t = i / Math.max(1, n - 1);
    let v;
    if (shape === 'linear')      v = start + (end - start) * t;
    else if (shape === 'ease')   v = start + (end - start) * (t * t * (3 - 2 * t));
    else if (shape === 'arc')    v = start + (end - start) * Math.sin(t * Math.PI / 2);
    else if (shape === 'spike')  v = start + (end - start) * (t < 0.7 ? t * 1.1 : t);
    else if (shape === 'wobble') v = start + (end - start) * t + (Math.sin(t * 7) * 0.6);
    else                          v = start + (end - start) * t;
    out.push(Math.round(v * 10) / 10);
  }
  return out;
};

const ARC_DATA = {
  aragorn: {
    character_name: 'Aragorn',
    campaign_name: 'The Fellowship of the Ring',
    direction: 'transformation',
    stage: 'climax',
    summary: 'A long-deferred king walks toward the throne he has refused for forty years. Each story tightens the choice — to claim the line of Isildur, or to die a Ranger unnamed. The blade is reforged. The crown remains in shadow.',
    storiesAnalyzed: 14,
    lastAnalyzed: '2026-05-09',
    baseline: { confidence: 6, reputation: 'respected', combat_effectiveness: 9 },
    metrics: {
      confidence:           { series: series(14, 5.5, 8.0, 'ease'),  dim: 'Personality',   label: 'Confidence',       direction: 'growth',         obs: 'Slow to accept his name, but steadier with each council.' },
      combat_effectiveness: { series: series(14, 8.5, 9.5, 'arc'),   dim: 'Abilities',     label: 'Combat',           direction: 'growth',         obs: 'Andúril reforged at Rivendell; effectiveness against orcs +12%.' },
      reputation:           { series: series(14, 4.0, 8.5, 'spike'), dim: 'Reputation',    label: 'Reputation',       direction: 'transformation', obs: 'From "Strider" in Bree to "Estel" in Rivendell to "Elessar" abroad.', categorical: true, value: 'renowned' },
      trauma_level:         { series: series(14, 3.0, 4.5, 'wobble'),dim: 'Trauma',        label: 'Burden',           direction: 'fluctuation',    obs: 'Carries the failure of Isildur and the doubt of his line.' },
      relationship_strength:{ series: series(14, 6.5, 8.5, 'ease'),  dim: 'Relationships', label: 'Bonds',            direction: 'growth',         obs: 'Sworn to defend Frodo; Arwen waits in Rivendell.' },
      goal_progress:        { series: series(14,15,    62,   'ease'),dim: 'Goals',         label: 'Primary goal',     direction: 'growth',         obs: '62% toward reforging the kingdom. Mount Doom remains.' },
    },
    relationships: [
      { target: 'Frodo Baggins',   type: 'protégé',  strength: 8, trust: 9, note: 'Sworn to defend the Ring-bearer to the end.' },
      { target: 'Gandalf the Grey',type: 'mentor',   strength: 9, trust: 9, note: 'Counsel since his fostering at Rivendell.' },
      { target: 'Arwen Undómiel',  type: 'beloved',  strength:10, trust: 9, note: 'A bond of binding — and the price of mortality.' },
      { target: 'Boromir',         type: 'rival',    strength: 5, trust: 5, note: 'Two heirs of two kingdoms; one will fall.' },
    ],
    goals: [
      { description: 'Reforge the line of Elendil',     status: 'active', progress: 62 },
      { description: 'See the Ring-bearer to Mount Doom', status: 'active', progress: 48 },
      { description: 'Take Arwen as queen',              status: 'dormant',progress: 10 },
    ],
    timeline: [
      { story_id: 's012', title: 'The Bell of Vellishar', session: 12, timestamp: '2026-04-22', obs: 'Refused the crown at council. Spoke as Strider, not Elessar.',
        events: ['Refused Elrond\'s ring at the war council', 'Reforged Andúril in the foundries below Rivendell'] },
      { story_id: 's013', title: 'Smoke at the Northgate', session: 13, timestamp: '2026-04-29', obs: 'First to commit the Fellowship at the burnt waystation; spoke for the hobbits when others would not.',
        events: ['Defeated three Uruks single-handed', 'Found the Lórien token'] },
      { story_id: 's014', title: 'A Ledger of Names', session: 14, timestamp: '2026-05-09', obs: 'Read his lineage aloud for the first time. A turning.',
        events: ['Accepted "Elessar" in the presence of Galadriel', 'Returned the broken horn to Boromir'], current: true },
    ],
  },

  frodo: {
    character_name: 'Frodo Baggins',
    campaign_name: 'The Fellowship of the Ring',
    direction: 'decline',
    stage: 'challenge',
    summary: 'The Ring grows heavier each league. Where Bilbo carried it as a curiosity, Frodo carries it as a wound. Trust narrows. Sam alone has not flickered. The road south will not be kinder.',
    storiesAnalyzed: 14,
    lastAnalyzed: '2026-05-09',
    baseline: { confidence: 6, trauma_level: 1, reputation: 'unknown' },
    metrics: {
      confidence:           { series: series(14, 6.5, 3.8, 'ease'),  dim: 'Personality',   label: 'Confidence',     direction: 'decline',       obs: 'Each use of the Ring leaves him quieter, less sure.' },
      trauma_level:         { series: series(14, 1.0, 7.2, 'spike'), dim: 'Trauma',        label: 'Ring burden',    direction: 'decline',       obs: 'Morgul-wound flares before storms; visions of an eye that does not blink.' },
      trust_level:          { series: series(14, 7.0, 4.5, 'wobble'),dim: 'Relationships', label: 'Trust in others',direction: 'fluctuation',   obs: 'Trusts Sam without question; everyone else by hesitation.' },
      relationship_strength:{ series: series(14, 5.5, 6.8, 'arc'),   dim: 'Relationships', label: 'Sam-bond',       direction: 'growth',        obs: 'Sam\'s steadiness is the only metric that climbs.' },
      moral_alignment:      { series: series(14, 8.0, 6.5, 'wobble'),dim: 'Beliefs',       label: 'Moral compass',  direction: 'fluctuation',   obs: 'Wavers when the Ring whispers. Has not yet broken.', categorical: true, value: 'neutral_good' },
      goal_progress:        { series: series(14, 5,   28,   'ease'), dim: 'Goals',         label: 'Mount Doom',     direction: 'growth',        obs: '28% of the way south. The Misty Mountains still ahead.' },
    },
    relationships: [
      { target: 'Samwise Gamgee',  type: 'loyal',     strength:10, trust:10, note: 'Closer than family. Has not flickered.' },
      { target: 'Gandalf the Grey',type: 'mentor',    strength: 8, trust: 7, note: 'Lost at Khazad-dûm — bond strained by absence.' },
      { target: 'Aragorn',         type: 'guardian',  strength: 7, trust: 8, note: 'Trusts the sword, less sure of the man\'s claim.' },
      { target: 'The Ring',        type: 'possession',strength: 9, trust: 1, note: 'Not an ally. A weight that whispers.' },
    ],
    goals: [
      { description: 'Bear the Ring to Mount Doom',  status: 'active',  progress: 28 },
      { description: 'Return to Bag End',            status: 'dormant', progress: 0 },
      { description: 'Resist the Ring\'s call',      status: 'active',  progress: 60 },
    ],
    timeline: [
      { story_id: 's012', title: 'The Bell of Vellishar', session: 12, timestamp: '2026-04-22', obs: 'Refused to wear the Ring at the cairn. A small victory; the wound still bled.',
        events: ['Resisted putting on the Ring during ambush', 'Morgul-wound flared'] },
      { story_id: 's013', title: 'Smoke at the Northgate', session: 13, timestamp: '2026-04-29', obs: 'Slept with the chain in his fist. Sam pried his fingers open before dawn.',
        events: ['Dream of the Eye', 'Refused food for a day and a half'] },
      { story_id: 's014', title: 'A Ledger of Names', session: 14, timestamp: '2026-05-09', obs: 'Spoke of "giving it to anyone, anyone" before catching himself. The first slip.',
        events: ['First spoken temptation to surrender the Ring', 'Galadriel\'s test passed by Frodo, not by the Ring'], current: true },
    ],
  },

  gandalf: {
    character_name: 'Gandalf the Grey',
    campaign_name: 'The Fellowship of the Ring',
    direction: 'transformation',
    stage: 'resolution',
    summary: 'Fell with the Balrog. Returned not as Grey but as something else — a wizard with a name unspoken, weighing every counsel against the fall in Khazad-dûm.',
    storiesAnalyzed: 12,
    lastAnalyzed: '2026-05-09',
    baseline: { combat_effectiveness: 9, confidence: 9, reputation: 'renowned' },
    metrics: {
      confidence:           { series: series(12, 8.5, 9.5, 'arc'),    dim: 'Personality',   label: 'Confidence',       direction: 'growth',         obs: 'Returned changed; speaks less and acts more deliberately.' },
      combat_effectiveness: { series: series(12, 9.0,10.0, 'ease'),   dim: 'Abilities',     label: 'Power',            direction: 'transformation', obs: 'Returned with abilities not previously catalogued.' },
      reputation:           { series: series(12, 8.0, 9.5, 'ease'),   dim: 'Reputation',    label: 'Renown',           direction: 'growth',         obs: 'Word of the White Rider precedes him into Rohan.', categorical: true, value: 'legendary' },
      trauma_level:         { series: series(12, 2.0, 5.5, 'spike'),  dim: 'Trauma',        label: 'Khazad-dûm',       direction: 'fluctuation',    obs: 'Speaks rarely of the fall. Sleep is no longer required.' },
      goal_progress:        { series: series(12,40,   72,   'ease'),  dim: 'Goals',         label: 'Counsel of the Wise', direction: 'growth',      obs: 'Rallying Rohan and Gondor before the Pelennor.' },
    },
    relationships: [
      { target: 'Aragorn',          type: 'protégé',   strength: 9, trust:10, note: 'Trained the heir since youth. Has handed off the chain.' },
      { target: 'Frodo Baggins',    type: 'guardian',  strength: 9, trust: 9, note: 'Will not abandon the Ring-bearer again.' },
      { target: 'Saruman the White',type: 'broken',    strength: 2, trust: 0, note: 'Once peer; now an enemy unmasked.' },
    ],
    goals: [
      { description: 'Rally the Free Peoples',     status: 'active', progress: 72 },
      { description: 'Defeat Saruman',             status: 'active', progress: 55 },
      { description: 'Return Galadriel\'s phial',  status: 'done',   progress:100 },
    ],
    timeline: [
      { story_id: 's013', title: 'Smoke at the Northgate', session: 13, timestamp: '2026-04-29', obs: 'Returned the staff broken. Returned the wizard whole.', events: ['Reunited with the Three Hunters', 'Broke Saruman\'s staff at distance'] },
      { story_id: 's014', title: 'A Ledger of Names', session: 14, timestamp: '2026-05-09', obs: 'Named Aragorn in Galadriel\'s presence — an old promise kept.', events: ['Formal naming of the heir', 'Counsel with Galadriel'], current: true },
    ],
  },

  legolas: {
    character_name: 'Legolas Greenleaf',
    campaign_name: 'The Fellowship of the Ring',
    direction: 'growth',
    stage: 'development',
    summary: 'Began with the easy certainty of an immortal among mortals. Each story has taught him a different humility. Begins to look at Gimli with something other than tolerance.',
    storiesAnalyzed: 13,
    lastAnalyzed: '2026-05-09',
    metrics: {
      confidence:           { series: series(13, 8.0, 8.5, 'linear'), dim: 'Personality',   label: 'Confidence',     direction: 'stasis',      obs: 'Already self-assured; little movement.' },
      combat_effectiveness: { series: series(13, 8.5, 9.2, 'ease'),   dim: 'Abilities',     label: 'Combat',         direction: 'growth',      obs: 'Counts kills with Gimli; competition has sharpened him.' },
      relationship_strength:{ series: series(13, 4.0, 7.5, 'arc'),    dim: 'Relationships', label: 'Bond with Gimli',direction: 'transformation', obs: 'Began as suspicion. Has become something rare between their peoples.' },
      moral_alignment:      { series: series(13, 9.0, 8.5, 'wobble'), dim: 'Beliefs',       label: 'Detachment',     direction: 'fluctuation', obs: 'The mortality of his companions has begun to mark him.', categorical: true, value: 'chaotic_good' },
    },
    relationships: [
      { target: 'Gimli',       type: 'fellow',   strength: 7, trust: 8, note: 'Friendship across the oldest grudge in the West.' },
      { target: 'Aragorn',     type: 'liege',    strength: 8, trust: 9, note: 'Sworn to the Fellowship and its captain.' },
    ],
    goals: [
      { description: 'See the Ring destroyed', status: 'active', progress: 32 },
      { description: 'Visit Fangorn with Gimli', status: 'active', progress: 10 },
    ],
    timeline: [
      { story_id: 's013', title: 'Smoke at the Northgate', session: 13, timestamp: '2026-04-29', obs: 'Tied with Gimli at 42 each. A grin not seen before.', events: ['Counted shots aloud for the first time'] },
      { story_id: 's014', title: 'A Ledger of Names', session: 14, timestamp: '2026-05-09', obs: 'Stood for Gimli when his name was challenged at Lórien.', events: ['Vouched for Gimli before Galadriel'], current: true },
    ],
  },

  samwise: {
    character_name: 'Samwise Gamgee',
    campaign_name: 'The Fellowship of the Ring',
    direction: 'growth',
    stage: 'development',
    summary: 'A gardener who has become something larger every story without noticing. The metric that climbs fastest is courage, and he would deny it climbs at all.',
    storiesAnalyzed: 14,
    lastAnalyzed: '2026-05-09',
    metrics: {
      confidence:           { series: series(14, 3.5, 6.8, 'ease'),  dim: 'Personality',   label: 'Confidence',     direction: 'growth',  obs: 'Speaks up now where he would not have a month ago.' },
      combat_effectiveness: { series: series(14, 2.0, 5.5, 'spike'), dim: 'Abilities',     label: 'Combat',         direction: 'growth',  obs: 'Drove a torch into a cave-troll. Still calls himself a gardener.' },
      relationship_strength:{ series: series(14, 8.0, 9.8, 'ease'),  dim: 'Relationships', label: 'Frodo-bond',     direction: 'growth',  obs: 'The only relationship in the Fellowship without doubt.' },
      goal_progress:        { series: series(14, 5,   28,   'ease'), dim: 'Goals',         label: 'See Mr. Frodo home', direction: 'growth', obs: 'Defines the goal in his own words. Hasn\'t changed it once.' },
    },
    relationships: [
      { target: 'Frodo Baggins', type: 'ward',  strength:10, trust:10, note: 'Without question. Without limit.' },
      { target: 'Rosie Cotton',  type: 'beloved', strength: 8, trust: 9, note: 'Waits in Hobbiton. Speaks of her at watch.' },
    ],
    goals: [
      { description: 'Get Mr. Frodo home',      status: 'active', progress: 28 },
      { description: 'Return to Rosie',         status: 'active', progress: 12 },
    ],
    timeline: [
      { story_id: 's013', title: 'Smoke at the Northgate', session: 13, timestamp: '2026-04-29', obs: 'First time spoke against Aragorn\'s counsel. He was right.', events: ['Insisted on watching Frodo through the night'] },
      { story_id: 's014', title: 'A Ledger of Names', session: 14, timestamp: '2026-05-09', obs: 'Stood at Frodo\'s shoulder before Galadriel and did not look away.', events: ['Refused to leave Frodo\'s side at the Mirror'], current: true },
    ],
  },

  merry: {
    character_name: 'Meriadoc Brandybuck',
    campaign_name: 'The Fellowship of the Ring',
    direction: 'growth',
    stage: 'establishment',
    summary: 'The conspirator. Plans like a Brandybuck. The road has not yet broken his good humor — it has only sharpened it.',
    storiesAnalyzed: 11,
    lastAnalyzed: '2026-05-02',
    metrics: {
      confidence:           { series: series(11, 5.0, 6.5, 'linear'), dim: 'Personality',   label: 'Confidence',     direction: 'growth',  obs: 'Steadier than expected. Notices terrain like a scout.' },
      combat_effectiveness: { series: series(11, 2.5, 4.0, 'ease'),   dim: 'Abilities',     label: 'Combat',         direction: 'growth',  obs: 'Bow now. Tendency to overreach in melee.' },
      relationship_strength:{ series: series(11, 7.0, 8.0, 'linear'), dim: 'Relationships', label: 'Hobbit-bond',    direction: 'growth',  obs: 'With Pippin: inseparable. With the rest: warming.' },
    },
    relationships: [
      { target: 'Pippin', type: 'cousin', strength:10, trust:10, note: 'Two halves of the same scheme.' },
    ],
    goals: [{ description: 'Live to tell the tale', status: 'active', progress: 32 }],
    timeline: [
      { story_id: 's012', title: 'The Bell of Vellishar', session: 12, timestamp: '2026-04-22', obs: 'Mapped the cairn perimeter without being asked.', events: ['First independent scouting'], current: true },
    ],
  },

  pippin: {
    character_name: 'Peregrin Took',
    campaign_name: 'The Fellowship of the Ring',
    direction: 'fluctuation',
    stage: 'establishment',
    summary: 'Curiosity is his strength and his flaw. The well in Khazad-dûm was a lesson he has not finished learning.',
    storiesAnalyzed: 11,
    lastAnalyzed: '2026-05-02',
    metrics: {
      confidence:           { series: series(11, 6.0, 5.2, 'wobble'),dim: 'Personality',   label: 'Confidence',     direction: 'fluctuation', obs: 'Bravado, then shame, then bravado.' },
      combat_effectiveness: { series: series(11, 2.0, 3.5, 'linear'),dim: 'Abilities',     label: 'Combat',         direction: 'growth',     obs: 'Game but small. Hides well, swings unwisely.' },
      trauma_level:         { series: series(11, 1.0, 4.0, 'spike'), dim: 'Trauma',        label: 'Guilt',          direction: 'decline',    obs: 'Bears the well-stone in his pocket; it knocks at night.' },
    },
    relationships: [
      { target: 'Merry', type: 'cousin', strength:10, trust:10, note: 'Cannot be measured separately.' },
    ],
    goals: [{ description: 'Make up for the well', status: 'active', progress: 20 }],
    timeline: [
      { story_id: 's012', title: 'The Bell of Vellishar', session: 12, timestamp: '2026-04-22', obs: 'Apologized to Gandalf privately. The apology landed.', events: ['Took watch alone for the first time'], current: true },
    ],
  },

  boromir: {
    character_name: 'Boromir of Gondor',
    campaign_name: 'The Fellowship of the Ring',
    direction: 'decline',
    stage: 'climax',
    summary: 'A captain of a great city, walking among smaller folk with a weight on his shoulders that is not his alone. The Ring listens to the heaviest first.',
    storiesAnalyzed: 12,
    lastAnalyzed: '2026-05-09',
    metrics: {
      confidence:           { series: series(12, 8.0, 7.0, 'wobble'),dim: 'Personality',   label: 'Confidence',     direction: 'decline',    obs: 'Speaks of Gondor more, and to fewer.' },
      combat_effectiveness: { series: series(12, 8.5, 9.2, 'ease'),  dim: 'Abilities',     label: 'Combat',         direction: 'growth',     obs: 'Sharper in steel; less so in counsel.' },
      moral_alignment:      { series: series(12, 7.5, 5.5, 'ease'),  dim: 'Beliefs',       label: 'Moral compass',  direction: 'decline',    obs: 'The Ring whispers in his father\'s voice.', categorical: true, value: 'lawful_neutral' },
      trauma_level:         { series: series(12, 3.5, 6.0, 'spike'), dim: 'Trauma',        label: 'Strain',         direction: 'decline',    obs: 'Watches the Ring when he should watch the road.' },
      relationship_strength:{ series: series(12, 6.0, 5.0, 'wobble'),dim: 'Relationships', label: 'Bonds',          direction: 'fluctuation',obs: 'Warm with the hobbits, cold with the Ring-bearer.' },
    },
    relationships: [
      { target: 'Aragorn', type: 'rival',    strength: 5, trust: 6, note: 'Two heirs walking the same road; one must yield.' },
      { target: 'Frodo',   type: 'distance', strength: 4, trust: 4, note: 'Cannot look at him without looking at the Ring.' },
      { target: 'Merry',   type: 'guardian', strength: 7, trust: 8, note: 'Teaches sword-play. Patient with the hobbit.' },
    ],
    goals: [
      { description: 'Save Gondor',       status: 'active', progress: 35 },
      { description: 'Wield the Ring',    status: 'active', progress: 18, flagged: true },
    ],
    timeline: [
      { story_id: 's013', title: 'Smoke at the Northgate', session: 13, timestamp: '2026-04-29', obs: 'Lingered when Frodo handled the Ring; corrected himself.', events: ['First flagged temptation event'] },
      { story_id: 's014', title: 'A Ledger of Names', session: 14, timestamp: '2026-05-09', obs: 'Did not speak at Galadriel\'s Mirror. Avoided her gaze on the way out.', events: ['Avoided the Mirror', 'Watched Frodo through the night'], current: true },
    ],
  },
};

const ARC_CHARS_ORDER = ['aragorn','frodo','gandalf','legolas','samwise','boromir','merry','pippin'];

/* Sub-set used by the Analyze artboard — Boromir mid-stream */
const ANALYZE_DEMO = {
  character: 'boromir',
  story_file: 's015_under_the_eaves_of_lorien.md',
  session_id: 'session-15',
  timestamp: '2026-05-15',
  proposed: {
    direction: 'decline',
    stage: 'climax',
    summary_partial: 'Boromir spoke of Minas Tirith with a desperation he has not shown before. When the Ring was unwrapped on the council table — for no good reason — his hand moved before his thought.',
    metric_deltas: [
      { metric: 'confidence',            dim: 'Personality',   prev: 7.0, next: 6.4, isNew: false },
      { metric: 'moral_alignment',       dim: 'Beliefs',       prev: 'lawful_neutral', next: 'true_neutral', isNew: false, categorical: true },
      { metric: 'trauma_level',          dim: 'Trauma',        prev: 6.0, next: 7.1, isNew: false },
      { metric: 'temptation_pressure',   dim: 'Trauma',        prev: null, next: 6.8, isNew: true },
      { metric: 'relationship_strength', dim: 'Relationships', prev: 5.0, next: 4.3, isNew: false },
    ],
    observations: [
      'Speaks of Gondor in the present where he previously spoke in the past',
      'Reached for the Ring without being addressed — the first overt action',
      'Avoided Frodo\'s gaze for the entire scene at Galadriel\'s Mirror',
      'Apologized to Pippin privately; the apology was about himself',
    ],
    key_events: [
      'Reached for the Ring during the unwrapping at the council table',
      'Did not look into Galadriel\'s Mirror',
      'Was given Galadriel\'s belt of gold — wore it inside the cloak',
    ],
    flags: [
      'Reached-for-Ring is the first flagged event for this character',
    ],
  },
};

Object.assign(window, { ARC_DATA, ARC_CHARS_ORDER, ANALYZE_DEMO, arcSeries: series });
