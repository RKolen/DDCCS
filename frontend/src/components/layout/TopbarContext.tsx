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
  /** Register the available campaign list and the initial active campaign. */
  register: (campaigns: DrupalCampaign[], initialActiveName: string | null) => void;
}

export const TopbarContext = React.createContext<TopbarContextValue>({
  campaigns:          [],
  activeCampaignName: null,
  onSwitchCampaign:   () => undefined,
  register:           () => undefined,
});

TopbarContext.displayName = 'TopbarContext';

export function useTopbar(): TopbarContextValue {
  return React.useContext(TopbarContext);
}
