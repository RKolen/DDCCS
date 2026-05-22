/**
 * Current Party — standalone Gatsby route
 * Route: /party/
 *
 * Mounts the StatelyLedger console with the characters section active.
 * Shares the same Drupal query + transform as index.tsx via buildConsoleData.
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
import { buildConsoleData } from '../utils/buildConsoleData';
import type { ConsoleQueryData } from '../utils/buildConsoleData';

const PartyPage: React.FC<PageProps<ConsoleQueryData>> = ({ data }) => (
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
      termCampaigns(first: 50) {
        nodes {
          id name campaignStatus
          currentParty { ... on Drupal_NodeCharacter { id title } }
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
