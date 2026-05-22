/**
 * SpellRegistryScreen — `stories/spells`.
 *
 * Spells are stored as `node--spell` content in Drupal.
 * This screen renders a table once spells are in ConsoleData.
 * Currently shows an empty state pointing to the data path.
 *
 * Port of `SpellRegistryScreen` from screens-router.jsx.
 */

import * as React from 'react';
import type { ScreenProps } from '../ScreenRouter';
import { Icon } from '../atoms';

export function SpellRegistryScreen({ ctx }: ScreenProps): React.ReactElement {
  const campaignName = ctx.activeCampaignName as string | null | undefined;

  return (
    <div className="screen-spells">
      <header className="screen-head">
        <div>
          <span className="reader-eyebrow">Spell registry</span>
          <h2>{campaignName ? `${campaignName} — Spells` : 'Spell registry'}</h2>
        </div>
        <div className="screen-head-actions">
          <button type="button" className="ghost-btn"><Icon name="search" size={12} /> Find</button>
          <button type="button" className="primary-btn"><Icon name="plus" size={11} /> Custom spell</button>
        </div>
      </header>

      <p style={{ fontFamily: 'var(--font-body)', color: 'var(--ink-dim)', fontStyle: 'italic', fontSize: 14 }}>
        Spells are stored as Spell nodes in Drupal. Enable <code>nodeSpells</code> in the GraphQL query
        and add them to ConsoleData to populate this registry.
      </p>
    </div>
  );
}
