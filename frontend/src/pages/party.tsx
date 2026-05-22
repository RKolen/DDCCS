/**
 * Current Party — standalone Gatsby route
 * Route: /party/
 *
 * Mounts the StatelyLedger console with the characters section active,
 * showing the party derived from the active campaign's currentPartyIds.
 *
 * Wiring note (HANDOFF §4c):
 *   When a `party` item is added to the characters section in menuData.ts,
 *   change initialItem from "list" to "party" to land on CurrentPartyScreen.
 *   Route already wired in ScreenRouter as `characters/party`.
 */

import * as React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { StatelyLedger } from '../components/console/StatelyLedger';
import type {
  ConsoleData, DrupalCampaign, DrupalCharacter, DrupalStory,
} from '../components/console/ConsoleContext';

/* ── Raw GraphQL types ── */

interface RawCampaignOnCharacter { id: string; name: string; }
interface RawCampaignOnStory {
  id: string; name: string;
  campaignStatus: string | null;
  currentParty: Array<{ id: string; title: string }>;
}

interface RawCharacter {
  id: string; title: string; firstName: string | null;
  nickname: string | null; level: number | null;
  armorClass: number | null; maximumHitpoints: number | null;
  movementSpeed: number | null; proficiencyBonus: number | null;
  pronouns: string | null; characterType: boolean | null;
  role: string | null; path: string | null;
  campaign: RawCampaignOnCharacter | null;
  image: { mediaImage: { url: string; alt: string } | null } | null;
}

interface RawStory {
  id: string; title: string; storyNumber: number | null;
  path: string | null; sessionDate: string | null;
  campaign: RawCampaignOnStory | null;
}

interface PartyQueryData {
  drupal: {
    nodeCharacters: { nodes: RawCharacter[] };
    nodeStories:    { nodes: RawStory[] };
  } | null;
}

/* ── Transform ── */

function buildConsoleData(data: PartyQueryData): ConsoleData {
  if (!data?.drupal) return { campaigns: [], characters: [], stories: [] };

  const characters: DrupalCharacter[] = data.drupal.nodeCharacters.nodes.map(n => ({
    id: n.id, title: n.title, nickname: n.nickname,
    level: n.level, armorClass: n.armorClass,
    maximumHitpoints: n.maximumHitpoints,
    movementSpeed: n.movementSpeed, proficiencyBonus: n.proficiencyBonus,
    pronouns: n.pronouns, role: n.role, characterClass: null,
    characterType: n.characterType,
    campaign: n.campaign?.name ?? null, campaignId: n.campaign?.id ?? null,
    path: n.path, imageUrl: n.image?.mediaImage?.url ?? null,
  }));

  const stories: DrupalStory[] = data.drupal.nodeStories.nodes
    .slice()
    .sort((a, b) => (a.storyNumber ?? 0) - (b.storyNumber ?? 0))
    .map(n => ({
      id: n.id, title: n.title, storyNumber: n.storyNumber,
      path: n.path, sessionDate: n.sessionDate,
      campaign: n.campaign?.name ?? null, campaignId: n.campaign?.id ?? null,
    }));

  const campaignMap = new Map<string, DrupalCampaign>();
  for (const s of data.drupal.nodeStories.nodes) {
    if (!s.campaign) continue;
    const { id, name, campaignStatus, currentParty } = s.campaign;
    if (!campaignMap.has(name)) {
      campaignMap.set(name, { id, name, campaignStatus, currentPartyIds: currentParty.map(m => m.id) });
    }
  }
  for (const c of data.drupal.nodeCharacters.nodes) {
    if (!c.campaign) continue;
    const { id, name } = c.campaign;
    if (!campaignMap.has(name)) {
      campaignMap.set(name, { id, name, campaignStatus: null });
    }
  }

  return { campaigns: Array.from(campaignMap.values()), characters, stories };
}

/* ── Page ── */

const PartyPage: React.FC<PageProps<PartyQueryData>> = ({ data }) => (
  <StatelyLedger
    fullscreen
    initialSection="characters"
    initialItem="list"
    liveData={buildConsoleData(data)}
  />
);

export const query = graphql`
  query PartyPageData {
    drupal {
      nodeCharacters(first: 100) {
        nodes {
          id title firstName nickname level armorClass
          maximumHitpoints movementSpeed proficiencyBonus
          pronouns characterType role path
          campaign { ... on Drupal_TermCampaign { id name } }
          image { ... on Drupal_MediaImage { mediaImage { url alt } } }
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
    }
  }
`;

export const Head: HeadFC = () => (
  <>
    <title>Current Party - DDCCS</title>
    <meta name="viewport" content="width=1440" />
  </>
);

export default PartyPage;
