/**
 * GlobalLayout — wraps every Gatsby page.
 *
 * Owns activeCampaignName as the single source of truth.
 * StatelyLedger registers the campaign list here; the chip's onSwitchCampaign
 * updates this state directly — no callback indirection, no stale closures.
 */

import * as React from 'react';
import { GlobalTopbar } from './GlobalTopbar';
import { TopbarContext } from './TopbarContext';
import type { DrupalCampaign } from '../console/ConsoleContext';

interface GlobalLayoutProps {
  children:  React.ReactNode;
  location?: { pathname: string; search: string };
}

export function GlobalLayout({ children, location }: GlobalLayoutProps): React.ReactElement {
  const [campaigns,          setCampaigns]          = React.useState<DrupalCampaign[]>([]);
  const [activeCampaignName, setActiveCampaignName] = React.useState<string | null>(null);

  /* Pages register their campaign list + initial active campaign.
     We only set the initial active name if nothing has been chosen yet. */
  const register = React.useCallback(
    (liveCampaigns: DrupalCampaign[], initialActiveName: string | null) => {
      setCampaigns(liveCampaigns);
      setActiveCampaignName(prev => prev ?? initialActiveName);
    },
    [],
  );

  /* Switching always goes through this one setter — no stale closures. */
  const onSwitchCampaign = React.useCallback((name: string) => {
    setActiveCampaignName(name);
  }, []);

  return (
    <TopbarContext.Provider value={{ campaigns, activeCampaignName, onSwitchCampaign, register }}>
      <div className="global-layout">
        <GlobalTopbar location={location} />
        <div className="global-content">
          {children}
        </div>
      </div>
    </TopbarContext.Provider>
  );
}
