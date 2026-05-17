/**
 * PlaceholderScreen — visible reminder that a screen is unimplemented.
 *
 * Makes the gap loud and obvious so it cannot be shipped as-is.
 * Replace by porting the relevant JSX from:
 *   _canonical_source/screens-content.jsx  (story / reader screens)
 *   _canonical_source/screens-admin.jsx    (settings / tools / NPCs)
 */

import * as React from 'react';
import type { MenuSection, MenuItem } from '../menuData';
import { Icon, AiTag, SlowTag } from '../atoms';

interface PlaceholderScreenProps {
  section: MenuSection;
  item: MenuItem;
}

export function PlaceholderScreen({ section, item }: PlaceholderScreenProps): React.ReactElement {
  return (
    <div className="screen-generic">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">{section.label}</span>
          <h2>
            {item.label}
            {item.ai && <AiTag label="AI" />}
            {item.slow && <SlowTag />}
          </h2>
          <p className="screen-blurb">
            This screen has not been ported yet. The canonical design lives
            in the design system project — see{' '}
            <code>_canonical_source/screens-content.jsx</code> or{' '}
            <code>_canonical_source/screens-admin.jsx</code> for the JSX to port.
          </p>
        </div>
        <div className="screen-head-actions">
          <button className="ghost-btn" disabled>Cancel</button>
          <button className="primary-btn" disabled>
            {item.ai && <Icon name="sparkle" size={11} />}
            Run
          </button>
        </div>
      </header>

      <div
        style={{
          marginTop: 24, padding: 24, borderRadius: 8,
          background: 'var(--canvas-raised, #3a2918)',
          border: '1px dashed var(--rule, rgba(201,169,110,0.33))',
          textAlign: 'center',
        }}
      >
        <div style={{ fontFamily: 'var(--font-display)', fontSize: 12, color: 'var(--brass-dim, #8a6d3e)', letterSpacing: '0.16em', textTransform: 'uppercase' }}>
          Screen ID
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, color: 'var(--brass, #c9a96e)', marginTop: 4 }}>
          {section.id} / {item.id}
        </div>
        {item.note && (
          <p style={{ marginTop: 12, fontFamily: 'var(--font-body)', fontStyle: 'italic', color: 'var(--ink-dim, #b09070)' }}>
            {item.note}
          </p>
        )}
      </div>
    </div>
  );
}
