/**
 * GlobalLayout — wraps every Gatsby page.
 *
 * Owns activeCampaignName and the campaigns list as single sources of truth.
 * Both are persisted to localStorage so they survive page loads and refreshes.
 *
 * register(campaigns, initial, canonical=false) merges by default so partial-
 * list callers (stories.tsx, campaign-reader.tsx) never wipe campaigns they
 * don't know about. Pass canonical=true only from StatelyLedger, which has
 * the full list from Drupal — this prunes deleted campaigns from localStorage.
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

  /* canonical=true replaces the stored list with liveCampaigns (pruning deleted
     entries). canonical=false (default) only adds campaigns not yet present —
     safe for partial-list callers that don't know about all campaigns. */
  const register = React.useCallback(
    (liveCampaigns: DrupalCampaign[], initialActiveName: string | null, canonical = false) => {
      setCampaigns(prev => {
        if (canonical) {
          return dedupeByName(liveCampaigns);
        }
        const existingNames = new Set(prev.map(c => c.name));
        const toAdd = liveCampaigns.filter(c => !existingNames.has(c.name));
        return toAdd.length > 0 ? dedupeByName([...prev, ...toAdd]) : prev;
      });
      setActiveCampaignName(prev => {
        const liveNames = new Set(liveCampaigns.map(c => c.name));
        if (canonical && prev !== null && !liveNames.has(prev)) {
          return liveCampaigns[0]?.name ?? null;
        }
        return prev ?? initialActiveName;
      });
    },
    [],
  );

  const onSwitchCampaign = React.useCallback((name: string) => {
    setActiveCampaignName(name);
  }, []);

  /* addCampaign writes synchronously to localStorage so the new entry
     survives an immediate window.location.reload() before the useEffects fire. */
  const addCampaign = React.useCallback((campaign: DrupalCampaign) => {
    setCampaigns(prev => {
      const updated = dedupeByName([...prev, campaign]);
      window.localStorage.setItem(CAMPAIGNS_KEY, JSON.stringify(updated));
      return updated;
    });
    setActiveCampaignName(campaign.name);
    window.localStorage.setItem(ACTIVE_KEY, campaign.name);
  }, []);

  return (
    <TopbarContext.Provider value={{ campaigns, activeCampaignName, onSwitchCampaign, register, addCampaign }}>
      <div className="global-layout">
        <GlobalTopbar location={location} />
        <div className="global-content">
          {children}
        </div>
      </div>
    </TopbarContext.Provider>
  );
}
