/**
 * GlobalLayout — wraps every Gatsby page.
 *
 * Receives the Gatsby `location` object from wrapPageElement so the topbar
 * can stay in sync with the current URL (e.g., showing/clearing the search
 * query on /search/).
 */

import * as React from 'react';
/* Minimal shape from Gatsby's PageProps location — avoids importing @gatsbyjs/reach-router */
interface GatsbyLocation { pathname: string; search: string; }
import { GlobalTopbar } from './GlobalTopbar';
import { TopbarContext } from './TopbarContext';
import type { DrupalCampaign } from '../console/ConsoleContext';

interface GlobalLayoutProps {
  children: React.ReactNode;
  location?: GatsbyLocation;
}

export function GlobalLayout({ children, location }: GlobalLayoutProps): React.ReactElement {
  const [campaigns, setCampaigns] = React.useState<DrupalCampaign[]>([]);
  const [activeCampaignName, setActiveCampaignName] = React.useState<string | null>(null);
  const [switchFn, setSwitchFn] = React.useState<((name: string) => void) | null>(null);

  const register = React.useCallback(
    (
      liveCampaigns: DrupalCampaign[],
      activeName: string | null,
      onSwitch: (name: string) => void,
    ) => {
      setCampaigns(liveCampaigns);
      setActiveCampaignName(activeName);
      setSwitchFn(() => onSwitch);
    },
    [],
  );

  const onSwitchCampaign = React.useCallback(
    (name: string) => {
      setActiveCampaignName(name);
      switchFn?.(name);
    },
    [switchFn],
  );

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
