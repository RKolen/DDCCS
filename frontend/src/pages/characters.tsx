import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { CharacterRoster } from '../components/organisms/CharacterRoster';
import type { RosterData } from '../components/organisms/CharacterRoster';

const CharactersPage: React.FC<PageProps<RosterData>> = ({ data, location }) => (
  <BaseTemplate currentPath={location.pathname}>
    <CharacterRoster data={data} isNpc={false} />
  </BaseTemplate>
);

export const query = graphql`
  query CharactersList {
    drupal {
      nodeCharacters(first: 100) {
        nodes {
          id title firstName nickname pronouns
          characterType sourceCharacter role
          level armorClass maximumHitpoints path
          campaign { ... on Drupal_TermCampaign { name } }
          image { ... on Drupal_MediaImage { mediaImage { url alt } } }
        }
      }
      nodeStories(first: 100) {
        nodes {
          campaign {
            ... on Drupal_TermCampaign {
              id name
              currentParty { ... on Drupal_NodeCharacter { id } }
            }
          }
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Characters | D&amp;D Consultant</title>;

export default CharactersPage;
