/* ============================================================
   AI action screen — shared chrome, dispatches to V1/V2.
   ============================================================ */

/* Small helpers used by both variations */

const AiFormControl = ({ input, value, onChange }) => {
  if (input.kind === 'select') {
    return (
      <select value={value ?? input.options[0]} onChange={e => onChange(e.target.value)}>
        {input.options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    );
  }
  if (input.kind === 'textarea') {
    return (
      <textarea
        rows={input.rows || 4}
        placeholder={input.placeholder}
        value={value ?? ''}
        onChange={e => onChange(e.target.value)}
      />
    );
  }
  if (input.kind === 'segment') {
    return (
      <div className="seg-control">
        {input.options.map(o => (
          <button key={o}
            type="button"
            className={`seg${(value ?? input.default ?? input.options[0]) === o ? ' active' : ''}`}
            onClick={() => onChange(o)}>{o}</button>
        ))}
      </div>
    );
  }
  return <input type="text" value={value ?? ''} onChange={e => onChange(e.target.value)} placeholder={input.placeholder} />;
};

/* Format a streaming string into <p>/<h3> blocks, with caret while running. */
const AiStreamBody = ({ text, caret }) => {
  // Split on blank lines, then render markdown-ish.
  const blocks = text.split(/\n{2,}/).filter(Boolean);
  const renderInline = (s) => {
    // Markdown bold/italic/code → spans. Done in passes.
    const parts = [];
    let i = 0;
    const push = (frag) => parts.push(frag);
    const re = /\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`/g;
    let m, last = 0;
    while ((m = re.exec(s)) !== null) {
      if (m.index > last) push(s.slice(last, m.index));
      if (m[1]) push(<strong key={parts.length}>{m[1]}</strong>);
      else if (m[2]) push(<em key={parts.length}>{m[2]}</em>);
      else if (m[3]) push(<span key={parts.length} className="ai-mono">{m[3]}</span>);
      last = re.lastIndex;
    }
    if (last < s.length) push(s.slice(last));
    return parts;
  };
  return (
    <div className="ai-stream">
      {blocks.map((blk, i) => {
        const isLast = i === blocks.length - 1;
        if (blk.startsWith('### ')) return <h3 key={i}>{renderInline(blk.slice(4))}{caret && isLast && <span className="caret"/>}</h3>;
        if (blk.startsWith('#### ')) return <h3 key={i} style={{ fontSize: 12 }}>{renderInline(blk.slice(5))}{caret && isLast && <span className="caret"/>}</h3>;
        return <p key={i}>{renderInline(blk)}{caret && isLast && <span className="caret"/>}</p>;
      })}
    </div>
  );
};

window.AiFormControl = AiFormControl;
window.AiStreamBody = AiStreamBody;
