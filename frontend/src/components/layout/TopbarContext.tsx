/**
 * TopbarContext — bridges the global topbar with page-level campaign data.
 *
 * Pages that have campaign data (primarily the console) register their
 * campaigns and active selection here so the global topbar can render a
 * live campaign chip. Non-console pages leave it at the empty default.
 */

import * as React from 'react';
import type { DrupalCampaign } from '../console/ConsoleContext';

export interface TopbarContextValue {
  campaigns: DrupalCampaign[];
  activeCampaignName: string | null;
  onSwitchCampaign: (name: string) => void;
  register: (
    campaigns: DrupalCampaign[],
    activeName: string | null,
    onSwitch: (name: string) => void,
  ) => void;
}

export const TopbarContext = React.createContext<TopbarContextValue>({
  campaigns: [],
  activeCampaignName: null,
  onSwitchCampaign: () => undefined,
  register: () => undefined,
});

TopbarContext.displayName = 'TopbarContext';

export function useTopbar(): TopbarContextValue {
  return React.useContext(TopbarContext);
}
