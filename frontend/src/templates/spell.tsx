/**
 * spell.tsx — individual spell page.
 * Route: each node--spell's Drupal path alias (e.g. /spells/fireball).
 */

import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { SpellSheet } from '../components/molecules/SpellSheet';
import {
  type SpellRecord,
  flattenDescription,
  schoolName,
} from '../types/spell';
import * as styles from './spell.module.css';

interface SpellPageData {
  drupal: {
    node: {
      __typename: 'Drupal_NodeSpell';
      id: string;
      title: string;
      path: string | null;
      spellLevel: number;
      castingTime: string | null;
      spellRange: string | null;
      spellComponents: string | null;
      spellDuration: string | null;
      concentration: boolean | null;
      ritual: boolean | null;
      spellSchool: { name: string | null } | null;
      description: Array<{ text: Array<{ processed: string }> | null }> | null;
    } | null;
  } | null;
}

function toRecord(
  node: NonNullable<NonNullable<SpellPageData['drupal']>['node']>,
): SpellRecord {
  return {
    id: node.id,
    title: node.title,
    path: node.path,
    spellLevel: node.spellLevel,
    school: schoolName(node.spellSchool),
    castingTime: node.castingTime,
    spellRange: node.spellRange,
    spellComponents: node.spellComponents,
    spellDuration: node.spellDuration,
    concentration: node.concentration,
    ritual: node.ritual,
    descriptionHtml: flattenDescription(node.description),
  };
}

const SpellPage: React.FC<PageProps<SpellPageData>> = ({ data, location }) => {
  const node = data?.drupal?.node ?? null;

  if (node == null) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <div className={styles.page}>
          <p className={styles.missing}>Spell not found.</p>
        </div>
      </BaseTemplate>
    );
  }

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <Link to="/spells/" className={styles.backLink}>All Spells</Link>
        <SpellSheet spell={toRecord(node)} />
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query SpellPage($id: ID!) {
    drupal {
      node(id: $id) {
        __typename
        ... on Drupal_NodeSpell {
          id
          title
          path
          spellLevel
          castingTime
          spellRange
          spellComponents
          spellDuration
          concentration
          ritual
          spellSchool { ... on Drupal_TermSpellSchool { name } }
          description { ... on Drupal_ParagraphWysiwyg { text { processed } } }
        }
      }
    }
  }
`;

export const Head: HeadFC<SpellPageData> = ({ data }) => (
  <title>{data?.drupal?.node?.title ?? 'Spell'} | D&amp;D Consultant</title>
);

export default SpellPage;
