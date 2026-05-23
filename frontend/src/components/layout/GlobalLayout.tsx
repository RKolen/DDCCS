/**
 * GlobalLayout — wraps every Gatsby page.
 *
 * Owns activeCampaignName and the campaigns list as single sources of truth.
 * Both are persisted to localStorage so they survive page loads and refreshes.
 *
 * register() merges incoming campaigns with the existing list rather than
 * replacing it — this prevents pages that only know about campaigns with
 * stories (e.g. stories.tsx) from wiping empty campaigns registered by
 * StatelyLedger.
 */

import * as React from 'react';
import { GlobalTopbar } from './GlobalTopbar';
import { TopbarContext } from './TopbarContext';
import type { DrupalCampaign } from '../console/ConsoleContext';

const ACTIVE_KEY    = 'ddccs:activeCampaign';
const CAMPAIGNS_KEY = 'ddccs:campaigns';

function readStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    return raw !== null ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function dedupeByName(campaigns: DrupalCampaign[]): DrupalCampaign[] {
  const seen = new Set<string>();
  return campaigns.filter(c => {
    if (seen.has(c.name)) return false;
    seen.add(c.name);
    return true;
  });
}

interface GlobalLayoutProps {
  children:  React.ReactNode;
  location?: { pathname: string; search: string };
}

export function GlobalLayout({ children, location }: GlobalLayoutProps): React.ReactElement {
  const [campaigns, setCampaigns] = React.useState<DrupalCampaign[]>(
    () => dedupeByName(readStorage<DrupalCampaign[]>(CAMPAIGNS_KEY, [])),
  );

  const [activeCampaignName, setActiveCampaignName] = React.useState<string | null>(
    () => readStorage<string | null>(ACTIVE_KEY, null),
  );

  React.useEffect(() => {
    if (campaigns.length > 0) {
      window.localStorage.setItem(CAMPAIGNS_KEY, JSON.stringify(campaigns));
    }
  }, [campaigns]);

  React.useEffect(() => {
    if (activeCampaignName !== null) {
      window.localStorage.setItem(ACTIVE_KEY, activeCampaignName);
    }
  }, [activeCampaignName]);

  /* register() merges by name: campaigns already present by name are skipped.
     Pages that register with id=name (stories.tsx, campaign-reader) never
     create duplicates alongside UUID-based entries from StatelyLedger. */
  const register = React.useCallback(
    (liveCampaigns: DrupalCampaign[], initialActiveName: string | null) => {
      setCampaigns(prev => {
        const existingNames = new Set(prev.map(c => c.name));
        const toAdd = liveCampaigns.filter(c => !existingNames.has(c.name));
        return toAdd.length > 0 ? dedupeByName([...prev, ...toAdd]) : prev;
      });
      setActiveCampaignName(prev => prev ?? initialActiveName);
    },
    [],
  );

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
