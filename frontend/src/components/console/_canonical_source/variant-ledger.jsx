/* Variation A — Stately Ledger (promoted to full-screen main app)
   Wide sidebar with brass-tab section labels, master/detail layout.
   The right column is a ScreenRouter that picks a deep screen by section+item.
*/

const StatelyLedger = ({ fullscreen = false }) => {
  /* Reasonable per-section default landing item */
  const SECTION_DEFAULTS = {
    characters: 'list',
    stories:    'work-series',
    read:       'r-story',
    npcs:       'n-list',
    config:     'c-view',
    model:      'm-switch',
    tools:      't-recent',
  };

  const [activeSection, setActiveSection] = React.useState('read');
  const [activeItem, setActiveItem] = React.useState('r-story');
  const [drawerOpen, setDrawerOpen] = React.useState(true);
  const [activityFull, setActivityFull] = React.useState(false);
  const [ctx, setCtxRaw] = React.useState({ storyIdx: 0, charIdx: 0 });

  /* Cross-screen navigation hook: setCtx({ _jumpTo: { sectionId, itemId, charIdx } }) */
  const setCtx = (next) => {
    if (next && next._jumpTo) {
      const j = next._jumpTo;
      if (j.sectionId) setActiveSection(j.sectionId);
      if (j.itemId)    setActiveItem(j.itemId);
      const clean = { ...next };
      delete clean._jumpTo;
      Object.assign(clean, j);
      setCtxRaw(clean);
    } else {
      setCtxRaw(next);
    }
  };

  const section = MENU_DATA.sections.find(s => s.id === activeSection);
  const item = section?.items.find(i => i.id === activeItem);

  return (
    <div className={`ledger-shell${fullscreen ? ' ledger-fullscreen' : ''}`}>
      {/* Top bar */}
      <header className="ledger-topbar">
        <div className="ledger-brand">
          <span className="brand-mark">DD</span>
          <span className="brand-name">DDCCS</span>
          <span className="brand-sub">Campaign Console</span>
        </div>
        <div className="ledger-top-center">
          <CampaignChip campaigns={MENU_DATA.campaigns} variant="ledger" />
        </div>
        <div className="ledger-top-right">
          <SearchField />
          <button className="topbar-icon-btn" title="Switch model profile"
            onClick={() => { setActiveSection('model'); setActiveItem('m-switch'); }}>
            <Icon name="model" size={15}/>
            <span>Sonnet · Narrative</span>
          </button>
        </div>
      </header>

      <div className="ledger-body">
        {/* Section sidebar — brass ledger tabs */}
        <nav className="ledger-sidebar">
          {MENU_DATA.sections.map(s => (
            <button key={s.id}
              className={`ledger-tab${s.id === activeSection ? ' active' : ''}`}
              onClick={() => { setActiveSection(s.id); setActiveItem(SECTION_DEFAULTS[s.id] || s.items[0].id); }}>
              <span className="ledger-tab-glyph">
                <Icon name={s.icon} size={18}/>
              </span>
              <span className="ledger-tab-text">
                <span className="ledger-tab-label">{s.label}</span>
                <span className="ledger-tab-blurb">{s.blurb}</span>
              </span>
              {s.count != null && <span className="ledger-tab-count">{s.count}</span>}
            </button>
          ))}
          <div className="ledger-sidebar-foot">
            <div className="utility-block">
              <span className="utility-eyebrow">Utility commands</span>
              {MENU_DATA.utilityCommands.map(c => (
                <button key={c.cmd} className="utility-cmd">
                  <code>{c.cmd}</code>
                  <span>{c.label}</span>
                  {c.slow && <SlowTag />}
                </button>
              ))}
            </div>
          </div>
        </nav>

        {/* Single action column with a slim tab header at the top */}
        <section className="ledger-action">
          <div className="action-header">
            <div className="action-header-top">
              <div className="action-header-text">
                <span className="reader-eyebrow">{section.label}</span>
                <h2>{item ? item.label : section.label}</h2>
              </div>
              <span className="action-header-meta">
                {section.items.length} actions
                <span className="dot-sep">·</span>
                {section.items.filter(i => i.ai).length} AI-powered
              </span>
            </div>
            <nav className="action-tabs">
              {section.items.map((it, i) => (
                <button key={it.id}
                  className={`action-tab${it.id === activeItem ? ' active' : ''}${it.deprecated ? ' deprecated' : ''}`}
                  onClick={() => setActiveItem(it.id)}>
                  <span className="tab-num">{String(i + 1).padStart(2, '0')}</span>
                  <span>{it.label}</span>
                  <span className="tab-tags">
                    {it.ai && <AiTag/>}
                    {it.slow && <SlowTag/>}
                    {it.hasSubmenu && <Icon name="chevron" size={10}/>}
                  </span>
                </button>
              ))}
            </nav>
          </div>
          <div className="action-body">
            <ScreenRouter section={section} item={item} ctx={ctx} setCtx={setCtx} />
          </div>
        </section>

        {!activityFull && (
          <ActivityDrawer
            items={MENU_DATA.activityLog}
            open={drawerOpen}
            onToggle={() => setDrawerOpen(!drawerOpen)}
          />
        )}
      </div>

      {/* Floating expand button on the activity drawer */}
      {drawerOpen && !activityFull && (
        <button className="activity-expand-btn" onClick={() => setActivityFull(true)} title="Open activity log full-screen">
          <Icon name="drawer" size={13}/> Expand
        </button>
      )}

      {/* Fullscreen activity view overlay */}
      {activityFull && (
        <div className="activity-overlay">
          <ActivityFullScreen onClose={() => setActivityFull(false)}/>
        </div>
      )}
    </div>
  );
};

window.StatelyLedger = StatelyLedger;
