/**
 * monster.tsx — individual monster stat block page.
 * Route: each nodeMonster's Drupal path (e.g. /monster/glimmer).
 *
 * Layout mirrors the character sheet: portrait hero, vitals strip,
 * two-column body (narrative left / mechanics right).
 *
 * Design reference: /project/Monster Stat Block.html
 */

import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Portrait } from '../components/atoms/Portrait';
import { ImageLightbox } from '../components/atoms/ImageLightbox';
import * as styles from './monster.module.css';

/* ────────────────────────────────────────────────────────────
   GraphQL response shape
   ──────────────────────────────────────────────────────────── */

interface RelationshipParagraph {
  relationshipDescription: string | null;
  relationshipType:        string | null;
  relationshipStrength:    number | null;
  relatedCharacter:        { title: string; path: string | null } | null;
}

interface MonsterPageData {
  drupal: {
    node: {
      __typename: 'Drupal_NodeMonster';
      id:                     string;
      title:                  string;
      challengeRating:        number | null;
      monsterSize:            string | null;
      monsterAlignment:       string | null;
      monsterSpeed:           string | null;
      monsterHitDice:         string | null;
      monsterXp:              number | null;
      monsterDamageResistances: string | null;
      monsterDamageImmunities:  string | null;
      monsterSenses:          string | null;
      monsterLanguages:       string | null;
      monsterSkills:          string | null;
      maximumHitpoints:       number | null;
      armorClass:             number | null;
      movementSpeed:          number | null;
      monsterTraits:          { processed: string } | null;
      monsterActions:         { processed: string } | null;
      monsterBonusActions:    { processed: string } | null;
      monsterReactions:       { processed: string } | null;
      monsterLegendaryActions: { processed: string } | null;
      monsterLairActions:     { processed: string } | null;
      specializedAbilities:   Array<{ processed: string }> | null;
      relationships:          RelationshipParagraph[] | null;
      type:                   { name: string } | null;
      faction:                { name: string } | null;
      path:                   string | null;
      image:                  { mediaImage: { url: string; alt: string } | null } | null;
    } | null;
  } | null;
}

/* ────────────────────────────────────────────────────────────
   Helpers
   ──────────────────────────────────────────────────────────── */

function crTierColor(cr: number | null): string {
  if (cr == null) return 'var(--color-neutral)';
  if (cr >= 17)   return 'var(--color-danger)';
  if (cr >= 11)   return 'var(--color-warning)';
  if (cr >= 5)    return 'var(--color-info)';
  return 'var(--color-success)';
}

function profBonusForCr(cr: number | null): number | null {
  if (cr == null) return null;
  return Math.ceil(Math.max(1, cr) / 4) + 1;
}

/* ────────────────────────────────────────────────────────────
   Sub-components
   ──────────────────────────────────────────────────────────── */

function RichPanel({ title, html, accent }: { title: string; html: string; accent?: string }): React.ReactElement {
  return (
    <section
      className={`${styles.panel} ${
        accent === 'legendary' ? styles.panelLegendary :
        accent === 'lair'      ? styles.panelLair : ''
      }`}
    >
      <h2 className={styles.panelTitle}>{title}</h2>
      <div className={styles.richText} dangerouslySetInnerHTML={{ __html: html }} />
    </section>
  );
}

function DefensesPanel({ m }: { m: NonNullable<MonsterPageData['drupal']>['node'] }): React.ReactElement | null {
  if (!m) return null;
  const rows = [
    { label: 'Skills',      val: m.monsterSkills },
    { label: 'Resistances', val: m.monsterDamageResistances },
    { label: 'Immunities',  val: m.monsterDamageImmunities },
    { label: 'Senses',      val: m.monsterSenses },
    { label: 'Languages',   val: m.monsterLanguages },
  ].filter(r => r.val != null);

  if (rows.length === 0) return null;

  return (
    <section className={styles.panel}>
      <h2 className={styles.panelTitle}>Defenses &amp; Senses</h2>
      {rows.map(r => (
        <div key={r.label} className={styles.propRow}>
          <span className={styles.propLabel}>{r.label}</span>
          <span className={styles.propVal}>{r.val}</span>
        </div>
      ))}
    </section>
  );
}

/* ────────────────────────────────────────────────────────────
   Page
   ──────────────────────────────────────────────────────────── */

type MonsterPageProps = PageProps<MonsterPageData>;

const MonsterPage: React.FC<MonsterPageProps> = ({ data, location }) => {
  const m = data?.drupal?.node ?? null;
  const [lightboxOpen, setLightboxOpen] = React.useState(false);

  if (!m) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p style={{ padding: '40px', color: 'var(--color-text-secondary)' }}>Monster not found.</p>
      </BaseTemplate>
    );
  }

  const imageUrl   = m.image?.mediaImage?.url ?? null;
  const tierColor  = crTierColor(m.challengeRating);
  const profBonus  = profBonusForCr(m.challengeRating);
  const typeName   = m.type?.name ?? null;
  const faction    = m.faction?.name ?? null;
  const speedText  = m.monsterSpeed ?? (m.movementSpeed != null ? `${m.movementSpeed} ft` : null);
  const hasLeg     = m.monsterLegendaryActions?.processed != null;
  const hasLair    = m.monsterLairActions?.processed != null;

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>

        {/* ── Hero ── */}
        <header className={styles.hero}>
          <div
            onClick={imageUrl ? () => setLightboxOpen(true) : undefined}
            style={imageUrl ? { cursor: 'zoom-in' } : undefined}
          >
            <Portrait
              name={m.title}
              size={120}
              imageUrl={imageUrl}
              className={styles.heroPortrait}
            />
          </div>

          {lightboxOpen && imageUrl && (
            <ImageLightbox src={imageUrl} alt={m.title} onClose={() => setLightboxOpen(false)} />
          )}

          <div className={styles.heroBody}>
            <div className={styles.heroTop}>
              <h1 className={styles.name}>{m.title}</h1>
            </div>

            <p className={styles.pronouns}>
              {[m.monsterSize, typeName, m.monsterAlignment].filter(Boolean).join(' · ')}
            </p>

            <div className={styles.heroBadges}>
              {typeName != null && <span className={styles.typeBadge}>{typeName}</span>}
              {faction   != null && <span className={styles.factionBadge}>{faction}</span>}
            </div>

            {/* Vitals strip */}
            <div className={styles.vitalsStrip}>
              {m.maximumHitpoints != null && (
                <div className={`${styles.vital} ${styles.vitalHp}`}>
                  <span className={styles.vitalLabel}>HP</span>
                  <span className={styles.vitalVal}>{m.maximumHitpoints}</span>
                </div>
              )}
              {m.armorClass != null && (
                <div className={`${styles.vital} ${styles.vitalAc}`}>
                  <span className={styles.vitalLabel}>AC</span>
                  <span className={styles.vitalVal}>{m.armorClass}</span>
                </div>
              )}
              {profBonus != null && (
                <div className={styles.vital}>
                  <span className={styles.vitalLabel}>Prof</span>
                  <span className={styles.vitalVal}>+{profBonus}</span>
                </div>
              )}
              {speedText != null && (
                <div className={styles.vital}>
                  <span className={styles.vitalLabel}>Speed</span>
                  <span className={styles.vitalVal} style={{ fontSize: 'var(--text-sm)' }}>{speedText}</span>
                </div>
              )}
              {m.challengeRating != null && (
                <div className={`${styles.vital} ${styles.vitalCr}`}>
                  <span className={styles.vitalLabel}>CR</span>
                  <span className={styles.vitalVal} style={{ color: tierColor }}>{m.challengeRating}</span>
                </div>
              )}
              {m.monsterXp != null && (
                <div className={styles.vital}>
                  <span className={styles.vitalLabel}>XP</span>
                  <span className={styles.vitalVal} style={{ fontSize: 'var(--text-sm)' }}>{m.monsterXp.toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>

          <a href="/monsters/" className={styles.backLink}>All Monsters</a>
        </header>

        <div className={styles.divider} />

        {/* ── Two-column body ── */}
        <div className={styles.mainGrid}>

          {/* Left — combat text + relationships */}
          <div className={styles.leftCol}>
            {m.monsterTraits?.processed      != null && <RichPanel title="Traits"        html={m.monsterTraits.processed} />}
            {m.monsterActions?.processed     != null && <RichPanel title="Actions"       html={m.monsterActions.processed} />}
            {m.monsterBonusActions?.processed != null && <RichPanel title="Bonus Actions" html={m.monsterBonusActions.processed} />}
            {m.monsterReactions?.processed   != null && <RichPanel title="Reactions"     html={m.monsterReactions.processed} />}

            {/* Relationships */}
            {m.relationships != null && m.relationships.length > 0 && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Relationships</h2>
                {m.relationships.map((rel, i) => (
                  <div key={i} className={styles.relCard}>
                    <div style={{ display: 'flex', alignItems: 'baseline', flexWrap: 'wrap' }}>
                      {rel.relatedCharacter != null ? (
                        <a href={rel.relatedCharacter.path ?? '#'} className={styles.relName}>
                          {rel.relatedCharacter.title}
                        </a>
                      ) : null}
                      {rel.relationshipType != null && (
                        <span className={styles.relType}>{rel.relationshipType}</span>
                      )}
                      {rel.relationshipStrength != null && (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--color-text-disabled)', marginLeft: 8 }}>
                          strength {rel.relationshipStrength}
                        </span>
                      )}
                    </div>
                    {rel.relationshipDescription != null && (
                      <p className={styles.relDesc}>{rel.relationshipDescription}</p>
                    )}
                  </div>
                ))}
              </section>
            )}
          </div>

          {/* Right — defenses + special abilities + boss mechanics */}
          <div className={styles.rightCol}>
            <DefensesPanel m={m} />

            {/* Special Abilities */}
            {m.specializedAbilities != null && m.specializedAbilities.length > 0 && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Special Abilities</h2>
                {m.specializedAbilities.map((sa, i) => (
                  <div key={i} className={styles.richText} dangerouslySetInnerHTML={{ __html: sa.processed }} />
                ))}
              </section>
            )}

            {hasLeg && <RichPanel title="Legendary Actions" html={m.monsterLegendaryActions!.processed} accent="legendary" />}
            {hasLair && <RichPanel title="Lair Actions"     html={m.monsterLairActions!.processed}      accent="lair" />}

            {!hasLeg && !hasLair && m.specializedAbilities == null && (
              <section className={styles.panel}>
                <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 14, color: 'var(--color-text-disabled)', margin: 0, textAlign: 'center' }}>
                  Standard creature — no legendary or lair mechanics.
                </p>
              </section>
            )}
          </div>
        </div>
      </div>
    </BaseTemplate>
  );
};

/* ────────────────────────────────────────────────────────────
   GraphQL query
   ──────────────────────────────────────────────────────────── */

export const query = graphql`
  query MonsterPage($id: ID!) {
    drupal {
      node(id: $id) {
        __typename
        ... on Drupal_NodeMonster {
          id title path
          challengeRating monsterSize monsterAlignment monsterSpeed
          monsterHitDice monsterXp maximumHitpoints armorClass movementSpeed
          monsterDamageResistances monsterDamageImmunities
          monsterSenses monsterLanguages monsterSkills
          monsterTraits           { processed }
          monsterActions          { processed }
          monsterBonusActions     { processed }
          monsterReactions        { processed }
          monsterLegendaryActions { processed }
          monsterLairActions      { processed }
          specializedAbilities    { processed }
          relationships {
            ... on Drupal_ParagraphRelationship {
              relationshipDescription
              relationshipType
              relationshipStrength
              relatedCharacter {
                ... on Drupal_NodeCharacter { title path }
              }
            }
          }
          type    { ... on Drupal_TermCreatureType { name } }
          faction { ... on Drupal_TermFaction      { name } }
          image   { ... on Drupal_MediaImage       { mediaImage { url alt } } }
        }
      }
    }
  }
`;

export const Head: HeadFC<MonsterPageData> = ({ data }) => (
  <title>{data?.drupal?.node?.title ?? 'Monster'} | D&amp;D Consultant</title>
);

export default MonsterPage;
