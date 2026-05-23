/* ============================================================
   Story Details viewer (s-view) — DM-mode reader.
   Two-pane: prose left (annotated), structured data right.
   ============================================================ */

const STORY_VIEW_DATA = {
  meta: {
    id: '014_weathertop',
    title: 'Weathertop',
    series: 'Whispers of the Sundered Crown',
    session: 14,
    date_in_world: 'Hammer 23, 1492 DR',
    played_at: 'May 14, 2026',
    wordcount: 2_640,
    party: ['Aragorn', 'Frodo', 'Gandalf', 'Legolas', 'Samwise', 'Merry', 'Pippin', 'Boromir'],
  },
  summary: 'The party reaches Weathertop at dusk. Aragorn refuses to camp above. Five Nazgûl find them in the dell. Frodo, against warning, puts on the Ring and is wounded by a Morgul blade. The party flees south.',
  body: [
    { kind: 'p', text: "The party reached the foot of Weathertop just as the wind began to pull at their cloaks. **Aragorn** crouched low beside the cairn-stones, one gloved hand pressed flat to the earth as though listening for footsteps the rest of them could not feel." },
    { kind: 'p', text: '"We rest here," he said. "Not above."' },
    { kind: 'note', label: 'DM note', text: 'Aragorn rolled a 19 on his Perception check and chose not to share what he heard. Mark for later — he knows.' },
    { kind: 'h', text: 'The watchfire and what answered it' },
    { kind: 'p', text: "They made a low fire in the bowl below the summit, ringed it with stones, and ate cold pork and apples. *Strider* would not eat. He sat on the lip of the dell, eyes fixed northward, and one by one the hobbits dropped into uneasy sleep." },
    { kind: 'p', text: "It was **Merry** who saw them first — five shapes that were a different kind of dark than the night around them, moving in single file along the ridge. He did not cry out. He simply touched Aragorn's wrist, and Aragorn was already on his feet, sword drawn." },
    { kind: 'note', label: 'Mechanics', text: 'Stealth check for the Nazgûl approach: party WIS (Perception) DC 18. Merry rolled 22 (advantage from Halfling Stealth feat); others all failed. Awareness reaches party 1 round before contact.' },
    { kind: 'h', text: 'A wound that did not bleed' },
    { kind: 'p', text: "Frodo did not mean to. He would say so afterwards, to anyone who would listen, and Gandalf would say *I know, my lad, I know* — but the truth, the truth he could feel even as the chain slid from his neck, was that the Ring had wanted to be put on. And he had let it." },
    { kind: 'p', text: "The world went grey, and the riders had faces." },
    { kind: 'p', text: "The blade that took him in the shoulder was the colour of cold iron. He felt nothing at first. Then he felt everything, all at once, and the cry that left him was not a cry his friends could answer — not on this side of the Veil." },
  ],
  combat: [
    { round: 'R1', who: 'Aragorn', action: 'Longsword vs Nazgûl 1',  d20: 17, total: 22, dmg: '8 slashing', hit: true,  crit: false },
    { round: 'R1', who: 'Frodo',   action: 'Sting vs Nazgûl 2',      d20: 3,  total: 5,  dmg: '—',          hit: false, crit: false },
    { round: 'R1', who: 'Nazgûl 1', action: 'Morgul blade vs Frodo', d20: 19, total: 24, dmg: '5 piercing + DC 15 WIS save', hit: true, crit: false },
    { round: 'R2', who: 'Sam',     action: 'Shortsword vs Nazgûl 1',  d20: 14, total: 17, dmg: '6 slashing', hit: true,  crit: false },
    { round: 'R2', who: 'Aragorn', action: 'Brand vs Nazgûl 3',       d20: 20, total: 25, dmg: '11 fire',    hit: true,  crit: true },
    { round: 'R2', who: 'Nazgûl 1', action: 'Withdraws (Morgul blade taken)', d20: '—', total: '—', dmg: '—', hit: false, crit: false },
  ],
  dcs: [
    { skill: 'WIS · Perception', dc: 18, who: 'Party', result: 'mixed', outcome: 'Merry passed; others failed.' },
    { skill: 'WIS · Saving Throw', dc: 15, who: 'Frodo', result: 'fail', outcome: 'Morgul-shard begins migration.' },
    { skill: 'CHA · Persuasion',  dc: 12, who: 'Aragorn', result: 'pass', outcome: 'Convinces party to flee south, not east.' },
    { skill: 'STR · Athletics',   dc: 10, who: 'Sam',     result: 'pass', outcome: 'Carries Frodo from the dell.' },
  ],
  npcs: [
    { name: 'The Nazgûl', role: 'Antagonist · Cult of the Crown servants', count: 5 },
    { name: 'Bill the Pony', role: 'Hireling · acquired in Bree',          count: 1 },
  ],
  loot: [
    { rarity: 'rare',      name: 'Morgul blade fragment',  meta: 'lodged in Frodo · cursed' },
    { rarity: 'uncommon',  name: 'Athelas (kingsfoil)',    meta: 'gathered en route to Rivendell' },
  ],
};

const STORY_INDEX = [
  { id: '014', title: 'Weathertop', tag: 'latest' },
  { id: '013', title: 'Bree' },
  { id: '012', title: 'Trollshaws' },
  { id: '011', title: 'Bruinen River' },
  { id: '010', title: 'Last Bridge' },
];

const RARITY_COLOR = {
  common: '#9e9e9e', uncommon: '#4caf50', rare: '#2196f3', 'very-rare': '#9c27b0', legendary: '#ff9800', artifact: '#f44336',
};

const StoryDetailsScreen = ({ ctx, setCtx }) => {
  const data = STORY_VIEW_DATA;
  const renderInline = (s) => {
    const parts = [];
    const re = /\*\*([^*]+)\*\*|\*([^*]+)\*/g;
    let m, last = 0;
    while ((m = re.exec(s)) !== null) {
      if (m.index > last) parts.push(s.slice(last, m.index));
      if (m[1]) parts.push(<strong key={parts.length}>{m[1]}</strong>);
      else if (m[2]) parts.push(<em key={parts.length}>{m[2]}</em>);
      last = re.lastIndex;
    }
    if (last < s.length) parts.push(s.slice(last));
    return parts;
  };
  const goBack = () => setCtx({ ...ctx, _jumpTo: { sectionId: 'stories', itemId: 'work-series' } });

  return (
    <div>
      <div className="action-back-row">
        <button className="action-back" onClick={goBack}>
          <Icon name="chevronLeft" size={11}/> Back to series workspace
        </button>
        <span className="action-entry-pip">
          <span className="dot"/>
          DM view · annotations on
        </span>
      </div>

      <header className="screen-head" style={{ marginBottom: 16, paddingBottom: 12 }}>
        <div>
          <span className="reader-eyebrow">View story details</span>
          <h2>Story {data.meta.session.toString().padStart(3, '0')} · {data.meta.title}</h2>
          <p className="screen-blurb">DM-mode read of <em>{data.meta.title}</em>. Prose left, structured data right. This view is read-only — use Amend or Notes to edit.</p>
        </div>
        <div className="screen-head-actions">
          <button className="ghost-btn"><Icon name="search" size={11}/> Find in story</button>
          <button className="ghost-btn"><Icon name="sparkle" size={11}/> Analyze</button>
          <button className="primary-btn">Amend</button>
        </div>
      </header>

      <div className="screen-storyview">
        {/* LEFT — prose */}
        <article className="storyview-prose">
          <div className="storyview-meta-row">
            <span>series · <b>{data.meta.series}</b></span>
            <span className="dot-sep">·</span>
            <span>session · <b>{String(data.meta.session).padStart(3, '0')}</b></span>
            <span className="dot-sep">·</span>
            <span>in-world · <b>{data.meta.date_in_world}</b></span>
            <span className="dot-sep">·</span>
            <span>played · <b>{data.meta.played_at}</b></span>
            <span className="dot-sep">·</span>
            <span><b>{data.meta.wordcount.toLocaleString()}</b> words</span>
          </div>
          <span className="reader-eyebrow">Title</span>
          <h1>{data.meta.title}</h1>
          <p className="summary">{data.summary}</p>

          <div className="body">
            {data.body.map((blk, i) => {
              if (blk.kind === 'h') return <h3 key={i}>{blk.text}</h3>;
              if (blk.kind === 'note') return (
                <span key={i} className="annotation">
                  <span className="ann-label">{blk.label}</span>
                  {blk.text}
                </span>
              );
              return <p key={i}>{renderInline(blk.text)}</p>;
            })}
          </div>
        </article>

        {/* RIGHT — structured rail */}
        <aside className="storyview-rail">
          <section className="storyview-panel">
            <h4>Party present <span className="count">{data.meta.party.length}</span></h4>
            <ul>
              {data.meta.party.map(name => (
                <li key={name} className="npc-mention">
                  <span className="npc-pip">{name[0]}</span>
                  <span className="npc-info">
                    <span className="npc-name">{name}</span>
                    <span className="npc-role">present this session</span>
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="storyview-panel">
            <h4>Combat log <span className="count">{data.combat.length} entries</span></h4>
            <ul>
              {data.combat.map((c, i) => (
                <li key={i} className="combat-entry">
                  <span className="round">{c.round}</span>
                  <span>
                    <span className="who">{c.who}</span><br/>
                    {c.action}
                  </span>
                  <span className={`roll ${c.crit ? 'crit' : c.hit ? 'hit' : 'miss'}`}>
                    {c.d20 === '—' ? '—' : <>d20:{c.d20}<br/><span style={{ fontSize: 9 }}>total {c.total}</span></>}
                  </span>
                </li>
              ))}
            </ul>
          </section>

          <section className="storyview-panel">
            <h4>DC checks <span className="count">{data.dcs.length}</span></h4>
            <ul>
              {data.dcs.map((d, i) => (
                <li key={i} className="dc-entry">
                  <div>
                    <span className="skill">{d.skill}</span><br/>
                    <span style={{ fontSize: 11, fontStyle: 'italic', color: 'var(--ink-dim)' }}>{d.outcome}</span>
                  </div>
                  <span className={`target ${d.result === 'pass' ? 'ok' : d.result === 'fail' ? 'fail' : ''}`}>DC {d.dc}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--brass-dim)' }}>{d.who}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="storyview-panel">
            <h4>NPC mentions <span className="count">{data.npcs.length}</span></h4>
            <ul>
              {data.npcs.map(n => (
                <li key={n.name} className="npc-mention">
                  <span className="npc-pip">{n.name[0]}</span>
                  <span className="npc-info">
                    <span className="npc-name">{n.name}</span>
                    <span className="npc-role">{n.role}</span>
                  </span>
                  <span className="npc-count">×{n.count}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="storyview-panel">
            <h4>Loot &amp; items <span className="count">{data.loot.length}</span></h4>
            <ul>
              {data.loot.map((l, i) => (
                <li key={i} className="loot-entry">
                  <span className="loot-rarity" style={{ background: RARITY_COLOR[l.rarity] || '#777' }}/>
                  <span className="loot-name">{l.name}</span>
                  <span className="loot-meta">{l.meta}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="storyview-panel">
            <h4>Other stories in series <span className="count">{STORY_INDEX.length}</span></h4>
            <ul>
              {STORY_INDEX.map(s => (
                <li key={s.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px dashed var(--rule)' }}>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--ink)' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--brass-dim)', marginRight: 8 }}>{s.id}</span>
                    {s.title}
                  </span>
                  {s.tag && <span className="latest-tag">{s.tag}</span>}
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
};

window.StoryDetailsScreen = StoryDetailsScreen;
