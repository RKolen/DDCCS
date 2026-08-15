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
  /** Synthesized "story so far" HTML from field_campaign_overview, if any */
  campaignOverview?: string | null;
}

/** A taxonomy term reduced to what the console needs: identity and label. */
export interface TermRef {
  id: string;
  name: string;
}

/**
 * The six ability scores, flattened out of the ability_scores paragraph.
 *
 * Always present as an object so a consumer can read a score without a null
 * check on the paragraph; an ability the character has no score for is null.
 */
export interface DrupalAbilityScores {
  strength:     number | null;
  dexterity:    number | null;
  constitution: number | null;
  intelligence: number | null;
  wisdom:       number | null;
  charisma:     number | null;
}

/**
 * One class paragraph. A multiclassed character has several, in Drupal's order.
 */
export interface DrupalCharacterClass {
  name: string;
  subclass: string | null;
  level: number | null;
}

/** The ability keys, in the order a character sheet lists them. */
export const ABILITY_KEYS: Array<keyof DrupalAbilityScores> = [
  'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma',
];

export interface DrupalCharacter {
  id: string;
  title: string;
  firstName: string | null;
  lastName: string | null;
  nickname: string | null;
  level: number | null;
  armorClass: number | null;
  maximumHitpoints: number | null;
  movementSpeed?: number | null;
  proficiencyBonus?: number | null;
  gold: number | null;
  abilityScores: DrupalAbilityScores;
  pronouns: string | null;
  gender: string | null;
  role?: string | null;
  /** Primary class name — `classes[0]`, kept flat for the many one-line summaries. */
  characterClass: string | null;
  /** Every class paragraph, so a multiclassed character reads correctly. */
  classes: DrupalCharacterClass[];
  /** true = player character, false = NPC */
  characterType: boolean | null;
  /** true = template / source character, false = campaign clone */
  sourceCharacter: boolean | null;
  /**
   * field_recurring. On an NPC this is what marks it as deserving a full
   * character profile rather than a walk-on part, and the editor uses it to
   * decide which field groups to offer.
   */
  recurring: boolean | null;
  campaign: string | null;
  campaignId: string | null;
  path: string | null;
  imageUrl: string | null;
  /** Reusable image-generation prompt (field_image_prompt), or null. */
  imagePrompt: string | null;
  /**
   * Rich profile fields for story generation. The term fields are carried as
   * both the display name (what most screens read) and the term UUID (what the
   * editor must send back to write the reference).
   */
  species: string | null;
  speciesId: string | null;
  lineage: string | null;
  lineageId: string | null;
  background: string | null;
  backgroundId: string | null;
  bonds: string[];
  ideals: string[];
  flaws: string[];
  personalityTraits: string[];
  majorPlotActions: string[];
  specializedAbilities: string[];
  plotHooks: string[];
  abilities: string[];
  personality: string | null;
  notes: string | null;
  languages: TermRef[];
  skills: TermRef[];
  tools: TermRef[];
  /**
   * Allegiance and characterisation. field_faction carries the ally/bbeg/neutral
   * style tag an NPC is filed under; field_key_traits is the shared `traits`
   * vocabulary the AI draws on for characterisation.
   */
  faction: string | null;
  factionId: string | null;
  keyTraits: TermRef[];
  /** Antagonist fields — populated on NPCs, generally empty on PCs. */
  encounterTactics: string[];
  defeatConditions: string[];
  lairActions: string[];
  legendaryActions: string[];
  regionalEffects: string[];
  /** Per-character AI overrides. */
  aiEnabled: boolean | null;
  aiModel: string | null;
  aiTemperature: number | null;
  aiMaxTokens: number | null;
  aiSystemPrompt: string | null;
  voiceId: string | null;
  voicePitch: number | null;
  voiceSpeed: number | null;
  /** Saved arc analysis, or null when never analysed. */
  arc: DrupalCharacterArc | null;
}

/** A saved arc metric's progression (series parsed from Drupal's CSV string). */
export interface DrupalArcMetric {
  label: string;
  series: number[];
  direction: string;
  obs: string;
}

/** A saved arc relationship. */
export interface DrupalArcRelationship {
  target: string;
  type: string;
  strength: number;
  trust: number;
  note: string;
}

/** A saved arc goal. */
export interface DrupalArcGoal {
  description: string;
  status: string;
  progress: number;
}

/** A character's saved arc analysis, mapped from the Drupal arc fields. */
export interface DrupalCharacterArc {
  direction: string;
  stage: string;
  summary: string;
  storiesAnalyzed: number;
  lastAnalyzed: string;
  metrics: Record<string, DrupalArcMetric>;
  relationships: DrupalArcRelationship[];
  goals: DrupalArcGoal[];
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
  weaponCategory:         string | null;
  weaponRange:            string | null;
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

/**
 * Scope an already-filtered roster to one campaign.
 *
 * A character belongs to a campaign either by its own field_campaign (clones)
 * or by membership in the campaign term's current party (source characters
 * added directly to a party). The party is the authoritative list, so union
 * both signals.
 */
function scopeToCampaign(
  data: ConsoleData,
  roster: DrupalCharacter[],
  campaignName: string,
): DrupalCharacter[] {
  const campaign = data.campaigns.find(c => c.name === campaignName);
  const partyIds = new Set(campaign?.currentPartyIds ?? []);
  return roster.filter(c => c.campaign === campaignName || partyIds.has(c.id));
}

export function charactersForCampaign(data: ConsoleData, campaignName: string): DrupalCharacter[] {
  return scopeToCampaign(data, playerCharacters(data), campaignName);
}

/*
 * There is deliberately no npcsForCampaign(). NPCs are not campaign-scoped:
 * field_campaign is unset on every NPC and they never join a campaign's
 * currentParty, so scoping them to a campaign yields an empty roster. The
 * bestiary of antagonists is shared across campaigns.
 */

/**
 * The roster a character screen should show: PCs scoped to the active campaign,
 * or the full NPC list.
 *
 * **NPCs are never campaign-scoped.** A player character belongs to a campaign
 * through field_campaign or the campaign's current party; an NPC carries
 * neither, so filtering NPCs by campaign empties the roster outright. The NPC
 * roster is shared across campaigns by design.
 *
 * `pinnedId` is a character that must appear even when it falls outside that
 * scope — the one arrived at from a deep link or from the completeness audit.
 * Without it, following a link to a character who is not in the active
 * campaign's party lands on an empty or wrong selection.
 *
 * The pin escapes the campaign scope but never the record-type one: it is
 * resolved against the PC/NPC list this screen asked for, so a player character
 * left over from a `?char=` link cannot be pinned into the NPC roster (and vice
 * versa) when the operator switches sections.
 */
export function rosterForScreen(
  data: ConsoleData,
  options: { npcMode?: boolean; campaignName?: string | null; pinnedId?: string | null },
): DrupalCharacter[] {
  const { npcMode = false, campaignName = null, pinnedId = null } = options;
  const all = npcMode ? npcCharacters(data) : playerCharacters(data);
  const scoped = !npcMode && campaignName != null && campaignName !== ''
    ? scopeToCampaign(data, all, campaignName)
    : all;

  if (pinnedId == null || scoped.some(c => c.id === pinnedId)) {
    return scoped;
  }
  const pinned = all.find(c => c.id === pinnedId);
  return pinned ? [pinned, ...scoped] : scoped;
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
