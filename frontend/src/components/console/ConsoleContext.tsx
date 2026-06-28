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
  /** true = template / source character, false = campaign clone */
  sourceCharacter: boolean | null;
  campaign: string | null;
  campaignId: string | null;
  path: string | null;
  imageUrl: string | null;
  /** Rich profile fields for story generation */
  species: string | null;
  lineage: string | null;
  background: string | null;
  bonds: string[];
  ideals: string[];
  flaws: string[];
  personalityTraits: string[];
  majorPlotActions: string[];
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

/* ── Monster action shapes ───────────────────────────── */

export interface MonsterAction {
  name: string;
  desc: string;
  cost?: number;
}

export interface MonsterLegendaryActions {
  available: number;
  actions: MonsterAction[];
}

export interface MonsterLairActions {
  enabled: boolean;
  lairLocation: string | null;
  actions: MonsterAction[];
}

export interface MonsterRegionalEffects {
  enabled: boolean;
  radius: string | null;
  effects: MonsterAction[];
}

export interface DrupalMonster {
  id: string;
  title: string;
  nickname: string | null;
  monsterType: string | null;
  size: string | null;
  alignment: string | null;
  faction: string | null;
  cr: number | null;
  /** 'simplified' | 'full' | 'major' */
  profileType: string | null;
  tagline: string | null;
  role: string | null;
  recurring: boolean | null;
  hp: number | null;
  maxHp: number | null;
  hitDice: string | null;
  ac: number | null;
  acNote: string | null;
  speed: string | null;
  profBonus: number | null;
  scores: Record<string, number> | null;
  saves: Record<string, string> | null;
  skills: Record<string, string> | null;
  resistances: string[];
  immunities: string[];
  conditionImmunities: string[];
  senses: string[];
  languages: string[];
  traits: MonsterAction[];
  actions: MonsterAction[];
  legendaryActions: MonsterLegendaryActions | null;
  lairActions: MonsterLairActions | null;
  regionalEffects: MonsterRegionalEffects | null;
  encounterTactics: string[];
  plotHooks: string[];
  defeatConditions: string[];
  campaign: string | null;
  campaignId: string | null;
  path: string | null;
  imageUrl: string | null;
}

export interface DrupalItem {
  id:                     string;
  title:                  string;
  itemType:               string | null;
  isMagic:                boolean | null;
  itemRarity:             string | null;
  itemRequiresAttunement: boolean | null;
  /** edition.name from Drupal: null/"Homebrew" = custom, "D&D 5.5e (2024)" etc. = official */
  source:                 string | null;
  damage:                 string | null;
  itemBonus:              number | null;
  itemCost:               string | null;
  itemWeight:             number | null;
  nonidentifiedName:      string | null;
  armorCategory:          string | null;
  armorAcBase:            number | null;
  armorStrRequirement:    number | null;
  descriptionHtml:        string | null;
  vestigeLevel:           string | null;
  damageTypes:            string[];
  weaponProperties:       string[];
  weaponMastery:          string[];
  weaponSubtype:          string[];
  itemProperties:         Array<{ name: string; effectHtml: string | null }>;
  path:                   string | null;
  imageUrl:               string | null;
}

export interface ConsoleData {
  campaigns: DrupalCampaign[];
  characters: DrupalCharacter[];
  stories: DrupalStory[];
  monsters: DrupalMonster[];
  items: DrupalItem[];
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
  // A character belongs to a campaign either by its own field_campaign (clones)
  // or by membership in the campaign term's current party (source characters
  // added directly to a party). The party is the authoritative list, so union
  // both signals.
  const campaign = data.campaigns.find(c => c.name === campaignName);
  const partyIds = new Set(campaign?.currentPartyIds ?? []);
  return playerCharacters(data).filter(
    c => c.campaign === campaignName || partyIds.has(c.id),
  );
}

/* ────────────────────────────────────────────────────────────
   Context
   ──────────────────────────────────────────────────────────── */

const ConsoleContext = React.createContext<ConsoleData>({
  campaigns: [],
  characters: [],
  stories: [],
  monsters: [],
  items: [],
});

ConsoleContext.displayName = 'ConsoleContext';

export { ConsoleContext };

export function useConsoleData(): ConsoleData {
  return React.useContext(ConsoleContext);
}
