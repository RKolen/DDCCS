/**
 * DeprecatedScreen — shown for deprecated menu items (e.g., `characters/ascii`).
 *
 * Port of `DeprecatedScreen` from screens-router.jsx.
 */

import * as React from 'react';
import type { MenuItem } from '../menuData';

interface DeprecatedScreenProps {
  item: MenuItem;
}

export function DeprecatedScreen({ item }: DeprecatedScreenProps): React.ReactElement {
  return (
    <div className="screen-deprecated">
      <div className="deprecated-card">
        <span className="deprecated-eyebrow">Deprecated</span>
        <h2>{item.label}</h2>
        <p>{item.note ?? 'This command is no longer supported.'}</p>
        <p>
          Character portraits are now produced through the <strong>ComfyUI image pipeline</strong>,
          attached automatically to each character profile. To generate or regenerate a portrait,
          open the character details and use <em>Generate image</em>.
        </p>
      </div>
    </div>
  );
}
