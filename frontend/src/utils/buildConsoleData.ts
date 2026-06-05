/**
 * Shared Drupal → ConsoleData transform.
 * Used by every page that mounts a StatelyLedger (index.tsx, party.tsx, …).
 *
 * Campaigns come from the direct termCampaigns query so that campaigns
 * without any stories or characters still appear in the switcher.
 */

import type {
  ConsoleData, DrupalCampaign, DrupalCharacter, DrupalStory, DrupalMonster, DrupalItem,
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

export interface RawItem {
  drupalId:               string;
  title:                  string;
  itemType?:              string | null;
  isMagic?:               boolean | null;
  itemRarity?:            string | null;
  itemRequiresAttunement?: boolean | null;
  source?:                string | null;
  edition?:               { name: string } | null;
  vestigeLevel?:          { name: string } | null;
  damageTypes?:           Array<{ name: string }> | null;
  weaponProperties?:      Array<{ name: string }> | null;
  weaponMastery?:         Array<{ name: string }> | null;
  weaponSubtype?:         Array<{ name: string }> | null;
  itemProperties?:        Array<{ name: string; effectHtml: string | null }> | null;
  damage?:                string | null;
  itemBonus?:             number | null;
  itemCost?:              string | null;
  itemWeight?:            number | null;
  nonidentifiedName?:     string | null;
  armorCategory?:         string | null;
  armorAcBase?:           number | null;
  armorStrRequirement?:   number | null;
  notes?:                 { value: string } | null;
  notesHtml?:             string | null;
  descriptionHtml?:       string | null;
  path?:                  string | null;
  image?:                 { mediaImage: { url: string; alt: string } | null } | null;
}

export interface RawMonster {
  id:                       string;
  title:                    string;
  challengeRating?:         number | null;
  type?:                    { name: string } | null;
  faction?:                 { name: string } | null;
  monsterSize?:             string | null;
  monsterAlignment?:        string | null;
  monsterSpeed?:            string | null;
  monsterHitDice?:          string | null;
  monsterXp?:               number | null;
  monsterDamageResistances?: string | null;
  monsterDamageImmunities?: string | null;
  monsterSenses?:           string | null;
  monsterLanguages?:        string | null;
  monsterSkills?:           string | null;
  maximumHitpoints?:        number | null;
  armorClass?:              number | null;
  movementSpeed?:           number | null;
  path?:                    string | null;
  campaign?:                RawCampaignOnCharacter | null;
  image?:                   { mediaImage: { url: string; alt: string } | null } | null;
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
    nodeMonsters?:  { nodes: RawMonster[] } | null;
  } | null;
  /* Items come from Gatsby sourceNodes (all pages, no 100-item cap) */
  allAllItem?: { nodes: RawItem[] } | null;
}

function splitCsv(s: string | null | undefined): string[] {
  if (!s) return [];
  return s.split(',').map(v => v.trim()).filter(Boolean);
}

export function buildConsoleData(data: ConsoleQueryData | null | undefined): ConsoleData {
  if (!data?.drupal) return { campaigns: [], characters: [], stories: [], monsters: [], items: [] };

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

  const monsters: DrupalMonster[] = (data.drupal.nodeMonsters?.nodes ?? []).map(n => ({
    id:          n.id,
    title:       n.title,
    nickname:    null,
    cr:          n.challengeRating ?? null,
    monsterType: n.type?.name ?? null,
    size:        n.monsterSize ?? null,
    alignment:   n.monsterAlignment ?? null,
    faction:     n.faction?.name ?? null,
    profileType: null,
    tagline:     null,
    role:        null,
    recurring:   null,
    hp:          n.maximumHitpoints ?? null,
    maxHp:       n.maximumHitpoints ?? null,
    hitDice:     n.monsterHitDice ?? null,
    ac:          n.armorClass ?? null,
    acNote:      null,
    speed:       n.monsterSpeed ?? null,
    profBonus:   null,
    scores:      null,
    saves:       null,
    skills:      n.monsterSkills ? Object.fromEntries(
      n.monsterSkills.split(',').map(s => s.trim()).filter(Boolean).map(s => {
        const parts = s.split(':');
        return [parts[0]?.trim() ?? s, parts[1]?.trim() ?? ''];
      }),
    ) : null,
    resistances:         splitCsv(n.monsterDamageResistances),
    immunities:          splitCsv(n.monsterDamageImmunities),
    conditionImmunities: [],
    senses:              splitCsv(n.monsterSenses),
    languages:           splitCsv(n.monsterLanguages),
    traits:               [],
    actions:              [],
    legendaryActions:     null,
    lairActions:          null,
    regionalEffects:      null,
    encounterTactics:     [],
    plotHooks:            [],
    defeatConditions:     [],
    campaign:    n.campaign?.name ?? null,
    campaignId:  n.campaign?.id ?? null,
    path:        n.path ?? null,
    imageUrl:    n.image?.mediaImage?.url ?? null,
  }));

  /* Items come from Gatsby's sourceNodes (all pages, no per-query limit).
     edition taxonomy drives homebrew vs official classification:
       null / "Homebrew" → homebrew  |  "D&D 5.5e (2024)" etc. → official */
  const items: DrupalItem[] = (data.allAllItem?.nodes ?? []).map(n => ({
    id:                     n.drupalId,
    title:                  n.title,
    itemType:               n.itemType ?? null,
    isMagic:                n.isMagic ?? null,
    itemRarity:             n.itemRarity ?? null,
    itemRequiresAttunement: n.itemRequiresAttunement ?? null,
    source:                 n.edition?.name ?? n.source ?? null,
    damage:                 n.damage ?? null,
    itemBonus:              n.itemBonus ?? null,
    itemCost:               n.itemCost ?? null,
    itemWeight:             n.itemWeight ?? null,
    nonidentifiedName:      n.nonidentifiedName ?? null,
    armorCategory:          n.armorCategory ?? null,
    armorAcBase:            n.armorAcBase ?? null,
    armorStrRequirement:    n.armorStrRequirement ?? null,
    notes:                  n.notes?.value ?? null,
    notesHtml:              n.notesHtml ?? null,
    descriptionHtml:        n.descriptionHtml ?? null,
    vestigeLevel:           n.vestigeLevel?.name ?? null,
    damageTypes:            (n.damageTypes ?? []).map(t => t.name),
    weaponProperties:       (n.weaponProperties ?? []).map(t => t.name),
    weaponMastery:          (n.weaponMastery ?? []).map(t => t.name),
    weaponSubtype:          (n.weaponSubtype ?? []).map(t => t.name),
    itemProperties:         n.itemProperties ?? [],
    path:                   n.path ?? null,
    imageUrl:               n.image?.mediaImage?.url ?? null,
  }));

  return {
    campaigns: Array.from(campaignMap.values()),
    characters,
    stories,
    monsters,
    items,
  };
}
