import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { MonsterRoster, type MonsterRosterData } from '../components/organisms/MonsterRoster';

const MonstersPage: React.FC<PageProps<MonsterRosterData>> = ({ data, location }) => (
  <BaseTemplate currentPath={location.pathname}>
    <MonsterRoster data={data} />
  </BaseTemplate>
);

export const query = graphql`
  query MonstersList {
    drupal {
      nodeMonsters(first: 100) {
        nodes {
          id title challengeRating monsterSize monsterAlignment path
          type  { ... on Drupal_TermCreatureType { name } }
          image { ... on Drupal_MediaImage { mediaImage { url alt } } }
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Bestiary | D&amp;D Consultant</title>;

export default MonstersPage;
