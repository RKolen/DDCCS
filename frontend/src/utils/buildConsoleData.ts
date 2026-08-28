/**
 * Shared Drupal → ConsoleData transform.
 * Used by every page that mounts a StatelyLedger (index.tsx, party.tsx, …).
 *
 * Campaigns come from the direct termCampaigns query so that campaigns
 * without any stories or characters still appear in the switcher.
 */

import type {
  ConsoleData, DrupalCampaign, DrupalCharacter, DrupalStory, DrupalMonster, DrupalItem,
  DrupalCharacterArc, DrupalArcMetric, DrupalAbilityScores, DrupalCharacterClass, TermRef,
  DrupalStoryArc, DrupalArcRelation,
} from '../components/console/ConsoleContext';
import { textValues, htmlToText } from './richTextToLines';

/** Drop the union members GraphQL returns as `{}` for unexposed vocabularies. */
function termRefs(items: RawTermRef[] | null | undefined): TermRef[] {
  return (items ?? []).filter((t): t is RawTermRef => Boolean(t?.id && t.name));
}

/** Parse Drupal's comma-separated metric series string into numbers. */
function parseSeries(csv: string | null | undefined): number[] {
  if (!csv) {
    return [];
  }
  return csv
    .split(',')
    .map(s => Number(s.trim()))
    .filter(n => !Number.isNaN(n));
}

/** Map a character's raw Drupal arc fields into DrupalCharacterArc, or null. */
function buildCharacterArc(n: RawCharacter): DrupalCharacterArc | null {
  const hasArc = Boolean(n.arcDirection || n.arcSummary || (n.arcMetrics?.length ?? 0) > 0);
  if (!hasArc) {
    return null;
  }
  const metrics: Record<string, DrupalArcMetric> = {};
  for (const m of n.arcMetrics ?? []) {
    const key = m.metricKey ?? m.metricLabel ?? '';
    if (!key) {
      continue;
    }
    metrics[key] = {
      label:     m.metricLabel ?? key,
      series:    parseSeries(m.metricSeries),
      direction: m.metricDirection ?? 'stasis',
      obs:       m.metricObs ?? '',
    };
  }
  return {
    direction:       n.arcDirection ?? 'stasis',
    stage:           n.arcStage ?? 'introduction',
    summary:         n.arcSummary ?? '',
    storiesAnalyzed: n.arcStories ?? 0,
    lastAnalyzed:    n.arcUpdated ?? '',
    metrics,
    relationships: (n.arcRelationships ?? [])
      .filter(r => (r.relTarget ?? '').trim() !== '')
      .map(r => ({
        target:   r.relTarget ?? '',
        type:     r.relType ?? 'neutral',
        strength: r.relStrength ?? 5,
        trust:    r.relTrust ?? 5,
        note:     r.relNote ?? '',
      })),
    goals: (n.arcGoals ?? [])
      .filter(g => (g.goalDescription ?? '').trim() !== '')
      .map(g => ({
        description: g.goalDescription ?? '',
        status:      g.goalStatus ?? 'active',
        progress:    g.goalProgress ?? 0,
      })),
  };
}

/**
 * Flatten the ability_scores paragraph into six numbers.
 *
 * Each ability is its own ability_score paragraph, so an unexposed or missing
 * one arrives as `{}` and reads as null rather than a score of zero.
 */
function abilityScores(raw: RawAbilityScores | null | undefined): DrupalAbilityScores {
  return {
    strength:     raw?.strength?.score ?? null,
    dexterity:    raw?.dexterity?.score ?? null,
    constitution: raw?.constitution?.score ?? null,
    intelligence: raw?.intelligence?.score ?? null,
    wisdom:       raw?.wisdom?.score ?? null,
    charisma:     raw?.charisma?.score ?? null,
  };
}

/**
 * Map the class paragraphs, dropping any whose class reference is empty.
 *
 * A paragraph with no classRef carries nothing worth showing — it is a half
 * filled row in Drupal, not a class the character has.
 */
function characterClasses(raw: RawClassParagraph[] | null | undefined): DrupalCharacterClass[] {
  return (raw ?? [])
    .filter((c): c is RawClassParagraph => Boolean(c?.classRef?.name))
    .map(c => ({
      name:     c.classRef?.name ?? '',
      subclass: c.subclassRef?.name ?? null,
      level:    c.level ?? null,
    }));
}

export interface RawCampaignOnCharacter {
  id: string;
  name: string;
}

/** One field_class paragraph as the console queries it. */
export interface RawClassParagraph {
  level?:       number | null;
  classRef?:    { name: string } | null;
  subclassRef?: { name: string } | null;
}

/** One ability_score paragraph, or `{}` when the reference is empty. */
export interface RawAbilityScoreItem {
  score?: number | null;
}

/** The ability_scores wrapper paragraph as the console queries it. */
export interface RawAbilityScores {
  strength?:     RawAbilityScoreItem | null;
  dexterity?:    RawAbilityScoreItem | null;
  constitution?: RawAbilityScoreItem | null;
  intelligence?: RawAbilityScoreItem | null;
  wisdom?:       RawAbilityScoreItem | null;
  charisma?:     RawAbilityScoreItem | null;
}

/** A taxonomy term as the console queries it: UUID plus label. */
export interface RawTermRef {
  id: string;
  name: string;
}

export interface RawCampaignTerm {
  id:               string;
  name:             string;
  campaignStatus:   string | null;
  currentParty:     Array<{ id: string; title: string }> | null;
  campaignOverview: { text: Array<{ processed: string }> | null } | null;
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
  imagePrompt?:      string | null;
  /* Everything below is optional: party.tsx mounts the same console from a
     narrower query and must keep type-checking. */
  lastName?:         string | null;
  gold?:             number | null;
  gender?:           string | null;
  abilityScores?:    RawAbilityScores | null;
  characterClasses?: RawClassParagraph[] | null;
  recurring?:        boolean | null;
  species?:          RawTermRef | null;
  lineage?:          RawTermRef | null;
  background?:       RawTermRef | null;
  languages?:        RawTermRef[] | null;
  skills?:           RawTermRef[] | null;
  tools?:            RawTermRef[] | null;
  faction?:          RawTermRef | null;
  keyTraits?:        RawTermRef[] | null;
  bonds?:            Array<{ value: string }> | null;
  ideals?:           Array<{ value: string }> | null;
  flaws?:            Array<{ value: string }> | null;
  personalityTraits?: Array<{ value: string }> | null;
  majorPlotActions?:  Array<{ value: string }> | null;
  specializedAbilities?: Array<{ value: string }> | null;
  plotHooks?:        Array<{ value: string }> | null;
  abilities?:        Array<{ value: string }> | null;
  /* Cardinality-1 text fields expose as a single object, not a list. */
  personality?:      { value: string } | null;
  notes?:            { value: string } | null;
  encounterTactics?: Array<{ value: string }> | null;
  defeatConditions?: Array<{ value: string }> | null;
  lairActions?:      Array<{ value: string }> | null;
  legendaryActions?: Array<{ value: string }> | null;
  regionalEffects?:  Array<{ value: string }> | null;
  aiEnabled?:        boolean | null;
  aiModel?:          string | null;
  aiTemperature?:    number | null;
  aiMaxTokens?:      number | null;
  aiSystemPrompt?:   { value: string } | null;
  voiceIdRef?:       { name: string } | null;
  voicePitch?:       number | null;
  voiceSpeed?:       number | null;
  arcDirection?:     string | null;
  arcStage?:         string | null;
  arcSummary?:       string | null;
  arcStories?:       number | null;
  arcUpdated?:       string | null;
  arcMetrics?:       Array<{
    metricKey?:       string | null;
    metricLabel?:     string | null;
    metricDirection?: string | null;
    metricSeries?:    string | null;
    metricObs?:       string | null;
  }> | null;
  arcRelationships?: Array<{
    relTarget?:   string | null;
    relType?:     string | null;
    relStrength?: number | null;
    relTrust?:    number | null;
    relNote?:     string | null;
  }> | null;
  arcGoals?: Array<{
    goalDescription?: string | null;
    goalStatus?:      string | null;
    goalProgress?:    number | null;
  }> | null;
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
  weaponCategory?:        { name: string } | null;
  weaponRange?:           { name: string } | null;
  itemProperties?:        Array<{ name: string; effectHtml: string | null }> | null;
  damage?:                string | null;
  itemBonus?:             number | null;
  itemCost?:              string | null;
  itemWeight?:            number | null;
  nonidentifiedName?:     string | null;
  armorCategory?:         string | null;
  armorAcBase?:           number | null;
  armorStrRequirement?:   number | null;
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
  storyArc?:   { id: string } | null;
  charactersPresent?: Array<{ id?: string } | null> | null;
}

interface RawArcPair {
  pairType?:   string | null;
  pairTier?:   number | null;
  pairNote?:   { processed?: string | null } | null;
  pairSource?: { id?: string; title?: string } | null;
  pairTarget?: { id?: string; title?: string } | null;
}

export interface RawStoryArc {
  id:             string;
  title:          string;
  path:           string | null;
  levelRange:     string | null;
  targetStories:  number | null;
  body?:          { processed?: string | null } | null;
  overallPlot?:   { processed?: string | null } | null;
  campaign?:      RawTermRef | null;
  faction?:       RawTermRef | null;
  party?:         Array<{ id?: string } | null> | null;
  npcs?:          Array<{ id?: string } | null> | null;
  arcPartyRelations?: Array<RawArcPair | null> | null;
  arcNpcRelations?:   Array<RawArcPair | null> | null;
}

export interface ConsoleQueryData {
  drupal: {
    nodeCharacters: { nodes: RawCharacter[] };
    nodeStories:    { nodes: RawStory[] };
    nodeStoryArcs?: { nodes: RawStoryArc[] } | null;
    termCampaigns:  { nodes: RawCampaignTerm[] };
    nodeMonsters?:  { nodes: RawMonster[] } | null;
  } | null;
  /* Items come from Gatsby sourceNodes (all pages, no 100-item cap) */
  allAllItem?: { nodes: RawItem[] } | null;
}

/** Collect the ids from an entity-reference list, dropping unresolved members. */
function idList(refs: Array<{ id?: string } | null> | null | undefined): string[] {
  return (refs ?? []).map(r => r?.id).filter((id): id is string => Boolean(id));
}

/**
 * Map arc_relationship_pair paragraphs into DrupalArcRelation.
 *
 * A pair missing either end is dropped: it cannot be shown from a character's
 * page, which is the whole reason both ends are stored as references.
 */
function arcRelations(pairs: Array<RawArcPair | null> | null | undefined): DrupalArcRelation[] {
  return (pairs ?? [])
    .filter((p): p is RawArcPair => Boolean(p?.pairSource?.id && p?.pairTarget?.id))
    .map(p => ({
      sourceId:   p.pairSource?.id ?? null,
      sourceName: p.pairSource?.title ?? null,
      targetId:   p.pairTarget?.id ?? null,
      targetName: p.pairTarget?.title ?? null,
      type:       p.pairType ?? null,
      tier:       p.pairTier ?? null,
      note:       htmlToText(p.pairNote?.processed ?? '') || null,
    }));
}

function splitCsv(s: string | null | undefined): string[] {
  if (!s) return [];
  return s.split(',').map(v => v.trim()).filter(Boolean);
}

export function buildConsoleData(data: ConsoleQueryData | null | undefined): ConsoleData {
  if (!data?.drupal) {
    return { campaigns: [], characters: [], stories: [], storyArcs: [], monsters: [], items: [] };
  }

  const characters: DrupalCharacter[] = data.drupal.nodeCharacters.nodes.map(n => {
    const classes = characterClasses(n.characterClasses);
    return {
      id:               n.id,
      title:            n.title,
      firstName:        n.firstName,
      lastName:         n.lastName ?? null,
      nickname:         n.nickname,
      level:            n.level,
      armorClass:       n.armorClass,
      maximumHitpoints: n.maximumHitpoints,
      movementSpeed:    n.movementSpeed,
      proficiencyBonus: n.proficiencyBonus,
      gold:             n.gold ?? null,
      abilityScores:    abilityScores(n.abilityScores),
      pronouns:         n.pronouns,
      gender:           n.gender ?? null,
      role:             n.role,
      characterClass:   classes.length > 0 ? classes[0].name : null,
      classes,
      characterType:    n.characterType,
      sourceCharacter:  n.sourceCharacter,
      recurring:        n.recurring ?? null,
      campaign:         n.campaign?.name ?? null,
      campaignId:       n.campaign?.id ?? null,
      path:             n.path,
      imageUrl:         n.image?.mediaImage?.url ?? null,
      imagePrompt:      n.imagePrompt ?? null,
      species:          n.species?.name ?? null,
      speciesId:        n.species?.id ?? null,
      lineage:          n.lineage?.name ?? null,
      lineageId:        n.lineage?.id ?? null,
      background:       n.background?.name ?? null,
      backgroundId:     n.background?.id ?? null,
      languages:        termRefs(n.languages),
      skills:           termRefs(n.skills),
      tools:            termRefs(n.tools),
      faction:          n.faction?.name ?? null,
      factionId:        n.faction?.id ?? null,
      keyTraits:        termRefs(n.keyTraits),
      bonds:            textValues(n.bonds),
      ideals:           textValues(n.ideals),
      flaws:            textValues(n.flaws),
      personalityTraits: textValues(n.personalityTraits),
      majorPlotActions:  textValues(n.majorPlotActions),
      specializedAbilities: textValues(n.specializedAbilities),
      plotHooks:        textValues(n.plotHooks),
      abilities:        textValues(n.abilities),
      personality:      htmlToText(n.personality?.value),
      notes:            htmlToText(n.notes?.value),
      encounterTactics: textValues(n.encounterTactics),
      defeatConditions: textValues(n.defeatConditions),
      lairActions:      textValues(n.lairActions),
      legendaryActions: textValues(n.legendaryActions),
      regionalEffects:  textValues(n.regionalEffects),
      aiEnabled:        n.aiEnabled ?? null,
      aiModel:          n.aiModel ?? null,
      aiTemperature:    n.aiTemperature ?? null,
      aiMaxTokens:      n.aiMaxTokens ?? null,
      aiSystemPrompt:   htmlToText(n.aiSystemPrompt?.value),
      voiceId:          n.voiceIdRef?.name ?? null,
      voicePitch:       n.voicePitch ?? null,
      voiceSpeed:       n.voiceSpeed ?? null,
      arc:              buildCharacterArc(n),
    };
  });

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
      storyArcId:  n.storyArc?.id ?? null,
      charactersPresentIds: idList(n.charactersPresent),
    }));

  const storyArcs: DrupalStoryArc[] = (data.drupal.nodeStoryArcs?.nodes ?? []).map(n => ({
    id:             n.id,
    title:          n.title,
    path:           n.path,
    campaign:       n.campaign?.name ?? null,
    campaignId:     n.campaign?.id ?? null,
    body:           htmlToText(n.body?.processed ?? '') || null,
    overallPlot:    htmlToText(n.overallPlot?.processed ?? '') || null,
    levelRange:     n.levelRange,
    targetStories:  n.targetStories,
    faction:        n.faction?.name ?? null,
    factionId:      n.faction?.id ?? null,
    partyIds:       idList(n.party),
    npcIds:         idList(n.npcs),
    partyRelations: arcRelations(n.arcPartyRelations),
    npcRelations:   arcRelations(n.arcNpcRelations),
  }));

  /* Build campaign map — primary source is the direct termCampaigns query
     so campaigns without stories or characters are always included. */
  const campaignMap = new Map<string, DrupalCampaign>();

  for (const c of data.drupal.termCampaigns.nodes) {
    campaignMap.set(c.name, {
      id:               c.id,
      name:             c.name,
      campaignStatus:   c.campaignStatus,
      currentPartyIds:  (c.currentParty ?? []).map(m => m.id),
      campaignOverview: c.campaignOverview?.text?.[0]?.processed ?? null,
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
    descriptionHtml:        n.descriptionHtml ?? null,
    vestigeLevel:           n.vestigeLevel?.name ?? null,
    damageTypes:            (n.damageTypes ?? []).map(t => t.name),
    weaponProperties:       (n.weaponProperties ?? []).map(t => t.name),
    weaponMastery:          (n.weaponMastery ?? []).map(t => t.name),
    weaponCategory:         n.weaponCategory?.name ?? null,
    weaponRange:            n.weaponRange?.name ?? null,
    itemProperties:         n.itemProperties ?? [],
    path:                   n.path ?? null,
    imageUrl:               n.image?.mediaImage?.url ?? null,
  }));

  return {
    campaigns: Array.from(campaignMap.values()),
    characters,
    stories,
    storyArcs,
    monsters,
    items,
  };
}
