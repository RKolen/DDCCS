/* Screen router — maps section.id + item.id → deep screen component.
   Default fallback is a thoughtful ActionForm.
*/

const ScreenRouter = ({ section, item, ctx, setCtx }) => {
  if (!section || !item) return null;
  const key = `${section.id}/${item.id}`;

  /* Stash item id in ctx for screens that branch on it */
  const ictx = { ...ctx, _itemId: item.id, _sectionId: section.id };
  const set = (next) => setCtx({ ...next, _itemId: next._itemId || item.id });

  /* ===== Characters ===== */
  if (key === 'characters/list')     return <ListCharactersScreen     ctx={ictx} setCtx={set}/>;
  if (key === 'characters/view')     return <ViewCharacterDetailsScreen ctx={ictx} setCtx={set}/>;
  if (key === 'characters/consult')  return <ConsultScreen           ctx={ictx} setCtx={set}/>;
  if (key === 'characters/ascii')    return <DeprecatedScreen        item={item}/>;

  /* ===== Stories ===== */
  if (key === 'stories/work-series') return <StorySeriesWorkspaceScreen ctx={ictx} setCtx={set}/>;
  if (key === 'stories/timeline')    return <TimelineScreen/>;
  if (key === 'stories/spells')      return <SpellRegistryScreen/>;
  if (key === 'stories/new-series')  return <NewSeriesWizardScreen/>;

  /* ===== Read Stories ===== */
  if (key === 'read/r-story')        return <ReadStoryFileScreen     ctx={ictx} setCtx={set}/>;
  if (key === 'read/r-char')         return <ViewCharacterDetailsScreen ctx={ictx} setCtx={set}/>;

  /* ===== NPCs ===== */
  if (key === 'npcs/n-list')         return <ListNPCsScreen/>;
  if (key === 'npcs/n-view')         return <NPCDetailsScreen/>;

  /* ===== Settings ===== */
  if (section.id === 'config') {
    /* All settings items route to the SettingsScreen, picking a tab */
    const map = { 'c-view': 'view', 'c-ai': 'ai', 'c-rag': 'rag', 'c-display': 'display', 'c-paths': 'paths', 'c-validate': 'validate' };
    const settingsTab = map[item.id] || 'view';
    if (item.id === 'c-save') return <SaveConfirmScreen/>;
    return <SettingsScreen ctx={{ ...ictx, settingsTab }} setCtx={set}/>;
  }

  /* ===== Model Profile ===== */
  if (section.id === 'model')        return <ModelProfileScreen      ctx={ictx} setCtx={set}/>;

  /* ===== Tools & Batch ===== */
  if (key === 'tools/t-recent' ||
      key === 'tools/t-search' ||
      key === 'tools/t-stats'  ||
      key === 'tools/t-clear')      return <ToolsHistoryScreen      ctx={ictx}/>;
  if (key === 'tools/t-level' ||
      key === 'tools/t-item')       return <BatchOpScreen           ctx={ictx}/>;

  /* Default: generic action form */
  return <GenericActionScreen section={section} item={item}/>;
};

/* ============================================================
   Generic action — for forms we haven't custom-built yet.
   ============================================================ */
const GenericActionScreen = ({ section, item }) => {
  const isAI = !!item.ai;
  return (
    <div className="screen-generic">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">{section.label}</span>
          <h2>
            {item.label}
            {isAI && <AiTag label="AI"/>}
            {item.slow && <SlowTag/>}
          </h2>
          <p className="screen-blurb">
            {isAI
              ? 'Uses the active model profile. Result streams into the activity drawer; keep working in other sections while it runs.'
              : 'Configure the inputs below and run when ready.'}
          </p>
        </div>
        <div className="screen-head-actions">
          <button className="ghost-btn">Cancel</button>
          <button className="primary-btn">
            {isAI && <Icon name="sparkle" size={11}/>}
            Run
          </button>
        </div>
      </header>

      <div className="generic-form">
        <div className="form-grid">
          <label className="form-row">
            <span>Series</span>
            <select defaultValue="whispers">
              <option value="whispers">Whispers of the Sundered Crown</option>
              <option value="ironroot">The Ironroot Pact</option>
              <option value="mistveil">Mistveil Quest</option>
            </select>
          </label>
          {section.id === 'characters' && (
            <label className="form-row">
              <span>Target character</span>
              <select>
                {MENU_DATA.characters.map(c => <option key={c.name}>{c.name}</option>)}
              </select>
            </label>
          )}
          {section.id === 'stories' && (
            <label className="form-row">
              <span>Target story</span>
              <select>
                {MENU_DATA.recentStories.map(s => <option key={s.title}>{s.title}</option>)}
              </select>
            </label>
          )}
          <label className="form-row">
            <span>Notes / prompt</span>
            <textarea rows="5" placeholder={isAI ? 'Optional context to steer the model…' : 'Optional notes…'}/>
          </label>
          {isAI && (
            <label className="form-row">
              <span>Model</span>
              <select defaultValue="sonnet">
                <option value="sonnet">Sonnet · Narrative <i>(active)</i></option>
                <option value="haiku">Haiku · Analysis</option>
                <option value="opus">Opus · Deep Arc (slow)</option>
              </select>
            </label>
          )}
        </div>
        {isAI && (
          <div className="form-side">
            <h4>What this does</h4>
            <p>{generatePreview(section.id, item.id)}</p>
            <h4>Recent similar runs</h4>
            <ul className="form-side-list">
              <li><span>2 days ago</span><span>2,400 tokens · 14s</span></li>
              <li><span>1 week ago</span><span>1,840 tokens · 12s</span></li>
              <li><span>2 weeks ago</span><span>3,100 tokens · 18s</span></li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

const generatePreview = (sectionId, itemId) => {
  const previews = {
    'characters/consult':  'Asks the active character for their take on a question in their own voice, using their profile, arc state, and recent story history.',
    'characters/verify':   'Checks the profile against schema + cross-references every story file that mentions this character.',
    'stories/new-series':  'Drafts a series outline, opening hook, and inciting incident from a one-line premise.',
    'characters/edit':     'Opens the profile in form mode. Manual edits — no AI.',
  };
  return previews[`${sectionId}/${itemId}`] || 'Runs the operation against the active campaign.';
};

/* ============================================================
   Smaller bespoke screens
   ============================================================ */
const ConsultScreen = ({ ctx }) => {
  const char = MENU_DATA.characters[ctx.charIdx ?? 0];
  return (
    <div className="screen-consult">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Character consultation <AiTag label="AI"/></span>
          <h2>{char.name}</h2>
          <p className="screen-blurb">Speaks in character. Draws on profile, arc state, and recent story appearances.</p>
        </div>
      </header>
      <div className="consult-pane">
        <div className="consult-thread">
          <div className="consult-bubble role-dm">
            <span className="bubble-tag">DM</span>
            <p>What does she fear most, right now?</p>
          </div>
          <div className="consult-bubble role-char">
            <span className="bubble-tag">{char.name} <AiTag/></span>
            <p>That her sister isn't in the Sundered Crown at all. That the entire pact, every page of the journal, every bell that's rung — was a lure. And that she'll learn this only after the cost has already been paid.</p>
          </div>
        </div>
        <div className="consult-input">
          <textarea placeholder="Ask the character…" rows="2"/>
          <button className="primary-btn"><Icon name="sparkle" size={11}/> Ask</button>
        </div>
      </div>
    </div>
  );
};

const SpellRegistryScreen = () => {
  const spells = [
    { name: 'Eldritch Blast', school: 'Evocation', level: '0', class: 'Warlock', source: 'PHB' },
    { name: 'Mending', school: 'Transmutation', level: '0', class: 'Cleric', source: 'PHB' },
    { name: 'Hex', school: 'Enchantment', level: '1', class: 'Warlock', source: 'PHB' },
    { name: 'Speak with Bells', school: 'Divination', level: '2', class: 'Custom', source: 'campaign · whispers', custom: true },
    { name: 'Ledger Ward', school: 'Abjuration', level: '3', class: 'Custom', source: 'campaign · whispers', custom: true },
    { name: 'Hunter\'s Mark', school: 'Divination', level: '1', class: 'Ranger', source: 'PHB' },
  ];
  return (
    <div className="screen-spells">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Spell registry</span>
          <h2>Spells in play ({spells.length})</h2>
        </div>
        <div className="screen-head-actions">
          <button className="ghost-btn"><Icon name="search" size={12}/> Find</button>
          <button className="primary-btn"><Icon name="plus" size={11}/> Custom spell</button>
        </div>
      </header>
      <div className="npc-table-wrap">
        <table className="npc-table">
          <thead><tr><th>Name</th><th>School</th><th className="num">Level</th><th>Class</th><th>Source</th></tr></thead>
          <tbody>
            {spells.map(s => (
              <tr key={s.name}>
                <td><strong>{s.name}</strong>{s.custom && <span className="custom-pill">custom</span>}</td>
                <td>{s.school}</td>
                <td className="num">{s.level}</td>
                <td>{s.class}</td>
                <td className="mono muted">{s.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const NewSeriesWizardScreen = () => (
  <div className="screen-newseries">
    <header className="screen-head">
      <div>
        <span className="reader-eyebrow">New series <AiTag label="AI"/></span>
        <h2>Start a story series</h2>
        <p className="screen-blurb">Drafts an outline, opening hook, and inciting incident from a one-line premise.</p>
      </div>
    </header>
    <div className="wizard">
      <ol className="wizard-steps">
        <li className="active"><span>1</span> Premise</li>
        <li><span>2</span> Tone &amp; constraints</li>
        <li><span>3</span> Party</li>
        <li><span>4</span> Review</li>
      </ol>
      <div className="wizard-pane">
        <label className="form-row">
          <span>One-line premise</span>
          <input type="text" placeholder='e.g. "A bell rings in a village that has no bell."'/>
        </label>
        <label className="form-row">
          <span>Genre</span>
          <div className="seg-control">
            <button className="seg active">Dark fantasy</button>
            <button className="seg">Heroic</button>
            <button className="seg">Mystery</button>
            <button className="seg">Horror</button>
          </div>
        </label>
        <label className="form-row">
          <span>Series length</span>
          <div className="seg-control">
            <button className="seg">3–5 stories</button>
            <button className="seg active">6–10 stories</button>
            <button className="seg">11+ stories</button>
          </div>
        </label>
        <div className="wizard-foot">
          <button className="ghost-btn">Back</button>
          <button className="primary-btn"><Icon name="sparkle" size={11}/> Draft outline</button>
        </div>
      </div>
    </div>
  </div>
);

const NPCDetailsScreen = () => (
  <div className="screen-npcdetails">
    <header className="screen-head">
      <div>
        <span className="reader-eyebrow">NPC</span>
        <h2>The Bellringer</h2>
        <div className="char-sheet-sub">
          <span>Recurring antagonist</span>
          <span className="dot-sep">·</span>
          <span>Cult of the Crown</span>
          <span className="dot-sep">·</span>
          <span>CR 9</span>
        </div>
      </div>
    </header>
    <div className="char-section-grid">
      <section className="char-section">
        <h4>Description</h4>
        <p>A cowled figure who rings a bell that should not exist. The bell, when rung, draws the dead from their cairns; the figure beneath the cowl is, herself, a memory of someone the party will recognize. Eventually.</p>
      </section>
      <section className="char-section">
        <h4>Appearances</h4>
        <ul className="story-mini-list">
          <li><span>The Bell of Vellishar</span><span>seen — 3 days ago</span></li>
          <li><span>Smoke at the Northgate</span><span>heard — 1 week ago</span></li>
          <li><span>A Ledger of Names</span><span>foreshadowed — 2 weeks ago</span></li>
        </ul>
      </section>
      <section className="char-section">
        <h4>Stat block</h4>
        <div className="ability-grid">
          {[['STR', 12, 1], ['DEX', 18, 4], ['CON', 16, 3], ['INT', 16, 3], ['WIS', 14, 2], ['CHA', 20, 5]].map(([k, v, m]) => (
            <div key={k} className="ability-cell">
              <span className="ability-name">{k}</span>
              <span className="ability-val">{v}</span>
              <span className="ability-mod">{m >= 0 ? '+' : ''}{m}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  </div>
);

const DeprecatedScreen = ({ item }) => (
  <div className="screen-deprecated">
    <div className="deprecated-card">
      <span className="deprecated-eyebrow">Deprecated</span>
      <h2>{item.label}</h2>
      <p>{item.note || 'This command is no longer supported.'}</p>
      <p>Character portraits are now produced through the <strong>ComfyUI image pipeline</strong>, attached automatically to each character profile. To generate or regenerate a portrait, open the character details and use <em>Generate image</em>.</p>
      <div>
        <button className="ghost-btn">Go to character details</button>
      </div>
    </div>
  </div>
);

const SaveConfirmScreen = () => (
  <div className="screen-confirm">
    <header className="screen-head"><h2>Save configuration</h2></header>
    <div className="confirm-card">
      <p>Write the current in-memory configuration to <code className="mono">game_data/config.json</code>.</p>
      <p>The file will be backed up to <code className="mono">.cache/config.json.bak</code> first.</p>
      <div className="confirm-actions">
        <button className="ghost-btn">Cancel</button>
        <button className="primary-btn">Save</button>
      </div>
    </div>
  </div>
);

Object.assign(window, {
  ScreenRouter, GenericActionScreen, ConsultScreen, SpellRegistryScreen,
  NewSeriesWizardScreen, NPCDetailsScreen, DeprecatedScreen, SaveConfirmScreen,
});
