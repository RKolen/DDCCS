/**
 * /spells/ — the Spell Compendium index.
 *
 * Level-grouped index over Drupal spell nodes, including school when the
 * `spell_schools` term is set. Detail pages are built in gatsby-node
 * from each node's path (`/spells/{title}`).
 */

import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { schoolName } from '../types/spell';
import * as styles from './spells.module.css';

// -- Types ---------------------------------------------------------------------

interface SpellNode {
  id:              string;
  title:           string;
  path:            string | null;
  spellLevel:      number;
  castingTime:     string | null;
  spellRange:      string | null;
  concentration:   boolean | null;
  ritual:          boolean | null;
  spellSchool:     { name: string | null } | null;
}

interface SpellsData {
  drupal: {
    nodeSpells: { nodes: SpellNode[] };
  };
}

// -- Grouping ------------------------------------------------------------------

interface LevelGroup {
  level:  number;
  spells: SpellNode[];
}

function groupByLevel(nodes: SpellNode[]): LevelGroup[] {
  const map = new Map<number, SpellNode[]>();

  for (const node of nodes) {
    const existing = map.get(node.spellLevel);
    if (existing) {
      existing.push(node);
    } else {
      map.set(node.spellLevel, [node]);
    }
  }

  return Array.from(map.entries())
    .sort(([a], [b]) => a - b)
    .map(([level, spells]) => ({
      level,
      spells: spells.slice().sort((a, b) => a.title.localeCompare(b.title)),
    }));
}

function levelLabel(level: number): string {
  if (level === 0) return 'Cantrips';
  return `Level ${String(level)}`;
}

/** Casting time and range, with the ritual/concentration flags Drupal carries. */
function spellMeta(spell: SpellNode): string {
  const parts: string[] = [];
  const school = schoolName(spell.spellSchool);
  if (school !== null) parts.push(school);
  if (spell.castingTime !== null && spell.castingTime !== '') parts.push(spell.castingTime);
  if (spell.spellRange !== null && spell.spellRange !== '')   parts.push(spell.spellRange);
  if (spell.concentration === true) parts.push('concentration');
  if (spell.ritual === true)        parts.push('ritual');
  return parts.join(' · ');
}

// -- Spell card ----------------------------------------------------------------

function SpellCard({ spell }: { spell: SpellNode }): React.ReactElement {
  const meta = spellMeta(spell);
  const body = (
    <>
      <h3 className={styles.spellName}>{spell.title}</h3>
      {meta !== '' && <p className={styles.spellMeta}>{meta}</p>}
    </>
  );

  if (spell.path === null || spell.path === '') {
    return <div className={styles.spell}>{body}</div>;
  }
  return <Link to={spell.path} className={styles.spell}>{body}</Link>;
}

// -- Page ----------------------------------------------------------------------

const SpellsPage: React.FC<PageProps<SpellsData>> = ({ data, location }) => {
  const spellNodes = data.drupal.nodeSpells.nodes;
  const groups     = groupByLevel(spellNodes);

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>
        <header className={styles.pageHeader}>
          <h1 className={styles.heading}>Spell Compendium</h1>
          <p className={styles.subtitle}>
            {spellNodes.length > 0
              ? `${String(spellNodes.length)} spells recorded`
              : 'Nothing recorded yet.'}
          </p>
        </header>

        {groups.length > 0 ? (
          groups.map(group => (
            <section key={group.level} className={styles.group}>
              <h2 className={styles.groupHeading}>{levelLabel(group.level)}</h2>
              <div className={styles.grid}>
                {group.spells.map(spell => (
                  <SpellCard key={spell.id} spell={spell} />
                ))}
              </div>
            </section>
          ))
        ) : (
          <p className={styles.empty}>
            No spells in Drupal yet. Create Spell nodes in the CMS and they will
            appear here on the next build.
          </p>
        )}
      </div>
    </BaseTemplate>
  );
};

// -- GraphQL query -------------------------------------------------------------

export const query = graphql`
  query SpellCompendium {
    drupal {
      nodeSpells(first: 100) {
        nodes {
          id
          title
          path
          spellLevel
          castingTime
          spellRange
          concentration
          ritual
          spellSchool { ... on Drupal_TermSpellSchool { name } }
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Spells | D&amp;D Consultant</title>;

export default SpellsPage;
