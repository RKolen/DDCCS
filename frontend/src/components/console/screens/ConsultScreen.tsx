/**
 * ConsultScreen — `characters / consult`.
 *
 * Character selector from ConsoleContext. No mock names.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { useConsoleData, playerCharacters } from '../ConsoleContext';
import { Icon, AiTag } from '../atoms';

function charLabel(c: ReturnType<typeof playerCharacters>[number]): string {
  if (c.sourceCharacter === true)  return `${c.title} · Source`;
  if (c.campaign != null)          return `${c.title} · ${c.campaign}`;
  return c.title;
}

export function ConsultScreen({ ctx, setCtx }: ScreenProps): React.ReactElement {
  const data = useConsoleData();
  const pcs  = playerCharacters(data);
  const idx  = ctx.charIdx ?? 0;
  const char = pcs[idx] ?? null;

  if (pcs.length === 0) {
    return (
      <div className="screen-consult">
        <header className="screen-head">
          <div>
            <span className="reader-eyebrow">Character consultation <AiTag label="AI" /></span>
            <h2>No characters</h2>
            <p className="screen-blurb">
              No player characters in Drupal. Add Character nodes with Character Type set to on.
            </p>
          </div>
        </header>
      </div>
    );
  }

  return (
    <div className="screen-consult">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Character consultation <AiTag label="AI" /></span>
          <h2>{char?.title ?? 'Select character'}</h2>
          <p className="screen-blurb">
            Speaks in character. Draws on profile, arc state, and recent story appearances.
          </p>
        </div>
        {pcs.length > 1 && (
          <div className="screen-head-actions">
            <select
              className="console-select"
              value={idx}
              onChange={e => setCtx({ ...ctx, charIdx: Number(e.target.value) })}
            >
              {pcs.map((c, i) => <option key={c.id} value={i}>{charLabel(c)}</option>)}
            </select>
          </div>
        )}
      </header>

      {char && (
        <div className="consult-pane">
          <div className="consult-thread">
            <div className="consult-bubble role-char">
              <span className="bubble-tag">{charLabel(char)} <AiTag /></span>
              <p style={{ fontStyle: 'italic', color: 'var(--ink-dim)' }}>
                Connect the Python AI backend to enable live character consultations.
              </p>
            </div>
          </div>
          <div className="consult-input">
            <textarea placeholder={`Ask ${char.title.split(' ')[0]}...`} rows={2} />
            <button className="primary-btn">
              <Icon name="sparkle" size={11} /> Ask
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
