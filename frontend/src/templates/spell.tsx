/**
 * spell.tsx — individual spell page.
 * Route: each spells-vocabulary term's Drupal path alias (e.g. /spells/fireball).
 */

import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { SpellSheet } from '../components/molecules/SpellSheet';
import {
  type SpellTermNode,
  spellTermToRecord,
} from '../types/spell';
import '../graphql/spellTerm';
import * as styles from './spell.module.css';

interface SpellPageData {
  drupal: {
    term: (SpellTermNode & { __typename: 'Drupal_TermSpell' }) | null;
  } | null;
}

const SpellPage: React.FC<PageProps<SpellPageData>> = ({ data, location }) => {
  const term = data?.drupal?.term ?? null;

  if (term == null) {
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
        <SpellSheet spell={spellTermToRecord(term)} />
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query SpellPage($id: ID!) {
    drupal {
      term(id: $id) {
        __typename
        ... on Drupal_TermSpell {
          ...SpellTermFields
        }
      }
    }
  }
`;

export const Head: HeadFC<SpellPageData> = ({ data }) => (
  <title>{data?.drupal?.term?.name ?? 'Spell'} | D&amp;D Consultant</title>
);

export default SpellPage;
