/**
 * Character rosters for a story arc.
 *
 * The two pickers cannot share a filter: a PC exists twice (canonical template
 * plus campaign clone) and the arc must point at the clone, while NPCs have no
 * clones yet and the same filter would return nothing.
 */

import type { ConsoleData, DrupalCharacter } from '../components/console/ConsoleContext';
import type { RosterEntry } from './arcMarkdown';

/** Player characters belonging to one campaign: clones only, never templates. */
export function partyRoster(data: ConsoleData, campaignName: string | null): DrupalCharacter[] {
  if (!campaignName) {
    return [];
  }
  return data.characters
    .filter(c => c.characterType !== false)
    .filter(c => c.sourceCharacter === false && c.campaign === campaignName)
    .sort((a, b) => a.title.localeCompare(b.title));
}

/** Prefers a campaign clone when one exists, else canon, so each NPC appears once. */
export function npcRoster(data: ConsoleData, campaignName: string | null): DrupalCharacter[] {
  const npcs = data.characters.filter(c => c.characterType === false);
  const byTitle = new Map<string, DrupalCharacter>();
  for (const npc of npcs) {
    const existing = byTitle.get(npc.title);
    if (!existing) {
      byTitle.set(npc.title, npc);
      continue;
    }
    const isClone = npc.sourceCharacter === false && npc.campaign === campaignName;
    if (isClone) {
      byTitle.set(npc.title, npc);
    }
  }
  return Array.from(byTitle.values()).sort((a, b) => a.title.localeCompare(b.title));
}

/** What the markdown importer resolves names against. */
export function importRoster(data: ConsoleData, campaignName: string | null): RosterEntry[] {
  return [...partyRoster(data, campaignName), ...npcRoster(data, campaignName)]
    .map(c => ({ id: c.id, title: c.title }));
}

/** Distinct factions present on the NPC roster, for the antagonist picker. */
export function factionOptions(npcs: DrupalCharacter[]): Array<{ id: string; name: string; count: number }> {
  const seen = new Map<string, { id: string; name: string; count: number }>();
  for (const npc of npcs) {
    if (!npc.factionId || !npc.faction) {
      continue;
    }
    const row = seen.get(npc.factionId);
    if (row) {
      row.count += 1;
    } else {
      seen.set(npc.factionId, { id: npc.factionId, name: npc.faction, count: 1 });
    }
  }
  return Array.from(seen.values()).sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}
