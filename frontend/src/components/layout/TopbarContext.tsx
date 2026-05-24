/**
 * TopbarContext — bridges the global topbar with page-level campaign data.
 *
 * GlobalLayout owns activeCampaignName as the single source of truth.
 * Pages register their campaign list via `register`; switching always goes
 * through onSwitchCampaign which updates only GlobalLayout's state.
 */

import * as React from 'react';
import type { DrupalCampaign } from '../console/ConsoleContext';

export interface TopbarContextValue {
  campaigns:          DrupalCampaign[];
  activeCampaignName: string | null;
  onSwitchCampaign:   (name: string) => void;
  /**
   * Register the available campaign list and the initial active campaign.
   * Pass canonical=true only from callers that have the complete list from
   * Drupal — this prunes deleted campaigns from localStorage.
   */
  register: (campaigns: DrupalCampaign[], initialActiveName: string | null, canonical?: boolean) => void;
  /**
   * Add a newly created campaign and activate it. Writes to localStorage
   * synchronously so the value survives an immediate page reload.
   */
  addCampaign: (campaign: DrupalCampaign) => void;
}

export const TopbarContext = React.createContext<TopbarContextValue>({
  campaigns:          [],
  activeCampaignName: null,
  onSwitchCampaign:   () => undefined,
  register:           () => undefined,
  addCampaign:        () => undefined,
});

TopbarContext.displayName = 'TopbarContext';

export function useTopbar(): TopbarContextValue {
  return React.useContext(TopbarContext);
}
