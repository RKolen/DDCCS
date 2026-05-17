/**
 * ConsoleContext — live Drupal data for the StatelyLedger console.
 *
 * All data comes from the index.tsx page query. Screens consume this
 * context and show empty states when data is absent — no mock fallbacks.
 *
 * NPC note: NPCs are character nodes with characterType = false.
 */

import * as React from 'react';

/* ────────────────────────────────────────────────────────────
   Shapes (mirror Drupal GraphQL fields, camelCase)
   ──────────────────────────────────────────────────────────── */

export interface DrupalCampaign {
  id: string;
  name: string;
  /** field_campaign_status value from the taxonomy term */
  campaignStatus: string | null;
  /** IDs of characters in field_current_party on the campaign term */
  currentPartyIds?: string[];
}

export interface DrupalCharacter {
  id: string;
  title: string;
  nickname: string | null;
  level: number | null;
  armorClass: number | null;
  maximumHitpoints: number | null;
  movementSpeed?: number | null;
  proficiencyBonus?: number | null;
  pronouns: string | null;
  role?: string | null;
  /** Class name: omitted for now — 'class' as a field name breaks graphql-js parser */
  characterClass: string | null;
  /** true = player character, false = NPC */
  characterType: boolean | null;
  campaign: string | null;
  campaignId: string | null;
  path: string | null;
  imageUrl: string | null;
}

export interface DrupalStory {
  id: string;
  title: string;
  storyNumber: number | null;
  path: string | null;
  sessionDate: string | null;
  /** Campaign taxonomy term name */
  campaign: string | null;
  campaignId: string | null;
}

export interface ConsoleData {
  campaigns: DrupalCampaign[];
  characters: DrupalCharacter[];
  stories: DrupalStory[];
}

/* ────────────────────────────────────────────────────────────
   Derived helpers — no filtering by mock data, pure from Drupal
   ──────────────────────────────────────────────────────────── */

export function playerCharacters(data: ConsoleData): DrupalCharacter[] {
  return data.characters.filter(c => c.characterType !== false);
}

export function npcCharacters(data: ConsoleData): DrupalCharacter[] {
  return data.characters.filter(c => c.characterType === false);
}

export function storiesForCampaign(data: ConsoleData, campaignName: string): DrupalStory[] {
  return data.stories.filter(s => s.campaign === campaignName);
}

export function charactersForCampaign(data: ConsoleData, campaignName: string): DrupalCharacter[] {
  return playerCharacters(data).filter(c => c.campaign === campaignName);
}

/* ────────────────────────────────────────────────────────────
   Context
   ──────────────────────────────────────────────────────────── */

const ConsoleContext = React.createContext<ConsoleData>({
  campaigns: [],
  characters: [],
  stories: [],
});

ConsoleContext.displayName = 'ConsoleContext';

export { ConsoleContext };

export function useConsoleData(): ConsoleData {
  return React.useContext(ConsoleContext);
}
