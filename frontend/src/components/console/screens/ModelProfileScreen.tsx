/**
 * ModelProfileScreen — `model/m-switch`.
 *
 * Available models come from GATSBY_AI_MODELS (comma-separated model IDs).
 * The active model comes from GATSBY_AI_MODEL.
 * Clicking a card updates ctx.modelId for the session.
 *
 * Example .env.development:
 *
 * Port of `ModelProfileScreen` from screens-admin.jsx.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';

const envActiveModel = process.env.GATSBY_AI_MODEL ?? '';
const envModelsRaw = process.env.GATSBY_AI_MODELS ?? '';

function parseModels(raw: string): string[] {
  return raw.split(',').map(s => s.trim()).filter(Boolean);
}

export function ModelProfileScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const availableModels = parseModels(envModelsRaw);
  const sessionActive = ctx.modelId as string | undefined;
  const activeId = sessionActive ?? envActiveModel;

  if (availableModels.length === 0) {
    return (
      <div className="screen-models">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Model profile</span>
            <h2>No models configured</h2>
            <p className="screen-blurb">
              Set <code>GATSBY_AI_MODELS</code> (comma-separated) and <code>GATSBY_AI_MODEL</code> in .env.development.
            </p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="screen-models">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Model profile</span>
          <h2>Active LLM for this session</h2>
          <p className="screen-blurb">
            {activeId
              ? <>Active: <code>{activeId}</code> — set <code>GATSBY_AI_MODEL</code> to change the default.</>
              : <>Set <code>GATSBY_AI_MODEL</code> in .env.development to configure the default.</>}
          </p>
        </div>
      </header>

      <ul className="model-list">
        {availableModels.map(modelId => (
          <li key={modelId}>
            <button
              type="button"
              className={`model-card${modelId === activeId ? ' active' : ''}`}
              onClick={() => setCtx({ ...ctx, modelId })}
            >
              <div className="model-card-head">
                <h4>{modelId}</h4>
                <div className="model-card-tags">
                  <code className="model-tag">{modelId}</code>
                </div>
              </div>
              <div className="model-card-foot">
                {modelId === activeId
                  ? <span className="active-badge">Active</span>
                  : <span className="muted-tag">Click to activate</span>
                }
              </div>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
