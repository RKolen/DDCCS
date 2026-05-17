/* Deep screens — admin domain (settings, tools, model profile, NPC details)
   Reads MENU_DATA and shared atoms from window.
*/

/* ============================================================
   Settings — multi-tab form (AI, RAG, Display, Paths)
   ============================================================ */
const SettingsScreen = ({ ctx, setCtx }) => {
  const tab = ctx.settingsTab || 'ai';
  const tabs = [
    { id: 'view',     label: 'Current' },
    { id: 'ai',       label: 'AI' },
    { id: 'rag',      label: 'RAG' },
    { id: 'display',  label: 'Display' },
    { id: 'paths',    label: 'Paths' },
    { id: 'validate', label: 'Validate' },
  ];
  return (
    <div className="screen-settings">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Settings</span>
          <h2>Configuration</h2>
        </div>
        <div className="screen-head-actions">
          <button className="ghost-btn">Reset</button>
          <button className="primary-btn">Save configuration</button>
        </div>
      </header>
      <nav className="settings-tabs">
        {tabs.map(t => (
          <button key={t.id}
            className={`settings-tab${t.id === tab ? ' active' : ''}`}
            onClick={() => setCtx({ ...ctx, settingsTab: t.id })}>
            {t.label}
          </button>
        ))}
      </nav>
      <div className="settings-body">
        {tab === 'view'    && <CurrentConfigPane/>}
        {tab === 'ai'      && <AIConfigPane/>}
        {tab === 'rag'     && <RAGConfigPane/>}
        {tab === 'display' && <DisplayConfigPane/>}
        {tab === 'paths'   && <PathsConfigPane/>}
        {tab === 'validate'&& <ValidatePane/>}
      </div>
    </div>
  );
};

const CurrentConfigPane = () => (
  <div className="config-readout">
    <div className="config-group">
      <h4>AI</h4>
      <dl>
        <dt>Model</dt><dd>claude-sonnet-4-5</dd>
        <dt>Base URL</dt><dd className="muted">(default)</dd>
        <dt>Temperature</dt><dd>0.7</dd>
        <dt>Max Tokens</dt><dd>2,048</dd>
        <dt>Enabled</dt><dd className="ok">yes</dd>
      </dl>
    </div>
    <div className="config-group">
      <h4>RAG</h4>
      <dl>
        <dt>Enabled</dt><dd className="ok">yes</dd>
        <dt>Cache Backend</dt><dd>sqlite</dd>
        <dt>Cache TTL</dt><dd>3,600s</dd>
        <dt>Search Depth</dt><dd>4</dd>
        <dt>Min Relevance</dt><dd>0.62</dd>
      </dl>
    </div>
    <div className="config-group">
      <h4>Display</h4>
      <dl>
        <dt>Use Rich</dt><dd className="ok">yes</dd>
        <dt>Theme</dt><dd>dark-parchment</dd>
        <dt>Max Line Width</dt><dd>100</dd>
        <dt>TTS Enabled</dt><dd>yes</dd>
        <dt>TTS Voice</dt><dd>narrator-warm-1</dd>
      </dl>
    </div>
    <div className="config-group">
      <h4>Paths</h4>
      <dl>
        <dt>Game Data</dt><dd className="mono">./game_data</dd>
        <dt>Cache Dir</dt><dd className="mono">./.cache</dd>
        <dt>Vector DB</dt><dd className="mono">./.cache/vectors.db</dd>
      </dl>
    </div>
  </div>
);

const AIConfigPane = () => {
  const [temp, setTemp] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(2048);
  return (
    <div className="config-form">
      <div className="form-grid">
        <label className="form-row">
          <span>API key</span>
          <div className="input-secret">
            <input type="password" defaultValue="sk-ant-•••••••••••••••••••••••••••"/>
            <button className="secret-reveal">Reveal</button>
          </div>
          <small>Stored locally in <code>game_data/config.json</code>.</small>
        </label>
        <label className="form-row">
          <span>Base URL</span>
          <input type="text" placeholder="https://api.anthropic.com (default)"/>
        </label>
        <label className="form-row">
          <span>Model</span>
          <select defaultValue="claude-sonnet-4-5">
            <option>claude-sonnet-4-5</option>
            <option>claude-haiku-4-5</option>
            <option>claude-opus-4-5</option>
            <option>custom…</option>
          </select>
        </label>
        <label className="form-row">
          <span>Temperature</span>
          <div className="slider-row">
            <input type="range" min="0" max="2" step="0.05" value={temp} onChange={e => setTemp(parseFloat(e.target.value))}/>
            <span className="slider-val mono">{temp.toFixed(2)}</span>
          </div>
          <small>Lower = consistent. Higher = creative. <code>0.7</code> is a balanced default for narrative generation.</small>
        </label>
        <label className="form-row">
          <span>Max tokens</span>
          <input type="number" value={maxTokens} onChange={e => setMaxTokens(+e.target.value)}/>
        </label>
        <label className="form-row toggle-row">
          <span>Enabled</span>
          <Toggle defaultOn={true}/>
        </label>
      </div>
    </div>
  );
};

const RAGConfigPane = () => (
  <div className="config-form">
    <div className="form-grid">
      <label className="form-row toggle-row"><span>Enabled</span><Toggle defaultOn={true}/></label>
      <label className="form-row"><span>Wiki base URL</span><input type="text" placeholder="https://campaign-wiki.local"/></label>
      <label className="form-row"><span>Rules base URL</span><input type="text" placeholder="https://dnd-rules.local"/></label>
      <label className="form-row"><span>Cache TTL (seconds)</span><input type="number" defaultValue="3600"/></label>
      <label className="form-row"><span>Max cache size</span><input type="number" defaultValue="500"/></label>
      <label className="form-row">
        <span>Search depth</span>
        <input type="number" defaultValue="4"/>
        <small>How many hops the retriever follows.</small>
      </label>
      <label className="form-row">
        <span>Min relevance</span>
        <input type="number" step="0.01" defaultValue="0.62"/>
      </label>
      <label className="form-row">
        <span>Cache backend</span>
        <div className="seg-control">
          <button className="seg active">sqlite</button>
          <button className="seg">json</button>
        </div>
      </label>
      <label className="form-row"><span>Vector DB path</span><input type="text" defaultValue="./.cache/vectors.db" className="mono"/></label>
    </div>
  </div>
);

const DisplayConfigPane = () => (
  <div className="config-form">
    <div className="form-grid">
      <label className="form-row toggle-row"><span>Use Rich terminal</span><Toggle defaultOn={true}/></label>
      <label className="form-row">
        <span>Theme</span>
        <select defaultValue="dark-parchment">
          <option>dark-parchment</option>
          <option>candlelit</option>
          <option>moonlit</option>
          <option>plain</option>
        </select>
      </label>
      <label className="form-row"><span>Max line width</span><input type="number" defaultValue="100"/></label>
      <label className="form-row toggle-row"><span>TTS enabled</span><Toggle defaultOn={true}/></label>
      <label className="form-row">
        <span>TTS voice</span>
        <select defaultValue="narrator-warm-1">
          <option>narrator-warm-1</option>
          <option>narrator-grim-2</option>
          <option>narrator-bardic-3</option>
        </select>
      </label>
      <label className="form-row">
        <span>TTS speed</span>
        <div className="slider-row">
          <input type="range" min="0.5" max="2" step="0.05" defaultValue="1"/>
          <span className="slider-val mono">1.00×</span>
        </div>
      </label>
    </div>
  </div>
);

const PathsConfigPane = () => (
  <div className="config-form">
    <div className="form-grid">
      <label className="form-row"><span>Game data directory</span><input type="text" defaultValue="./game_data" className="mono"/></label>
      <label className="form-row"><span>Cache directory</span><input type="text" defaultValue="./.cache" className="mono"/></label>
    </div>
  </div>
);

const ValidatePane = () => (
  <div className="validate-pane">
    <header className="validate-head">
      <h4>Validation report</h4>
      <button className="ghost-btn">Re-run</button>
    </header>
    <ul className="validate-list">
      <li className="valid"><span className="check">✓</span> AI settings valid · model resolved</li>
      <li className="valid"><span className="check">✓</span> RAG settings valid · 24 documents indexed</li>
      <li className="valid"><span className="check">✓</span> Path settings valid · all paths exist</li>
      <li className="warn"><span className="check">!</span> TTS voice <code>narrator-grim-2</code> not installed locally — will fall back</li>
      <li className="valid"><span className="check">✓</span> Active campaign has 4 party members · all profiles found</li>
    </ul>
  </div>
);

/* ============================================================
   Switch Model Profile
   ============================================================ */
const ModelProfileScreen = ({ ctx, setCtx }) => {
  const profiles = [
    { id: 'sonnet-narr', name: 'Sonnet · Narrative',  model: 'claude-sonnet-4-5', task: 'story_generation', detail: 'Long-form, consistent voice. Default for story continuation and session results.', active: true },
    { id: 'haiku-anal',  name: 'Haiku · Analysis',    model: 'claude-haiku-4-5',  task: 'analysis',         detail: 'Fast and cheap. Used for character action extraction, DC suggestions.' },
    { id: 'opus-deep',   name: 'Opus · Deep Arc',     model: 'claude-opus-4-5',   task: 'arc_analysis',     detail: 'Slow, expensive, nuanced. Use for character arc and series analysis.', slow: true },
    { id: 'local-llama', name: 'Local · Llama 70B',   model: 'llama-3.1-70b',     task: 'fallback',         detail: 'Runs locally via Ollama. Used when network is unavailable.' },
  ];
  const activeId = ctx.modelId || profiles.find(p => p.active).id;
  return (
    <div className="screen-models">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Model profile</span>
          <h2>Choose the active LLM for this session</h2>
        </div>
        <div className="screen-head-actions">
          <button className="ghost-btn"><Icon name="plus" size={11}/> Add profile</button>
        </div>
      </header>
      <ul className="model-list">
        {profiles.map(p => (
          <li key={p.id}>
            <button
              className={`model-card${p.id === activeId ? ' active' : ''}`}
              onClick={() => setCtx({ ...ctx, modelId: p.id })}>
              <div className="model-card-head">
                <h4>{p.name}</h4>
                <div className="model-card-tags">
                  <code className="model-tag">{p.model}</code>
                  <span className="model-task">{p.task}</span>
                  {p.slow && <SlowTag/>}
                </div>
              </div>
              <p>{p.detail}</p>
              <div className="model-card-foot">
                {p.id === activeId ? <span className="active-badge">Active</span> : <span className="muted-tag">Click to activate</span>}
              </div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

/* ============================================================
   Tools & Batch — History views, batch ops
   ============================================================ */
const ToolsHistoryScreen = ({ ctx }) => {
  const variant = ctx._itemId; /* t-recent | t-search | t-stats | t-clear */
  const entries = [
    { date: '2026-05-12', status: 'ok', cmd: 'story generate --series whispers --prompt "the bell rings"' },
    { date: '2026-05-12', status: 'ok', cmd: 'characters consult vesper --question "What does she fear most?"' },
    { date: '2026-05-12', status: 'fail', cmd: 'reindex --vector-db' },
    { date: '2026-05-11', status: 'ok', cmd: 'session-results generate --story 004_bell' },
    { date: '2026-05-11', status: 'ok', cmd: 'batch level-up --all +1' },
    { date: '2026-05-10', status: 'ok', cmd: 'story add --series whispers' },
    { date: '2026-05-09', status: 'ok', cmd: 'npc validate' },
  ];

  if (variant === 't-stats') {
    return (
      <div className="screen-stats">
        <header className="screen-head"><h2>History statistics</h2></header>
        <div className="stat-cards">
          {[
            ['Total commands', '1,284'],
            ['Sessions', '47'],
            ['Avg / session', '27.3'],
            ['Failures', '38', 'danger'],
          ].map(([l, v, tone]) => (
            <div key={l} className={`big-stat${tone ? ' tone-' + tone : ''}`}>
              <span className="big-stat-val">{v}</span>
              <span className="big-stat-label">{l}</span>
            </div>
          ))}
        </div>
        <section className="stat-list-section">
          <h4>Most used commands</h4>
          <ul className="stat-bars">
            {[
              ['story generate', 184],
              ['consult', 142],
              ['session-results generate', 98],
              ['npc view', 72],
              ['reindex', 24],
            ].map(([cmd, n]) => (
              <li key={cmd}>
                <span className="bar-label mono">{cmd}</span>
                <span className="bar-track"><span className="bar-fill" style={{ width: `${(n/184)*100}%` }}/></span>
                <span className="bar-val">{n}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    );
  }

  if (variant === 't-clear') {
    return (
      <div className="screen-confirm">
        <header className="screen-head"><h2>Clear command history</h2></header>
        <div className="confirm-card danger">
          <p>This will permanently delete <strong>1,284 history entries</strong> across <strong>47 sessions</strong>.</p>
          <p>This cannot be undone. Consider exporting history first.</p>
          <div className="confirm-actions">
            <button className="ghost-btn">Export first</button>
            <button className="danger-btn">Clear all history</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-history">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">History</span>
          <h2>{variant === 't-search' ? 'Search history' : 'Recent commands'}</h2>
        </div>
        <div className="screen-head-actions">
          {variant === 't-search'
            ? <input className="screen-search" type="text" placeholder="Search history…"/>
            : <select className="ghost-btn"><option>Last 10</option><option>Last 50</option><option>All</option></select>}
          <button className="ghost-btn">Export</button>
        </div>
      </header>
      <ol className="history-list">
        {entries.map((e, i) => (
          <li key={i} className={`history-row status-${e.status}`}>
            <span className="history-date mono">{e.date}</span>
            <span className={`history-status status-${e.status}`}>{e.status === 'ok' ? '[OK]' : '[FAIL]'}</span>
            <code className="history-cmd">{e.cmd}</code>
            <button className="ghost-btn ghost-small">Re-run</button>
          </li>
        ))}
      </ol>
    </div>
  );
};

const BatchOpScreen = ({ ctx }) => {
  const isLevel = ctx._itemId === 't-level';
  return (
    <div className="screen-batch">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Batch operation</span>
          <h2>{isLevel ? 'Batch level-up characters' : 'Batch add item to characters'}</h2>
        </div>
      </header>
      <div className="batch-body">
        <section className="batch-targets">
          <h4>Targets</h4>
          <ul className="batch-target-list">
            {MENU_DATA.characters.map(c => (
              <li key={c.name}>
                <label className="batch-target">
                  <input type="checkbox" defaultChecked/>
                  <span className="target-name">{c.name}</span>
                  <span className="target-meta">{c.class} · L{c.level}</span>
                </label>
              </li>
            ))}
          </ul>
          <button className="ghost-btn ghost-small">Select all party members</button>
        </section>
        <section className="batch-config">
          <h4>Parameters</h4>
          {isLevel ? (
            <>
              <label className="form-row"><span>Levels to add</span><input type="number" defaultValue="1" min="1" max="20"/></label>
              <p className="caption">Each character will roll for new HP using their class's hit die. ASIs at levels 4, 8, 12, 16, 19 will be queued for review.</p>
            </>
          ) : (
            <>
              <label className="form-row"><span>Item name</span><input type="text" placeholder="e.g. Potion of Healing"/></label>
              <label className="form-row"><span>Quantity</span><input type="number" defaultValue="1" min="1"/></label>
              <label className="form-row toggle-row"><span>Identified</span><Toggle defaultOn={true}/></label>
            </>
          )}
          <div className="batch-foot">
            <button className="ghost-btn">Dry run</button>
            <button className="primary-btn">Apply to 4 characters</button>
          </div>
        </section>
      </div>
    </div>
  );
};

/* ============================================================
   Activity drawer — expanded full-screen view
   ============================================================ */
const ActivityFullScreen = ({ onClose }) => {
  const items = [
    ...MENU_DATA.activityLog,
    { kind: 'ai', status: 'done', label: 'DM narrative suggestions', detail: 'Whispers · 3 suggestions · 8s ago' },
    { kind: 'ai', status: 'done', label: 'Character consult: Vesper', detail: '"What does she fear most?" · 12s' },
    { kind: 'index', status: 'done', label: 'Drupal sync', detail: '8 files pushed · 14s ago' },
    { kind: 'batch', status: 'done', label: 'Batch add item: Healing potion ×3', detail: '4/4 succeeded · 31s ago' },
    { kind: 'ai', status: 'done', label: 'Combat → narrative conversion', detail: 'Trollshaws ambush · 2,400 tokens · 22s' },
  ];
  const groups = {
    running: items.filter(i => i.status === 'running'),
    failed:  items.filter(i => i.status === 'failed'),
    done:    items.filter(i => i.status === 'done'),
  };
  return (
    <div className="activity-fullscreen">
      <header className="activity-full-head">
        <div>
          <span className="reader-eyebrow">Activity log</span>
          <h2>All operations</h2>
        </div>
        <div className="activity-full-stats">
          <span className="pill pill-running">{groups.running.length} running</span>
          <span className="pill pill-failed">{groups.failed.length} failed</span>
          <span className="pill pill-done">{groups.done.length} completed</span>
        </div>
        <button className="ghost-btn" onClick={onClose}><Icon name="close" size={12}/> Close</button>
      </header>
      <div className="activity-full-body">
        {groups.running.length > 0 && (
          <section><h4>Running</h4>
            {groups.running.map((it, i) => <ActivityFullRow key={i} item={it}/>)}
          </section>
        )}
        {groups.failed.length > 0 && (
          <section><h4>Failed</h4>
            {groups.failed.map((it, i) => <ActivityFullRow key={i} item={it}/>)}
          </section>
        )}
        <section><h4>Completed</h4>
          {groups.done.map((it, i) => <ActivityFullRow key={i} item={it}/>)}
        </section>
      </div>
    </div>
  );
};
const ActivityFullRow = ({ item }) => (
  <div className={`activity-full-row status-${item.status}`}>
    <span className={`dot dot-${item.status}`}/>
    <div className="activity-full-meta">
      <div className="activity-full-label">
        {item.kind === 'ai' && <Icon name="sparkle" size={11}/>}
        {item.label}
      </div>
      <div className="activity-full-detail">{item.detail}</div>
    </div>
    {item.progress != null && (
      <div className="activity-full-bar"><div className="fill" style={{width: `${item.progress*100}%`}}/></div>
    )}
    {item.status === 'failed' && <button className="ghost-btn ghost-small">Retry</button>}
    {item.status === 'done' && <button className="ghost-btn ghost-small">Open</button>}
  </div>
);

/* ============================================================
   Toggle atom
   ============================================================ */
const Toggle = ({ defaultOn = false, onChange }) => {
  const [on, setOn] = useState(defaultOn);
  return (
    <button className={`toggle${on ? ' on' : ''}`} onClick={() => { setOn(!on); onChange && onChange(!on); }}>
      <span className="toggle-knob"/>
    </button>
  );
};

Object.assign(window, {
  SettingsScreen, ModelProfileScreen, ToolsHistoryScreen, BatchOpScreen,
  ActivityFullScreen, Toggle,
});
