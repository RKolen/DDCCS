/* DDCCS arc-screens — shared atoms */
/* global React */

const ArcSparkle = ({ size = 9 }) => (
  <svg viewBox="0 0 16 16" width={size} height={size}
       style={{ flexShrink: 0 }}>
    <g stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round">
      <path d="M8 2v4M8 10v4M2 8h4M10 8h4M4.5 4.5l2.5 2.5M9 9l2.5 2.5M4.5 11.5l2.5-2.5M9 7l2.5-2.5"/>
    </g>
  </svg>
);

const ArcAiPill = ({ label = 'AI', size = 9 }) => (
  <span className="arc-ai-pill"><ArcSparkle size={size}/>{label}</span>
);

const ArcGlyph = ({ name, size = 12 }) => {
  const s = { stroke: 'currentColor', strokeWidth: 1.5, fill: 'none',
              strokeLinecap: 'round', strokeLinejoin: 'round' };
  const paths = {
    book:    <g {...s}><path d="M3 3h6c1 0 2 .8 2 2v9H5c-1 0-2-.8-2-2z"/><path d="M3 12c0-1 .8-2 2-2h6"/></g>,
    char:    <g {...s}><circle cx="8" cy="6" r="3"/><path d="M2.5 14c.8-3 2.9-4.5 5.5-4.5s4.7 1.5 5.5 4.5"/></g>,
    plus:    <g {...s}><path d="M8 3v10M3 8h10"/></g>,
    close:   <g {...s}><path d="M4 4l8 8M12 4l-8 8"/></g>,
    search:  <g {...s}><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5L14 14"/></g>,
    refresh: <g {...s}><path d="M14 8a6 6 0 11-2-4.5"/><path d="M14 2v3.5h-3.5"/></g>,
    check:   <g {...s}><path d="M3 8.5l3.5 3.5L13 5"/></g>,
    download:<g {...s}><path d="M8 2v9M4 8l4 4 4-4M3 14h10"/></g>,
    edit:    <g {...s}><path d="M3 13l1-4 6-6 3 3-6 6z"/><path d="M9 4l3 3"/></g>,
    arrow:   <g {...s}><path d="M3 8h10M9 4l4 4-4 4"/></g>,
    file:    <g {...s}><path d="M4 2h5l3 3v9H4z"/><path d="M9 2v3h3"/></g>,
    folder:  <g {...s}><path d="M2 4h4l2 2h6v7H2z"/></g>,
    history: <g {...s}><path d="M8 3v5l3 2"/><circle cx="8" cy="8" r="6"/></g>,
    play:    <g {...s} fill="currentColor"><path d="M4 3l9 5-9 5z"/></g>,
    eye:     <g {...s}><path d="M1.5 8s2.5-5 6.5-5 6.5 5 6.5 5-2.5 5-6.5 5-6.5-5-6.5-5z"/><circle cx="8" cy="8" r="2"/></g>,
  };
  return (
    <svg viewBox="0 0 16 16" width={size} height={size} style={{ flexShrink: 0 }}>
      {paths[name] || null}
    </svg>
  );
};

/* Direction badge — color-coded per ArcDirection enum */
const DIR_LABELS = {
  growth: { label: 'Growth', arrow: '↗' },
  decline: { label: 'Decline', arrow: '↘' },
  stasis: { label: 'Stasis', arrow: '→' },
  fluctuation: { label: 'Flux', arrow: '↕' },
  transformation: { label: 'Transformation', arrow: '⇧' },
};
const ArcDirBadge = ({ direction = 'stasis' }) => {
  const { label, arrow } = DIR_LABELS[direction] || DIR_LABELS.stasis;
  return (
    <span className={`arc-dir ${direction}`}>
      <span className="arrow">{arrow}</span>
      {label}
    </span>
  );
};

/* 7-stage track */
const STAGES = ['introduction', 'establishment', 'challenge', 'development',
                'climax', 'resolution', 'aftermath'];
const ArcStageTrack = ({ stage = 'introduction', withLabel = true }) => {
  const idx = STAGES.indexOf(stage);
  return (
    <span className="arc-stage" title={stage}>
      {STAGES.map((s, i) => (
        <React.Fragment key={s}>
          <span className={`pip ${i < idx ? 'done' : i === idx ? 'current' : ''}`}/>
          {i < STAGES.length - 1 && (
            <span className={`pip-bar ${i < idx ? 'done' : ''}`}/>
          )}
        </React.Fragment>
      ))}
      {withLabel && <span className="arc-stage-label">{stage}</span>}
    </span>
  );
};

/* Sparkline — pass series (0..1 normalized array), direction colors it */
const ArcSpark = ({ series, direction = 'stasis', width = 80, height = 24 }) => {
  if (!series || series.length < 2) {
    return <svg className={`arc-spark ${direction}`} width={width} height={height}/>;
  }
  const min = Math.min(...series);
  const max = Math.max(...series);
  const range = Math.max(max - min, 0.05);
  const pad = 3;
  const w = width - pad * 2;
  const h = height - pad * 2;
  const pts = series.map((v, i) => {
    const x = pad + (series.length === 1 ? 0 : (i * w) / (series.length - 1));
    const y = pad + h - ((v - min) / range) * h;
    return [x, y];
  });
  const linePath = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ');
  const areaPath = `${linePath} L ${pts[pts.length - 1][0].toFixed(1)} ${height - pad} L ${pts[0][0].toFixed(1)} ${height - pad} Z`;
  const last = pts[pts.length - 1];
  return (
    <svg className={`arc-spark ${direction}`} width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <path className="area" d={areaPath}/>
      <path className="line" d={linePath}/>
      <circle className="end-dot" cx={last[0]} cy={last[1]} r={2}/>
    </svg>
  );
};

/* Portrait — color block w/ initials */
const ArcPortrait = ({ char, size = 'md' }) => {
  const cls = `arc-portrait ${size === 'lg' ? 'lg' : size === 'sm' ? 'sm' : size === 'xs' ? 'xs' : ''}`;
  const initials = (char.first_name || char.name).slice(0, 2).toUpperCase();
  return (
    <div className={cls} style={{ background: char.portrait || 'var(--color-bg-overlay)' }}>
      {initials}
    </div>
  );
};

/* Console chrome with characters/arc submenu */
const ArcChrome = ({ activeItem = 'arc-summary', children }) => {
  const sections = [
    { id: 'characters', glyph: 'C', label: 'Characters', blurb: 'Profiles, arcs', count: 8, active: true, expand: true },
    { id: 'stories',    glyph: 'S', label: 'Stories',    blurb: 'Sessions, series', count: 22 },
    { id: 'read',       glyph: 'R', label: 'Read',       blurb: 'Player view',     count: 22 },
    { id: 'npcs',       glyph: 'N', label: 'NPCs',       blurb: 'Major figures',   count: 14 },
    { id: 'config',     glyph: 'Σ', label: 'Settings',   blurb: 'AI · RAG · paths' },
    { id: 'tools',      glyph: 'T', label: 'Tools',      blurb: 'History · batch' },
  ];
  const charSubs = [
    { id: 'list',         label: 'List Characters' },
    { id: 'view',         label: 'View Details' },
    { id: 'edit',         label: 'Edit Profile' },
    { id: 'consult',      label: 'Consult',         ai: true },
    { id: 'verify',       label: 'Verify Profile' },
    { id: 'arc',          label: 'Arc Analysis',    ai: true, expand: true },
    { id: 'arc-summary',  label: 'View summary',          sub: true },
    { id: 'arc-analyze',  label: 'Analyze for arc', ai: true, sub: true },
    { id: 'arc-overview', label: 'Campaign overview',     sub: true },
    { id: 'arc-export',   label: 'Export report',         sub: true },
    { id: 'template',     label: 'From template' },
  ];

  return (
    <div className="arc-art">
      <div className="arc-chrome">
        <div className="arc-topbar">
          <div className="arc-brand">
            <span className="arc-brand-mark">DD</span>
            <span className="arc-brand-name">DDCCS</span>
          </div>
          <span className="sep">/</span>
          <span className="ctx">
            Characters · <em>Arc Analysis</em>
          </span>
          <span className="arc-topbar-spacer"/>
          <span className="arc-campaign-chip">
            <span className="pin"/>
            <span className="name">The Fellowship — Eastern March</span>
            <span className="meta">22 · 8</span>
          </span>
          <span className="arc-search">
            <ArcGlyph name="search" size={12}/>
            <span>Search</span>
            <kbd>⌘K</kbd>
          </span>
          <button className="arc-model-btn">Sonnet 4.5</button>
        </div>

        <aside className="arc-sidebar">
          {sections.map(s => (
            <React.Fragment key={s.id}>
              <div className={`arc-tab${s.active ? ' active' : ''}`}>
                <span className="glyph">{s.glyph}</span>
                <span className="label">
                  <strong>{s.label}</strong>
                  <span>{s.blurb}</span>
                </span>
                {s.count != null && <span className="count">{s.count}</span>}
              </div>
              {s.expand && (
                <div className="arc-submenu">
                  {charSubs.map(it => (
                    <div key={it.id}
                         style={it.sub ? { paddingLeft: 24, fontSize: 11.5 } : null}
                         className={`sub${it.id === activeItem ? ' active' : ''}`}>
                      <span>{it.label}</span>
                      {it.ai && <span className="ai"/>}
                    </div>
                  ))}
                </div>
              )}
            </React.Fragment>
          ))}
        </aside>

        <main className="arc-action">{children}</main>
      </div>
    </div>
  );
};

Object.assign(window, {
  ArcSparkle, ArcAiPill, ArcGlyph, ArcDirBadge, ArcStageTrack, ArcSpark,
  ArcPortrait, ArcChrome, STAGES, DIR_LABELS,
});
