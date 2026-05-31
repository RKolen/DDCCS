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
import { StatelyLedger } from '../components/console/StatelyLedger';
import { buildConsoleData } from '../utils/buildConsoleData';
import type { ConsoleQueryData } from '../utils/buildConsoleData';

/* ────────────────────────────────────────────────────────────
   Page
   ──────────────────────────────────────────────────────────── */

const IndexPage: React.FC<PageProps<ConsoleQueryData>> = ({ data }) => (
  <StatelyLedger fullscreen liveData={buildConsoleData(data)} />
);

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
          nickname
          level
          armorClass
          maximumHitpoints
          movementSpeed
          proficiencyBonus
          pronouns
          characterType
          sourceCharacter
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
          species    { ... on Drupal_TermSpecies     { name } }
          lineage    { ... on Drupal_TermLineage     { name } }
          background { ... on Drupal_TermBackground  { name } }
          personalityTraits { value }
          bonds             { value }
          ideals            { value }
          flaws             { value }
          majorPlotActions  { value }
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
  }
`;

export const Head: HeadFC = () => (
  <>
    <title>DDCCS · Campaign Console</title>
    <meta name="viewport" content="width=1440" />
  </>
);

export default IndexPage;
