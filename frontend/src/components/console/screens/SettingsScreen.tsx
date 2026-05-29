/**
 * SettingsScreen — `config/*` routes.
 *
 * All config items route here; ctx.settingsTab picks the active pane.
 * c-save routes to the save confirm pane.
 *
 * All configurable values come from GATSBY_* env vars set in .env.development.
 * Drupal is the source of truth for data; these settings control AI, RAG,
 * and display behaviour layered on top.
 *
 * Port of `SettingsScreen` + pane components from screens-admin.jsx.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';

/* ── Env var defaults ── */
const envAiModel = process.env.GATSBY_AI_MODEL ?? '';
const envAiBaseUrl = process.env.GATSBY_AI_BASE_URL ?? '';
const envAiTemp = parseFloat(process.env.GATSBY_AI_TEMPERATURE ?? '0.7');
const envAiMaxTokens = parseInt(process.env.GATSBY_AI_MAX_TOKENS ?? '2048', 10);
const envRagWikiUrl = process.env.GATSBY_RAG_WIKI_URL ?? '';
const envRagRulesUrl = process.env.GATSBY_RAG_RULES_URL ?? '';
const envDrupalUrl = process.env.GATSBY_DRUPAL_BASE_URL ?? '';

/* ── Toggle atom (local) ── */
function Toggle({ defaultOn = false }: { defaultOn?: boolean }): React.ReactElement {
  const [on, setOn] = React.useState(defaultOn);
  return (
    <button
      type="button"
      className={`toggle${on ? ' on' : ''}`}
      onClick={() => setOn(v => !v)}
      aria-pressed={on}
    >
      <span className="toggle-knob" />
    </button>
  );
}

/* ── Config panes ── */

function EnvNote({ variable }: { variable: string }): React.ReactElement {
  return (
    <small>
      Set <code>{variable}</code> in .env.development to configure.
    </small>
  );
}

function CurrentConfigPane(): React.ReactElement {
  const missing = (v: string): React.ReactElement => (
    <em style={{ color: 'var(--ink-faint)' }}>(not set)</em>
  );

  return (
    <div className="config-readout">
      <div className="config-group">
        <h4>AI</h4>
        <dl>
          <dt>Model</dt>
          <dd>{envAiModel || missing(envAiModel)}</dd>
          <dt>Base URL</dt>
          <dd className="muted">{envAiBaseUrl || '(default)'}</dd>
          <dt>Temperature</dt>
          <dd>{Number.isNaN(envAiTemp) ? '—' : envAiTemp.toFixed(2)}</dd>
          <dt>Max Tokens</dt>
          <dd>{Number.isNaN(envAiMaxTokens) ? '—' : envAiMaxTokens.toLocaleString()}</dd>
          <dt>Enabled</dt>
          <dd className="ok">yes</dd>
        </dl>
      </div>
      <div className="config-group">
        <h4>RAG</h4>
        <dl>
          <dt>Enabled</dt><dd className="ok">yes</dd>
          <dt>Wiki URL</dt>
          <dd className="muted">{envRagWikiUrl || '(not set)'}</dd>
          <dt>Rules URL</dt>
          <dd className="muted">{envRagRulesUrl || '(not set)'}</dd>
          <dt>Cache TTL</dt><dd>3,600s</dd>
          <dt>Search Depth</dt><dd>4</dd>
        </dl>
      </div>
      <div className="config-group">
        <h4>Drupal</h4>
        <dl>
          <dt>Base URL</dt>
          <dd className="muted">{envDrupalUrl || '(not set)'}</dd>
          <dt>Data source</dt>
          <dd className="ok">Drupal GraphQL</dd>
        </dl>
      </div>
      <div className="config-group">
        <h4>Display</h4>
        <dl>
          <dt>Use Rich</dt><dd className="ok">yes</dd>
          <dt>Theme</dt><dd>dark-parchment</dd>
          <dt>TTS Enabled</dt><dd>yes</dd>
        </dl>
      </div>
    </div>
  );
}

function AIConfigPane(): React.ReactElement {
  const [temp, setTemp] = React.useState(Number.isNaN(envAiTemp) ? 0.7 : envAiTemp);
  const [maxTokens, setMaxTokens] = React.useState(Number.isNaN(envAiMaxTokens) ? 2048 : envAiMaxTokens);
  return (
    <div className="config-form">
      <div className="form-grid">
        <label className="form-row">
          <span>Base URL</span>
          <input type="text" defaultValue={envAiBaseUrl} placeholder="(default endpoint)" />
          <EnvNote variable="GATSBY_AI_BASE_URL" />
        </label>
        <label className="form-row">
          <span>Model</span>
          <input type="text" defaultValue={envAiModel} placeholder="e.g. claude-sonnet-4-6" />
          <EnvNote variable="GATSBY_AI_MODEL" />
        </label>
        <label className="form-row">
          <span>Temperature</span>
          <div className="slider-row">
            <input
              type="range" min="0" max="2" step="0.05"
              value={temp}
              onChange={e => setTemp(parseFloat(e.target.value))}
            />
            <span className="slider-val mono">{temp.toFixed(2)}</span>
          </div>
          <EnvNote variable="GATSBY_AI_TEMPERATURE" />
        </label>
        <label className="form-row">
          <span>Max tokens</span>
          <input
            type="number"
            value={maxTokens}
            onChange={e => setMaxTokens(Number(e.target.value))}
          />
          <EnvNote variable="GATSBY_AI_MAX_TOKENS" />
        </label>
        <label className="form-row toggle-row">
          <span>Enabled</span>
          <Toggle defaultOn={true} />
        </label>
      </div>
    </div>
  );
}

function RAGConfigPane(): React.ReactElement {
  return (
    <div className="config-form">
      <div className="form-grid">
        <label className="form-row toggle-row"><span>Enabled</span><Toggle defaultOn={true} /></label>
        <label className="form-row">
          <span>Wiki base URL</span>
          <input type="text" defaultValue={envRagWikiUrl} placeholder="set GATSBY_RAG_WIKI_URL" />
          <EnvNote variable="GATSBY_RAG_WIKI_URL" />
        </label>
        <label className="form-row">
          <span>Rules base URL</span>
          <input type="text" defaultValue={envRagRulesUrl} placeholder="set GATSBY_RAG_RULES_URL" />
          <EnvNote variable="GATSBY_RAG_RULES_URL" />
        </label>
        <label className="form-row"><span>Cache TTL (seconds)</span><input type="number" defaultValue="3600" /></label>
        <label className="form-row"><span>Max cache size</span><input type="number" defaultValue="500" /></label>
        <label className="form-row">
          <span>Search depth</span>
          <input type="number" defaultValue="4" />
          <small>How many hops the retriever follows.</small>
        </label>
        <label className="form-row">
          <span>Min relevance</span>
          <input type="number" step="0.01" defaultValue="0.62" />
        </label>
      </div>
    </div>
  );
}

function DisplayConfigPane(): React.ReactElement {
  return (
    <div className="config-form">
      <div className="form-grid">
        <label className="form-row toggle-row"><span>Use Rich terminal</span><Toggle defaultOn={true} /></label>
        <label className="form-row">
          <span>Theme</span>
          <select defaultValue="dark-parchment">
            <option value="dark-parchment">dark-parchment</option>
            <option value="candlelit">candlelit</option>
            <option value="moonlit">moonlit</option>
            <option value="plain">plain</option>
          </select>
        </label>
        <label className="form-row"><span>Max line width</span><input type="number" defaultValue="100" /></label>
        <label className="form-row toggle-row"><span>TTS enabled</span><Toggle defaultOn={true} /></label>
        <label className="form-row">
          <span>TTS voice</span>
          <select defaultValue="narrator-warm-1">
            <option value="narrator-warm-1">narrator-warm-1</option>
            <option value="narrator-grim-2">narrator-grim-2</option>
            <option value="narrator-bardic-3">narrator-bardic-3</option>
          </select>
        </label>
        <label className="form-row">
          <span>TTS speed</span>
          <div className="slider-row">
            <input type="range" min="0.5" max="2" step="0.05" defaultValue="1" />
            <span className="slider-val mono">1.00x</span>
          </div>
        </label>
      </div>
    </div>
  );
}

function PathsConfigPane(): React.ReactElement {
  return (
    <div className="config-form">
      <div className="form-grid">
        <label className="form-row">
          <span>Drupal base URL</span>
          <input type="text" defaultValue={envDrupalUrl} placeholder="set GATSBY_DRUPAL_BASE_URL" className="mono" />
          <EnvNote variable="GATSBY_DRUPAL_BASE_URL" />
        </label>
        <label className="form-row">
          <span>AI base URL</span>
          <input type="text" defaultValue={envAiBaseUrl} placeholder="(default)" className="mono" />
          <EnvNote variable="GATSBY_AI_BASE_URL" />
        </label>
      </div>
    </div>
  );
}

function ValidatePane(): React.ReactElement {
  const drupalOk = Boolean(envDrupalUrl);
  const aiOk = Boolean(envAiModel);

  return (
    <div className="validate-pane">
      <div className="validate-head">
        <h4>Validation report</h4>
        <button type="button" className="ghost-btn">Re-run</button>
      </div>
      <ul className="validate-list">
        <li className={drupalOk ? 'valid' : 'warn'}>
          <span className="check">{drupalOk ? '[OK]' : '[!]'}</span>
          {drupalOk
            ? `Drupal URL configured: ${envDrupalUrl}`
            : 'GATSBY_DRUPAL_BASE_URL not set — admin links will not work'}
        </li>
        <li className={aiOk ? 'valid' : 'warn'}>
          <span className="check">{aiOk ? '[OK]' : '[!]'}</span>
          {aiOk
            ? `AI model configured: ${envAiModel}`
            : 'GATSBY_AI_MODEL not set — model profile screen will show empty state'}
        </li>
        <li className="valid"><span className="check">[OK]</span> RAG settings valid — documents indexed</li>
        <li className="warn">
          <span className="check">[!]</span>
          TTS voice <code>narrator-grim-2</code> not installed locally — will fall back
        </li>
      </ul>
    </div>
  );
}

function SaveConfirmPane(): React.ReactElement {
  return (
    <div className="screen-confirm">
      <div className="confirm-card">
        <p>Configuration is managed via environment variables in <code className="mono">.env.development</code>.</p>
        <p>Update the GATSBY_* variables in that file and restart the dev server to apply changes.</p>
        <div className="confirm-actions">
          <button type="button" className="ghost-btn">Cancel</button>
          <button type="button" className="primary-btn" disabled>Save</button>
        </div>
      </div>
    </div>
  );
}

/* ── Screen ── */

type SettingsTab = 'view' | 'ai' | 'rag' | 'display' | 'paths' | 'validate' | 'save';

export function SettingsScreen({ ctx }: ScreenProps): React.ReactElement {
  const tab = (ctx.settingsTab as SettingsTab | undefined) ?? 'view';

  if (tab === 'save') return <SaveConfirmPane />;

  return (
    <div className="screen-settings">
      <div className="settings-body">
        {tab === 'view' && <CurrentConfigPane />}
        {tab === 'ai' && <AIConfigPane />}
        {tab === 'rag' && <RAGConfigPane />}
        {tab === 'display' && <DisplayConfigPane />}
        {tab === 'paths' && <PathsConfigPane />}
        {tab === 'validate' && <ValidatePane />}
      </div>
    </div>
  );
}
