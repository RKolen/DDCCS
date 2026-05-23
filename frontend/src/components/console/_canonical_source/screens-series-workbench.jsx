/* ============================================================
   AI action — V1 "WORKBENCH" layout.
   Form sticky on left, streaming canvas on right. Both visible
   simultaneously. Form stays editable during streaming so the
   DM can tweak inputs and re-run.
   ============================================================ */

const AiActionWorkbench = ({ actionId, ctx, setCtx, entry, typewriterSpeed }) => {
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

  const statusClass = run.phase === 'running' ? 'running' : run.phase === 'done' ? 'done' : 'idle';
  const statusLabel = run.phase === 'running' ? 'Streaming' : run.phase === 'done' ? 'Complete' : 'Ready';

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

      <header className="screen-head" style={{ marginBottom: 16, paddingBottom: 12 }}>
        <div>
          <span className="reader-eyebrow">{preset.group} <AiTag label="AI"/></span>
          <h2>{preset.label}{preset.slow && <SlowTag/>}</h2>
          <p className="screen-blurb">{preset.blurb}</p>
        </div>
      </header>

      <div className="ai-workbench">
        {/* LEFT — sticky setup form */}
        <aside className="ai-form-pane">
          <h3><Icon name="gear" size={11}/> Setup</h3>

          {preset.inputs.map(inp => (
            <div key={inp.id} className="ai-form-row">
              <label>{inp.label}</label>
              <AiFormControl input={inp} value={formValues[inp.id]} onChange={v => setField(inp.id, v)}/>
            </div>
          ))}

          <dl className="ai-model-readout">
            <dt>Model</dt><dd>{preset.model.name}</dd>
            <dt>Task</dt><dd><em>{preset.model.task}</em></dd>
            {preset.target && (<><dt>Lands as</dt><dd>{preset.target.kind}</dd></>)}
            {preset.target && (<><dt>Path</dt><dd className="mono">{preset.target.path}</dd></>)}
          </dl>

          <div className="ai-form-foot">
            {run.phase === 'setup' && (
              <button className="ai-run-btn" onClick={run.start}>
                <Icon name="sparkle" size={11}/> Run
              </button>
            )}
            {run.phase === 'running' && (
              <button className="ai-run-btn" onClick={run.cancel} style={{ background: 'linear-gradient(180deg,#b04a3a,#832d23)', borderColor: '#6b1f17', color: '#fff7e8' }}>
                <Icon name="close" size={11}/> Cancel
              </button>
            )}
            {run.phase === 'done' && (
              <button className="ai-run-btn" onClick={run.start}>
                <Icon name="sparkle" size={11}/> Re-run with same inputs
              </button>
            )}
            <p className="ai-form-tip">Edits to inputs above will apply on next run. Result is not saved until you accept it.</p>
          </div>
        </aside>

        {/* RIGHT — status bar + streaming canvas + result foot */}
        <section className="ai-result-pane">
          <div className="ai-result-bar">
            <div className="ai-result-status">
              <span className={`ai-status-dot ${statusClass}`}/>
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
                <span className="glyph"><Icon name="sparkle" size={22}/></span>
                <h4>Ready when you are</h4>
                <p>Fill the form on the left and hit <b>Run</b>. The result will stream in here. Nothing is written to your campaign until you accept it.</p>
              </div>
            ) : (
              <AiStreamBody text={run.streamed} caret={run.phase === 'running'}/>
            )}
          </div>

          {run.phase === 'done' && (
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
          )}
        </section>
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

window.AiActionWorkbench = AiActionWorkbench;
