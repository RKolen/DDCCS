/**
 * Shared Drupal → ConsoleData transform.
 * Used by every page that mounts a StatelyLedger (index.tsx, party.tsx, …).
 *
 * Campaigns come from the direct termCampaigns query so that campaigns
 * without any stories or characters still appear in the switcher.
 */

import type {
  ConsoleData, DrupalCampaign, DrupalCharacter, DrupalStory,
} from '../components/console/ConsoleContext';

export interface RawCampaignOnCharacter {
  id: string;
  name: string;
}

export interface RawCampaignTerm {
  id:             string;
  name:           string;
  campaignStatus: string | null;
  currentParty:   Array<{ id: string; title: string }> | null;
}

export interface RawCampaignOnStory {
  id:             string;
  name:           string;
  campaignStatus: string | null;
  currentParty:   Array<{ id: string; title: string }>;
}

export interface RawCharacter {
  id:              string;
  title:           string;
  firstName:       string | null;
  nickname:        string | null;
  level:           number | null;
  armorClass:      number | null;
  maximumHitpoints: number | null;
  movementSpeed:   number | null;
  proficiencyBonus: number | null;
  pronouns:        string | null;
  characterType:   boolean | null;
  sourceCharacter: boolean | null;
  role:            string | null;
  path:            string | null;
  campaign:        RawCampaignOnCharacter | null;
  image:           { mediaImage: { url: string; alt: string } | null } | null;
  species?:          { name: string } | null;
  lineage?:          { name: string } | null;
  background?:       { name: string } | null;
  bonds?:            Array<{ value: string }> | null;
  ideals?:           Array<{ value: string }> | null;
  flaws?:            Array<{ value: string }> | null;
  personalityTraits?: Array<{ value: string }> | null;
  majorPlotActions?:  Array<{ value: string }> | null;
}

export interface RawStory {
  id:          string;
  title:       string;
  storyNumber: number | null;
  path:        string | null;
  sessionDate: string | null;
  campaign:    RawCampaignOnStory | null;
}

export interface ConsoleQueryData {
  drupal: {
    nodeCharacters: { nodes: RawCharacter[] };
    nodeStories:    { nodes: RawStory[] };
    termCampaigns:  { nodes: RawCampaignTerm[] };
  } | null;
}

export function buildConsoleData(data: ConsoleQueryData | null | undefined): ConsoleData {
  if (!data?.drupal) return { campaigns: [], characters: [], stories: [] };

  const characters: DrupalCharacter[] = data.drupal.nodeCharacters.nodes.map(n => ({
    id:               n.id,
    title:            n.title,
    nickname:         n.nickname,
    level:            n.level,
    armorClass:       n.armorClass,
    maximumHitpoints: n.maximumHitpoints,
    movementSpeed:    n.movementSpeed,
    proficiencyBonus: n.proficiencyBonus,
    pronouns:         n.pronouns,
    role:             n.role,
    characterClass:   null,
    characterType:    n.characterType,
    sourceCharacter:  n.sourceCharacter,
    campaign:         n.campaign?.name ?? null,
    campaignId:       n.campaign?.id ?? null,
    path:             n.path,
    imageUrl:         n.image?.mediaImage?.url ?? null,
    species:          n.species?.name ?? null,
    lineage:          n.lineage?.name ?? null,
    background:       n.background?.name ?? null,
    bonds:            (n.bonds ?? []).map(b => b.value),
    ideals:           (n.ideals ?? []).map(b => b.value),
    flaws:            (n.flaws ?? []).map(b => b.value),
    personalityTraits: (n.personalityTraits ?? []).map(b => b.value),
    majorPlotActions:  (n.majorPlotActions ?? []).map(b => b.value),
  }));

  const stories: DrupalStory[] = data.drupal.nodeStories.nodes
    .slice()
    .sort((a, b) => (a.storyNumber ?? 0) - (b.storyNumber ?? 0))
    .map(n => ({
      id:          n.id,
      title:       n.title,
      storyNumber: n.storyNumber,
      path:        n.path,
      sessionDate: n.sessionDate,
      campaign:    n.campaign?.name ?? null,
      campaignId:  n.campaign?.id ?? null,
    }));

  /* Build campaign map — primary source is the direct termCampaigns query
     so campaigns without stories or characters are always included. */
  const campaignMap = new Map<string, DrupalCampaign>();

  for (const c of data.drupal.termCampaigns.nodes) {
    campaignMap.set(c.name, {
      id:              c.id,
      name:            c.name,
      campaignStatus:  c.campaignStatus,
      currentPartyIds: (c.currentParty ?? []).map(m => m.id),
    });
  }

  /* Fill in any campaigns referenced by stories that weren't in the term query */
  for (const s of data.drupal.nodeStories.nodes) {
    if (!s.campaign || campaignMap.has(s.campaign.name)) continue;
    const { id, name, campaignStatus, currentParty } = s.campaign;
    campaignMap.set(name, {
      id,
      name,
      campaignStatus,
      currentPartyIds: currentParty.map(m => m.id),
    });
  }

  return {
    campaigns: Array.from(campaignMap.values()),
    characters,
    stories,
  };
}
