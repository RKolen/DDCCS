/* ============================================================
   AI action — V2 "FORGE" layout.
   Three sequential phases, each taking the full canvas:
     1. Setup (focused dense form)
     2. Stream (large console + side meter)
     3. Artifact (clean reader view with accept/discard)
   ============================================================ */

const AiActionForge = ({ actionId, ctx, setCtx, entry, typewriterSpeed }) => {
  const preset = ACTION_PRESETS[actionId];
  const [formValues, setFormValues] = React.useState({});
  const [toast, setToast] = React.useState(null);
  const run = useAiRun(actionId, { speed: typewriterSpeed });

  if (!preset) return <div className="screen-blurb">Unknown action: {actionId}</div>;

  const setField = (id, v) => setFormValues(o => ({ ...o, [id]: v }));
  const goBack = () => setCtx({ ...ctx, _jumpTo: { sectionId: 'stories', itemId: 'work-series' } });

  const onAccept = () => {
    setToast({ tag: 'Saved to Drupal', path: preset.target?.path || 'campaigns/whispers/' });
    setTimeout(() => setToast(null), 4200);
  };

  // Stepper state
  const stepClass = (id) => {
    if (run.phase === 'setup') return id === 'setup' ? 'is-active' : '';
    if (run.phase === 'running') {
      if (id === 'setup') return 'is-done';
      if (id === 'stream') return 'is-active';
      return '';
    }
    // done
    if (id === 'setup') return 'is-done';
    if (id === 'stream') return 'is-done';
    return 'is-active';
  };

  return (
    <div className="screen-aiaction">
      <div className="action-back-row">
        <button className="action-back" onClick={goBack}>
          <Icon name="chevronLeft" size={11}/> Back to series workspace
        </button>
        <span className="action-entry-pip">
          <span className="dot"/>
          Opened from {entry === 'session' ? 'Session Reader · End of chronicle' : 'Series workspace'}
        </span>
      </div>

      <header className="screen-head" style={{ marginBottom: 12, paddingBottom: 10 }}>
        <div>
          <span className="reader-eyebrow">{preset.group} <AiTag label="AI"/></span>
          <h2>{preset.label}{preset.slow && <SlowTag/>}</h2>
          <p className="screen-blurb">{preset.blurb}</p>
        </div>
      </header>

      <div className="ai-forge">
        {/* Stepper */}
        <div className="forge-stepper">
          <div className={`forge-step ${stepClass('setup')}`}><span className="num">1</span> Setup</div>
          <div className="step-rule"/>
          <div className={`forge-step ${stepClass('stream')}`}><span className="num">2</span> Generate</div>
          <div className="step-rule"/>
          <div className={`forge-step ${stepClass('result')}`}><span className="num">3</span> Review &amp; accept</div>
        </div>

        <div className="forge-canvas">
          {/* PHASE 1 — SETUP */}
          {run.phase === 'setup' && (
            <div className="forge-setup">
              <span className="reader-eyebrow">Step 1 · {preset.group}</span>
              <h3>{preset.label}</h3>
              <p className="forge-blurb">{preset.blurb}</p>

              {preset.inputs.map(inp => (
                <div key={inp.id} className="ai-form-row">
                  <label>{inp.label}</label>
                  <AiFormControl input={inp} value={formValues[inp.id]} onChange={v => setField(inp.id, v)}/>
                </div>
              ))}

              <dl className="ai-model-readout" style={{ marginTop: 8 }}>
                <dt>Model</dt><dd>{preset.model.name}</dd>
                <dt>Task</dt><dd><em>{preset.model.task}</em></dd>
                {preset.target && (<><dt>Lands as</dt><dd>{preset.target.kind} · <span className="mono">{preset.target.path}</span></dd></>)}
              </dl>

              <div className="forge-launch">
                <p className="ai-form-tip" style={{ margin: 0 }}>The model is chosen automatically by task. Result is not saved until you accept it.</p>
                <button className="ai-run-btn" onClick={run.start}>
                  <Icon name="sparkle" size={12}/> Forge
                </button>
              </div>
            </div>
          )}

          {/* PHASE 2 — STREAM */}
          {run.phase === 'running' && (
            <div className="forge-stream">
              <div className="forge-stream-body">
                <AiStreamBody text={run.streamed} caret/>
              </div>
              <aside className="forge-meter">
                <h4>Live</h4>
                <div className="meter-row">
                  <span className="meter-label">Progress</span>
                  <div className="meter-progress"><span className="meter-progress-fill" style={{ width: `${Math.round(run.progress * 100)}%` }}/></div>
                  <span className="meter-sub">{Math.round(run.progress * 100)}% · {run.elapsed.toFixed(1)}s elapsed</span>
                </div>
                <div className="meter-row">
                  <span className="meter-label">Tokens</span>
                  <span className="meter-val">{run.tokens.toLocaleString()}</span>
                  <span className="meter-sub">{run.tokensPerSec}/s · ~{Math.max(1, Math.round((preset.duration/1000 - run.elapsed)))}s left</span>
                </div>
                <div className="meter-row">
                  <span className="meter-label">Model</span>
                  <span className="meter-sub" style={{ color: 'var(--brass-bright)', fontSize: 12 }}>{preset.model.name}</span>
                  <span className="meter-sub">task: <em>{preset.model.task}</em></span>
                </div>
                <h4 style={{ marginTop: 6 }}>Events</h4>
                <ul className="meter-events">
                  {run.events.length === 0 && <li style={{ fontStyle: 'italic' }}><span className="t">—</span> waiting on first token…</li>}
                  {run.events.map((ev, i) => (
                    <li key={i}><span className="t">{ev.t}</span>{ev.msg}</li>
                  ))}
                </ul>
                <button className="meter-cancel" onClick={run.cancel}>Cancel run</button>
              </aside>
            </div>
          )}

          {/* PHASE 3 — ARTIFACT */}
          {run.phase === 'done' && (
            <div className="forge-artifact">
              <header className="forge-artifact-head">
                <div>
                  <span className="reader-eyebrow">Step 3 · Ready to review</span>
                  <h3>{preset.label}</h3>
                  <div className="forge-artifact-meta">
                    <span><b>{run.tokens.toLocaleString()}</b> tokens</span>
                    <span><b>{run.elapsed.toFixed(1)}s</b> elapsed</span>
                    <span>model · <b>{preset.model.name}</b></span>
                    {preset.target && <span>target · <b>{preset.target.kind}</b></span>}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <button className="ghost-btn ghost-small" onClick={run.reset}>Edit inputs</button>
                </div>
              </header>
              <div className="forge-artifact-body">
                <AiStreamBody text={run.streamed} caret={false}/>
              </div>
              <div className="ai-result-foot">
                <div className="ai-result-foot-left">
                  <span className="ai-result-foot-target">
                    {preset.target ? <>Will save as <b>{preset.target.kind}</b> · <span className="mono">{preset.target.path}</span></> : 'Consult-only — not saved to Drupal'}
                  </span>
                  <span className="ai-result-foot-hint">{preset.target ? 'Discard to throw it away. Accept to push to Drupal and add to the chronicle.' : 'You can copy this into your notes.'}</span>
                </div>
                <div className="ai-result-foot-right">
                  <button className="ghost-btn" onClick={run.reset}>Discard</button>
                  <button className="ghost-btn" onClick={run.start}><Icon name="sparkle" size={11}/> Regenerate</button>
                  {preset.target && (
                    <button className="ai-accept-btn" onClick={onAccept}>
                      <Icon name="plus" size={11}/> Accept &amp; save
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {toast && (
        <div className="ai-toast">
          <span className="toast-tag">✓ {toast.tag}</span>
          <span className="toast-path">{toast.path}</span>
        </div>
      )}
    </div>
  );
};

/* Top-level dispatcher — chooses variation based on tweak. */
const AiActionScreen = ({ actionId, ctx, setCtx }) => {
  const variant = (window.__tweaks && window.__tweaks.aiLayout) || 'workbench';
  const typewriterSpeed = (window.__tweaks && window.__tweaks.typewriter) || 1;
  const entry = ctx?._entryFrom || 'workspace';
  if (variant === 'forge') {
    return <AiActionForge actionId={actionId} ctx={ctx} setCtx={setCtx} entry={entry} typewriterSpeed={typewriterSpeed}/>;
  }
  return <AiActionWorkbench actionId={actionId} ctx={ctx} setCtx={setCtx} entry={entry} typewriterSpeed={typewriterSpeed}/>;
};

window.AiActionForge = AiActionForge;
window.AiActionScreen = AiActionScreen;
