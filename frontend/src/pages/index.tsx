/**
 * Homepage — DDCCS Campaign Console
 * Route: /
 *
 * Query uses only fields confirmed working in existing pages, plus
 * pronouns/species/background/campaignStatus which are enabled in
 * graphql_compose settings. The `class` paragraph field is intentionally
 * omitted — graphql-js's tagged-template parser rejects `class` as a
 * fragment field name, cascading all other queries to fail.
 */

import * as React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { StatelyLedger } from '../components/console/StatelyLedger';
import type {
  ConsoleData, DrupalCampaign, DrupalCharacter, DrupalStory,
} from '../components/console/ConsoleContext';

/* ────────────────────────────────────────────────────────────
   Raw GraphQL types (1-to-1 with query below)
   ──────────────────────────────────────────────────────────── */

interface RawCampaignOnCharacter {
  id: string;
  name: string;
}

interface RawCampaignOnStory {
  id: string;
  name: string;
  campaignStatus: string | null;
  currentParty: Array<{ id: string; title: string }>;
}

interface RawCharacter {
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

interface RawStory {
  id: string;
  title: string;
  storyNumber: number | null;
  path: string | null;
  sessionDate: string | null;
  campaign: RawCampaignOnStory | null;
}

interface ConsoleQueryData {
  drupal: {
    nodeCharacters: { nodes: RawCharacter[] };
    nodeStories:    { nodes: RawStory[] };
  } | null;
}

/* ────────────────────────────────────────────────────────────
   Transform Drupal → ConsoleData
   ──────────────────────────────────────────────────────────── */

function buildConsoleData(data: ConsoleQueryData): ConsoleData {
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

  /*
   * Campaigns come from the story's TermCampaign reference —
   * the only place that gives us campaignStatus + currentParty
   * without a separate termCampaigns top-level query.
   */
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

  /* Fall back: campaigns that have characters but no stories yet */
  for (const c of data.drupal.nodeCharacters.nodes) {
    if (!c.campaign) continue;
    const { id, name } = c.campaign;
    if (!campaignMap.has(name)) {
      campaignMap.set(name, { id, name, campaignStatus: null });
    }
  }

  const campaigns: DrupalCampaign[] = Array.from(campaignMap.values());
  return { campaigns, characters, stories };
}

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
        }
      }
      nodeStories(first: 100) {
        nodes {
          id
          title
          storyNumber
          path
          sessionDate
          campaign {
            ... on Drupal_TermCampaign {
              id
              name
              campaignStatus
              currentParty {
                ... on Drupal_NodeCharacter {
                  id
                  title
                }
              }
            }
          }
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
