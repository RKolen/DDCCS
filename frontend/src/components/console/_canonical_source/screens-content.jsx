/* Deep screens — content domain (characters, stories, read, npcs)
   All read `MENU_DATA` and shared atoms (Icon, AiTag, SlowTag…) from window.
*/

const { useState, useMemo, useEffect, useRef } = React;

/* ============================================================
   Read Story File — the player reader
   ============================================================ */
const ReadStoryFileScreen = ({ ctx, setCtx }) => {
  const stories = MENU_DATA.recentStories;
  const activeIdx = ctx.storyIdx ?? 0;
  const story = stories[activeIdx];

  return (
    <div className="screen-readstory">
      <aside className="reader-picker">
        <div className="reader-picker-head">
          <span className="reader-eyebrow">Stories</span>
          <h3>{ctx.campaign || 'Whispers of the Sundered Crown'}</h3>
        </div>
        <ol className="reader-picker-list">
          {stories.map((s, i) => (
            <li key={s.title}>
              <button
                className={`reader-picker-item${i === activeIdx ? ' active' : ''}`}
                onClick={() => setCtx({ ...ctx, storyIdx: i })}>
                <span className="picker-num">{String(i + 1).padStart(3, '0')}</span>
                <span className="picker-meta">
                  <strong>{s.title}</strong>
                  <span>{s.date}</span>
                </span>
              </button>
            </li>
          ))}
        </ol>
      </aside>

      <article className="reader-page">
        <header className="reader-head">
          <span className="reader-chip">Story {String(activeIdx + 1).padStart(3, '0')}</span>
          <h1>{story.title}</h1>
          <div className="reader-meta-row">
            <span><Icon name="book" size={11}/> {story.series}</span>
            <span className="dot-sep">·</span>
            <span>{story.date}</span>
            <span className="dot-sep">·</span>
            <span>~12 min read</span>
          </div>
        </header>

        <div className="reader-body">
          <p className="reader-dropcap">
            <span className="dropcap">T</span>he afternoon sun cast long shadows across the winding path leading deeper into Trollshaws Forest. Ancient trees, gnarled and twisted by centuries of growth, loomed overhead like silent sentinels guarding forgotten secrets. The party walked in cautious formation, their footsteps muffled by the carpet of fallen leaves.
          </p>
          <p>
            <strong>Aragorn</strong> raised a closed fist, signalling a halt. Something was wrong — the forest had gone quiet. Not the natural quiet of dusk, but the held-breath silence that precedes ambush. <strong>Frodo</strong> reached for the small dagger at his belt, his eyes wide. <strong>Gandalf</strong> tilted his head, listening to something the rest could not hear.
          </p>
          <h3>The Hollow Cairn</h3>
          <p>
            Past a curtain of low-hanging willow, they found it: a moss-eaten cairn of black stones, knee-high, arranged in a near-perfect circle. Old runes had been carved into the topmost stones, weathered but legible to those with the schooling for it. The runes did not warn of treasure. They warned of <em>what lay beneath</em>.
          </p>
          <p>
            <strong>Pippin</strong>, never one to leave a thing alone, stepped forward. <strong>Sam</strong> grabbed his elbow. The forest air thickened, and somewhere distant — or perhaps very close — a single bell rang once and went silent.
          </p>
          <h3>A Bargain in the Underdark</h3>
          <p>
            They did not open the cairn that day. But the bell would ring again, three nights hence, when the party reached the village of Hollowmere. By then it would be too late to pretend they had not heard it the first time.
          </p>
        </div>

        <footer className="reader-foot">
          <div className="reader-foot-ornament">❦ · ❦ · ❦</div>
          <div className="reader-actions">
            <NarrateMedallion />
            <ImageGenMedallion />
            <button className="reader-action-btn">
              <Icon name="chevron" size={12}/> Next: {stories[(activeIdx + 1) % stories.length].title}
            </button>
          </div>
        </footer>
      </article>
    </div>
  );
};

const NarrateMedallion = () => {
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    if (!playing) return;
    const t = setInterval(() => setProgress(p => (p >= 1 ? 0 : p + 0.01)), 100);
    return () => clearInterval(t);
  }, [playing]);
  return (
    <button className={`big-medallion${playing ? ' is-active' : ''}`} onClick={() => setPlaying(p => !p)}>
      <Icon name={playing ? 'pause' : 'speaker'} size={18}/>
      <span className="medallion-label">{playing ? 'Narrating…' : 'Narrate'}</span>
      {playing && (
        <span className="medallion-progress">
          <span className="medallion-progress-fill" style={{ width: `${progress * 100}%` }}/>
        </span>
      )}
    </button>
  );
};

const ImageGenMedallion = () => {
  const [state, setState] = useState('idle'); /* idle | running | done */
  const run = () => {
    if (state === 'running') return;
    setState('running');
    setTimeout(() => setState('done'), 2200);
  };
  return (
    <button className={`big-medallion big-medallion--ai state-${state}`} onClick={run} disabled={state === 'running'}>
      <Icon name={state === 'running' ? 'sparkle' : 'image'} size={18}/>
      <span className="medallion-label">
        {state === 'idle' && 'Generate image'}
        {state === 'running' && 'Conjuring…'}
        {state === 'done' && 'View image'}
      </span>
      <AiTag label=""/>
    </button>
  );
};

/* ============================================================
   View Character Details — profile sheet
   ============================================================ */
const ViewCharacterDetailsScreen = ({ ctx, setCtx }) => {
  const chars = MENU_DATA.characters;
  const activeIdx = ctx.charIdx ?? 0;
  const char = chars[activeIdx];

  return (
    <div className="screen-chardetails">
      <aside className="char-picker">
        <div className="reader-picker-head">
          <span className="reader-eyebrow">Party</span>
          <h3>4 members</h3>
        </div>
        <ol className="char-picker-list">
          {chars.map((c, i) => (
            <li key={c.name}>
              <button
                className={`char-picker-item${i === activeIdx ? ' active' : ''}`}
                onClick={() => setCtx({ ...ctx, charIdx: i })}>
                <span className="char-pip">{c.name[0]}</span>
                <span className="char-pip-meta">
                  <strong>{c.name}</strong>
                  <span>{c.class} · L{c.level}</span>
                </span>
              </button>
            </li>
          ))}
        </ol>
      </aside>

      <section className="char-sheet">
        <header className="char-sheet-head">
          <div className="char-sheet-portrait">
            <span className="portrait-placeholder">portrait</span>
            <span className="portrait-tag"><AiTag label="ComfyUI"/></span>
          </div>
          <div className="char-sheet-title">
            <span className="reader-eyebrow">Character</span>
            <h1>{char.name}</h1>
            <div className="char-sheet-sub">
              <span>{char.class}</span>
              <span className="dot-sep">·</span>
              <span>Level {char.level}</span>
              {char.pronouns && <><span className="dot-sep">·</span><span>{char.pronouns}</span></>}
            </div>
          </div>
          <div className="char-sheet-actions">
            <button className="ghost-btn"><Icon name="sparkle" size={12}/> Consult</button>
            <button className="ghost-btn">Edit</button>
          </div>
        </header>

        <div className="char-sheet-body">
          <div className="char-stat-row">
            {[
              ['HP', '64 / 64', 'success'],
              ['AC', '17'],
              ['SPD', '30 ft'],
              ['INIT', '+3'],
              ['PROF', '+3'],
              ['SAVE DC', '15'],
            ].map(([label, val, tone]) => (
              <div key={label} className={`stat-cell${tone ? ' tone-' + tone : ''}`}>
                <span className="stat-label">{label}</span>
                <span className="stat-val">{val}</span>
              </div>
            ))}
          </div>

          <div className="char-section-grid">
            <section className="char-section">
              <h4>Ability Scores</h4>
              <div className="ability-grid">
                {[['STR', 10, 0], ['DEX', 16, 3], ['CON', 14, 2], ['INT', 12, 1], ['WIS', 18, 4], ['CHA', 13, 1]].map(([k, v, m]) => (
                  <div key={k} className="ability-cell">
                    <span className="ability-name">{k}</span>
                    <span className="ability-val">{v}</span>
                    <span className="ability-mod">{m >= 0 ? '+' : ''}{m}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="char-section">
              <h4>Personality</h4>
              <p>Cautious by nature, devout by training. Speaks rarely; when she does it carries weight. Carries an old field journal she will not let anyone read.</p>
              <h5>Bonds</h5>
              <ul className="bullet-list">
                <li>Owes Brynn a life-debt from the Battle of Eastreach.</li>
                <li>Searches for her sister, last seen in the Sundered Crown.</li>
              </ul>
            </section>

            <section className="char-section">
              <h4>Arc Progress <AiTag label="AI"/></h4>
              <div className="arc-progress">
                <div className="arc-pip filled"></div>
                <div className="arc-pip filled"></div>
                <div className="arc-pip filled"></div>
                <div className="arc-pip current"></div>
                <div className="arc-pip"></div>
              </div>
              <p className="arc-blurb">Approaching the <strong>Threshold</strong>: the choice between continuing the search and answering the call of the Pact.</p>
              <button className="ghost-btn ghost-small"><Icon name="sparkle" size={11}/> Analyze recent story</button>
            </section>

            <section className="char-section">
              <h4>Recent Story Appearances</h4>
              <ul className="story-mini-list">
                <li><span>The Bell of Vellishar</span><span>3 days ago</span></li>
                <li><span>Smoke at the Northgate</span><span>1 week ago</span></li>
                <li><span>A Ledger of Names</span><span>2 weeks ago</span></li>
              </ul>
            </section>
          </div>
        </div>
      </section>
    </div>
  );
};

/* ============================================================
   Story Series Workspace — when "Work with Story Series" active
   ============================================================ */
const StorySeriesWorkspaceScreen = ({ ctx, setCtx }) => {
  const stories = ['001_prancing_pony.md', '002_trollshaws.md', '003_weathertop.md', '004_bell_of_vellishar.md', '005_northgate.md'];

  const groups = [
    { title: 'Create', items: [
      { id: 's-add', label: 'Add new story', ai: true },
    ]},
    { title: 'Generate', items: [
      { id: 's-session', label: 'Session results', ai: true },
      { id: 's-chardev', label: 'Character development', ai: true },
      { id: 's-combat', label: 'Combat → narrative', ai: true },
    ]},
    { title: 'Consult', items: [
      { id: 's-dc', label: 'DC suggestions', ai: true },
      { id: 's-dm', label: 'DM narrative suggestions', ai: true },
      { id: 's-suggest', label: 'AI story suggestions', ai: true },
    ]},
    { title: 'Analyze', items: [
      { id: 's-analyze', label: 'Analyze single story', ai: true },
      { id: 's-story-anal', label: 'Series consistency', ai: true, slow: true },
      { id: 's-char-anal', label: 'Character analysis', ai: true, slow: true },
    ]},
    { title: 'Curate', items: [
      { id: 's-view', label: 'View story details' },
      { id: 's-amend', label: 'Amend story actions' },
      { id: 's-notes', label: 'Session notes' },
    ]},
  ];

  return (
    <div className="screen-series">
      <header className="series-head">
        <div>
          <span className="reader-eyebrow">Series</span>
          <h2>Whispers of the Sundered Crown</h2>
          <div className="series-stats">
            <span><Icon name="scroll" size={12}/> {stories.length} stories</span>
            <span className="dot-sep">·</span>
            <span><Icon name="char" size={12}/> 4 party members</span>
            <span className="dot-sep">·</span>
            <span>Started 8 weeks ago</span>
          </div>
        </div>
        <div className="series-head-actions">
          <button className="ghost-btn">Switch series</button>
          <button className="primary-btn"><Icon name="plus" size={11}/><Icon name="sparkle" size={11}/> New story</button>
        </div>
      </header>

      <div className="series-grid">
        <aside className="series-stories">
          <div className="series-stories-head">
            <h4>Stories in series</h4>
            <span className="series-stories-count">{stories.length}</span>
          </div>
          <ol className="series-story-list">
            {stories.map((s, i) => (
              <li key={s}>
                <button className={`series-story${i === stories.length - 1 ? ' is-latest' : ''}`}>
                  <span className="story-numeral">{s.slice(0, 3)}</span>
                  <span className="story-filename">{s.slice(4).replace('.md', '').replace(/_/g, ' ')}</span>
                  {i === stories.length - 1 && <span className="latest-tag">latest</span>}
                </button>
              </li>
            ))}
          </ol>
        </aside>

        <section className="series-actions">
          {groups.map(g => (
            <div key={g.title} className="action-group">
              <h5 className="action-group-title">{g.title}</h5>
              <div className="action-group-cards">
                {g.items.map(it => (
                  <button key={it.id} className="series-action-card">
                    <span className="series-action-label">
                      {it.label}
                      {it.ai && <AiTag />}
                      {it.slow && <SlowTag />}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
};

/* ============================================================
   Timeline Tracking
   ============================================================ */
const TimelineScreen = () => {
  const events = [
    { date: 'Hammer 12, 1492 DR', label: 'Party formed at the Prancing Pony', tag: 'session 1' },
    { date: 'Hammer 14, 1492 DR', label: 'First encounter — Trollshaws ambush', tag: 'combat' },
    { date: 'Hammer 16, 1492 DR', label: 'Discovered the Hollow Cairn', tag: 'lore' },
    { date: 'Hammer 19, 1492 DR', label: 'Bell rang in Vellishar — first prophecy', tag: 'plot' },
    { date: 'Alturiak 2, 1492 DR', label: 'Smoke at the Northgate', tag: 'combat' },
    { date: 'Alturiak 7, 1492 DR', label: 'Vesper found the Ledger', tag: 'character' },
  ];

  return (
    <div className="screen-timeline">
      <header className="timeline-head">
        <div>
          <span className="reader-eyebrow">Campaign timeline</span>
          <h2>Whispers of the Sundered Crown</h2>
        </div>
        <div className="timeline-actions">
          <button className="ghost-btn">Filter</button>
          <button className="ghost-btn"><Icon name="plus" size={11}/> Add event</button>
        </div>
      </header>
      <ol className="timeline-list">
        {events.map((e, i) => (
          <li key={i} className="timeline-row">
            <span className="timeline-rail"/>
            <span className={`timeline-dot tag-${e.tag.split(' ')[0]}`}/>
            <div className="timeline-content">
              <span className="timeline-date">{e.date}</span>
              <span className="timeline-label">{e.label}</span>
              <span className={`timeline-tag tag-${e.tag.split(' ')[0]}`}>{e.tag}</span>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
};

/* ============================================================
   List Characters — polished grid
   ============================================================ */
const ListCharactersScreen = ({ ctx, setCtx }) => (
  <div className="screen-charlist">
    <header className="screen-head">
      <div>
        <span className="reader-eyebrow">Characters</span>
        <h2>Party of 4</h2>
      </div>
      <div className="screen-head-actions">
        <button className="ghost-btn"><Icon name="search" size={12}/> Find</button>
        <button className="primary-btn"><Icon name="plus" size={11}/> New character</button>
      </div>
    </header>
    <div className="char-grid">
      {MENU_DATA.characters.map((c, i) => (
        <article key={c.name} className="char-card" onClick={() => setCtx({ ...ctx, _jumpTo: { itemId: 'view', charIdx: i } })}>
          <div className="char-portrait">
            <span className="portrait-placeholder">portrait</span>
            <span className="portrait-tag"><AiTag label="ComfyUI"/></span>
          </div>
          <div className="char-card-body">
            <h4>{c.name}</h4>
            <span className="char-card-meta">{c.class} · Level {c.level}</span>
            {c.pronouns && <span className="char-card-pron">{c.pronouns}</span>}
          </div>
          <div className="char-card-stats">
            <span>HP 64</span>
            <span>AC 17</span>
            <span>+3 prof</span>
          </div>
        </article>
      ))}
    </div>
  </div>
);

/* ============================================================
   List Major NPCs — table
   ============================================================ */
const ListNPCsScreen = () => {
  const npcs = [
    { name: 'Lhamtharra, the Sundered', role: 'BBEG · Lich Queen', faction: 'Cult of the Crown', cr: '18' },
    { name: 'Captain Selmir Vance', role: 'Ally · Watch Captain', faction: 'Hollowmere Guard', cr: '6' },
    { name: 'Old Borin of the Mire', role: 'Mentor · Hedge wizard', faction: 'Independent', cr: '4' },
    { name: 'The Bellringer', role: 'Recurring antagonist', faction: 'Cult of the Crown', cr: '9' },
    { name: 'Lady Cerys Marlowe', role: 'Patron · Noble', faction: 'House Marlowe', cr: '3' },
  ];
  return (
    <div className="screen-npclist">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">NPCs</span>
          <h2>Major NPCs ({npcs.length})</h2>
        </div>
        <div className="screen-head-actions">
          <button className="ghost-btn">Validate all</button>
          <button className="primary-btn"><Icon name="plus" size={11}/> New NPC</button>
        </div>
      </header>
      <div className="npc-table-wrap">
        <table className="npc-table">
          <thead>
            <tr><th>Name</th><th>Role</th><th>Faction</th><th className="num">CR</th><th></th></tr>
          </thead>
          <tbody>
            {npcs.map(n => (
              <tr key={n.name}>
                <td><strong>{n.name}</strong></td>
                <td>{n.role}</td>
                <td><span className="faction-pill">{n.faction}</span></td>
                <td className="num">{n.cr}</td>
                <td className="row-actions">
                  <button className="ghost-btn ghost-small">View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

Object.assign(window, {
  ReadStoryFileScreen, ViewCharacterDetailsScreen, StorySeriesWorkspaceScreen,
  TimelineScreen, ListCharactersScreen, ListNPCsScreen,
  NarrateMedallion, ImageGenMedallion,
});
