/**
 * Shared Drupal → ConsoleData transform.
 * Used by every page that mounts a StatelyLedger (index.tsx, party.tsx, …).
 */

import type {
  ConsoleData, DrupalCampaign, DrupalCharacter, DrupalStory,
} from '../components/console/ConsoleContext';

export interface RawCampaignOnCharacter {
  id: string;
  name: string;
}

export interface RawCampaignOnStory {
  id: string;
  name: string;
  campaignStatus: string | null;
  currentParty: Array<{ id: string; title: string }>;
}

export interface RawCharacter {
  id: string;
  title: string;
  firstName: string | null;
  nickname: string | null;
  level: number | null;
  armorClass: number | null;
  maximumHitpoints: number | null;
  movementSpeed: number | null;
  proficiencyBonus: number | null;
  pronouns: string | null;
  characterType: boolean | null;
  role: string | null;
  path: string | null;
  campaign: RawCampaignOnCharacter | null;
  image: { mediaImage: { url: string; alt: string } | null } | null;
}

export interface RawStory {
  id: string;
  title: string;
  storyNumber: number | null;
  path: string | null;
  sessionDate: string | null;
  campaign: RawCampaignOnStory | null;
}

export interface ConsoleQueryData {
  drupal: {
    nodeCharacters: { nodes: RawCharacter[] };
    nodeStories:    { nodes: RawStory[] };
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
    campaign:         n.campaign?.name ?? null,
    campaignId:       n.campaign?.id ?? null,
    path:             n.path,
    imageUrl:         n.image?.mediaImage?.url ?? null,
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

  const campaignMap = new Map<string, DrupalCampaign>();

  for (const s of data.drupal.nodeStories.nodes) {
    if (!s.campaign) continue;
    const { id, name, campaignStatus, currentParty } = s.campaign;
    if (!campaignMap.has(name)) {
      campaignMap.set(name, {
        id,
        name,
        campaignStatus,
        currentPartyIds: currentParty.map(m => m.id),
      });
    }
  }

  for (const c of data.drupal.nodeCharacters.nodes) {
    if (!c.campaign) continue;
    const { id, name } = c.campaign;
    if (!campaignMap.has(name)) {
      campaignMap.set(name, { id, name, campaignStatus: null });
    }
  }

  return {
    campaigns: Array.from(campaignMap.values()),
    characters,
    stories,
  };
}
