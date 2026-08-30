/**
 * /spells/ — the Spell Compendium index.
 *
 * Level-grouped index over Drupal spells-vocabulary terms, including school
 * when `field_spell_school` is set. Detail pages are built in gatsby-node
 * from each term's path (`/spells/{name}`).
 */

import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { schoolName } from '../types/spell';
import '../graphql/spellTerm';
import * as styles from './spells.module.css';

// -- Types ---------------------------------------------------------------------

interface SpellRow {
  id: string;
  name: string;
  path: string | null;
  spellLevel: number | null;
  spellCastingTime: string | null;
  spellRange: string | null;
  spellConcentration: boolean | null;
  spellRitual: boolean | null;
  spellSchool: { name: string | null } | null;
}

interface SpellsData {
  drupal: {
    termSpells: { nodes: SpellRow[] };
  };
}

// -- Grouping ------------------------------------------------------------------

interface LevelGroup {
  level:  number;
  spells: SpellRow[];
}

function groupByLevel(nodes: SpellRow[]): LevelGroup[] {
  const map = new Map<number, SpellRow[]>();

  for (const node of nodes) {
    const level = node.spellLevel ?? 0;
    const existing = map.get(level);
    if (existing) {
      existing.push(node);
    } else {
      map.set(level, [node]);
    }
  }

  return Array.from(map.entries())
    .sort(([a], [b]) => a - b)
    .map(([level, spells]) => ({
      level,
      spells: spells.slice().sort((a, b) => a.name.localeCompare(b.name)),
    }));
}

function levelLabel(level: number): string {
  if (level === 0) return 'Cantrips';
  return `Level ${String(level)}`;
}

/** Casting time and range, with the ritual/concentration flags Drupal carries. */
function spellMeta(spell: SpellRow): string {
  const parts: string[] = [];
  const school = schoolName(spell.spellSchool);
  if (school !== null) parts.push(school);
  if (spell.spellCastingTime !== null && spell.spellCastingTime !== '') {
    parts.push(spell.spellCastingTime);
  }
  if (spell.spellRange !== null && spell.spellRange !== '') {
    parts.push(spell.spellRange);
  }
  if (spell.spellConcentration === true) parts.push('concentration');
  if (spell.spellRitual === true) parts.push('ritual');
  return parts.join(' · ');
}

// -- Spell card ----------------------------------------------------------------

function SpellCard({ spell }: { spell: SpellRow }): React.ReactElement {
  const meta = spellMeta(spell);
  const body = (
    <>
      <h3 className={styles.spellName}>{spell.name}</h3>
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
  const spellNodes = data.drupal.termSpells.nodes;
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
            No spells in Drupal yet. Create spells-vocabulary terms in the CMS
            and they will appear here on the next build.
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
      termSpells(first: 500) {
        nodes {
          ...SpellTermFields
        }
      }
    }
  }
`;

export const Head: HeadFC = () => <title>Spells | D&amp;D Consultant</title>;

export default SpellsPage;
