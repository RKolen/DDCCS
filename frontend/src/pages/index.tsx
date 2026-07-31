/**
 * Homepage — DDCCS Campaign Console
 * Route: /
 *
 * Query includes rich character profile fields for story generation:
 * personalityTraits, bonds, ideals, flaws, majorPlotActions are text fields
 * (already enabled). species/lineage/background reference taxonomy terms enabled
 * via entity_config.taxonomy_term in graphql_compose settings (requires ddev drush cim).
 * The `class` paragraph field is intentionally omitted — graphql-js's tagged-template
 * parser rejects `class` as a fragment field name, cascading all other queries to fail.
 */

import * as React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { MENU_DATA } from '../components/console/menuData';
import type { MenuSection } from '../components/console/menuData';
import { StatelyLedger } from '../components/console/StatelyLedger';
import { buildConsoleData } from '../utils/buildConsoleData';
import type { ConsoleQueryData } from '../utils/buildConsoleData';

/* ────────────────────────────────────────────────────────────
   Deep links
   ──────────────────────────────────────────────────────────── */

/**
 * Where a `/?section=…&item=…&char=…` link should open the console.
 *
 * Character and NPC pages link here to reach the profile editor. The section
 * and item are validated against the menu rather than trusted, so a stale or
 * hand-edited link falls back to the default landing screen instead of
 * rendering the "missing screen" placeholder.
 */
function deepLink(search: string): {
  section?: MenuSection['id'];
  item?: string;
  charId?: string;
} {
  const params  = new URLSearchParams(search);
  const wanted  = params.get('section');
  const section = MENU_DATA.sections.find(s => s.id === wanted);
  if (section == null) {
    return {};
  }
  const itemId = params.get('item');
  const item   = section.items.find(i => i.id === itemId);
  return {
    section: section.id,
    item:    item?.id,
    charId:  params.get('char') ?? undefined,
  };
}

/* ────────────────────────────────────────────────────────────
   Page
   ──────────────────────────────────────────────────────────── */

const IndexPage: React.FC<PageProps<ConsoleQueryData>> = ({ data, location }) => {
  const link = deepLink(location.search);
  return (
    <StatelyLedger
      fullscreen
      /* Keys on the link so a second navigation from a character page remounts
         the console on the newly named character rather than keeping the
         selection the first link established. */
      key={`${link.section ?? ''}:${link.item ?? ''}:${link.charId ?? ''}`}
      initialSection={link.section}
      initialItem={link.item}
      initialCharId={link.charId}
      liveData={buildConsoleData(data)}
    />
  );
};

/* ────────────────────────────────────────────────────────────
   GraphQL query
   Field provenance:
     Confirmed in characters.tsx   → id, title, firstName, level, armorClass,
                                     maximumHitpoints, path, campaign.name, image
     Confirmed in character.tsx    → nickname, movementSpeed, proficiencyBonus
     Confirmed in npcs.tsx         → characterType, role
     Confirmed in campaign-reader  → storyNumber, sessionDate, campaign.currentParty
     Confirmed in stories.tsx      → storyNumber, campaign.name
     Enabled in graphql_compose,
       not yet in a working query  → pronouns, species, background, campaignStatus
     Pending Drupal config import  → characterClasses (field_class renamed via
       name_sdl to avoid JS `class` keyword; also needs taxonomy_term.class
       enabled in graphql_compose settings). Re-add after `ddev drush cim`.
   ──────────────────────────────────────────────────────────── */

export const query = graphql`
  query ConsoleData {
    drupal {
      nodeCharacters(first: 100) {
        nodes {
          id
          title
          firstName
          lastName
          nickname
          level
          armorClass
          maximumHitpoints
          movementSpeed
          proficiencyBonus
          gold
          pronouns
          gender
          characterType
          sourceCharacter
          recurring
          role
          path
          campaign {
            ... on Drupal_TermCampaign {
              id
              name
            }
          }
          image {
            ... on Drupal_MediaImage {
              mediaImage { url alt }
            }
          }
          imagePrompt
          species    { ... on Drupal_TermSpecies     { id name } }
          lineage    { ... on Drupal_TermLineage     { id name } }
          background { ... on Drupal_TermBackground  { id name } }
          languages  { ... on Drupal_TermLanguage    { id name } }
          skills     { ... on Drupal_TermSkill       { id name } }
          tools      { ... on Drupal_TermToolProfiency { id name } }
          personalityTraits { value }
          bonds             { value }
          ideals            { value }
          flaws             { value }
          majorPlotActions  { value }
          specializedAbilities { value }
          plotHooks         { value }
          abilities         { value }
          personality       { value }
          notes             { value }
          encounterTactics  { value }
          defeatConditions  { value }
          lairActions       { value }
          legendaryActions  { value }
          regionalEffects   { value }
          aiEnabled
          aiModel
          aiTemperature
          aiMaxTokens
          aiSystemPrompt    { value }
          voiceIdRef { ... on Drupal_TermVoiceId { name } }
          voicePitch
          voiceSpeed
          arcDirection
          arcStage
          arcSummary
          arcStories
          arcUpdated
          arcMetrics {
            ... on Drupal_ParagraphArcMetric {
              metricKey metricLabel metricDirection metricSeries metricObs
            }
          }
          arcRelationships {
            ... on Drupal_ParagraphArcRelationship {
              relTarget relType relStrength relTrust relNote
            }
          }
          arcGoals {
            ... on Drupal_ParagraphArcGoal {
              goalDescription goalStatus goalProgress
            }
          }
        }
      }
      nodeStories(first: 100) {
        nodes {
          id title storyNumber path sessionDate
          campaign {
            ... on Drupal_TermCampaign {
              id name campaignStatus
              currentParty { ... on Drupal_NodeCharacter { id title } }
            }
          }
        }
      }
      termCampaigns(first: 50) {
        nodes {
          id
          name
          campaignStatus
          currentParty { ... on Drupal_NodeCharacter { id title } }
          campaignOverview {
            ... on Drupal_ParagraphWysiwyg { text { processed } }
          }
        }
      }
      nodeMonsters(first: 100) {
        nodes {
          id
          title
          challengeRating
          monsterSize
          monsterAlignment
          monsterSpeed
          monsterHitDice
          monsterXp
          monsterDamageResistances
          monsterDamageImmunities
          monsterSenses
          monsterLanguages
          monsterSkills
          maximumHitpoints
          armorClass
          movementSpeed
          path
          type    { ... on Drupal_TermCreatureType { name } }
          faction { ... on Drupal_TermFaction      { name } }
          image   { ... on Drupal_MediaImage        { mediaImage { url alt } } }
        }
      }
    }
    allAllItem {
      nodes {
        drupalId title path source
        itemType isMagic itemRarity itemRequiresAttunement
        damage itemBonus itemCost itemWeight
        nonidentifiedName armorCategory armorAcBase armorStrRequirement
        descriptionHtml
        edition       { name }
        vestigeLevel  { name }
        damageTypes   { name }
        weaponProperties { name }
        weaponMastery    { name }
        weaponSubtype    { name }
        itemProperties   { name effectHtml }
        image { mediaImage { url alt } }
      }
    }
  }
`;

export const Head: HeadFC = () => (
  <>
    <title>DDCCS · Campaign Console</title>
    <meta name="viewport" content="width=1440" />
  </>
);

export default IndexPage;
