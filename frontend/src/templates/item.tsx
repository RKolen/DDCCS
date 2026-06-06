/**
 * item.tsx — individual item page.
 * Route: each node--item's Drupal path alias (e.g. /item/worldroot-girdle).
 *
 * Uses drupal.node(id: $drupalId) via gatsby-source-graphql since item nodes
 * are fetched by UUID from the drupal { } stitched schema.
 */

import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Portrait } from '../components/atoms/Portrait';
import { ImageLightbox } from '../components/atoms/ImageLightbox';
import * as styles from './item.module.css';

/* ────────────────────────────────────────────────────────────
   GraphQL response shape
   ──────────────────────────────────────────────────────────── */

interface ItemTerm { name: string }

interface ItemPageData {
  drupal: {
    node: {
      __typename: 'Drupal_NodeItem';
      id: string;
      title: string;
      path: string | null;
      source: string | null;
      itemType: string | null;
      isMagic: boolean | null;
      itemRarity: string | null;
      itemRequiresAttunement: boolean | null;
      damage: string | null;
      itemBonus: number | null;
      itemCost: string | null;
      itemWeight: number | null;
      nonidentifiedName: string | null;
      armorCategory: string | null;
      armorAcBase: number | null;
      armorStrRequirement: number | null;
      notes: { processed: string } | null;
      description: Array<{ text: Array<{ processed: string }> }> | null;
      edition: ItemTerm | null;
      vestigeLevel: ItemTerm | null;
      damageTypes: ItemTerm[] | null;
      weaponProperties: ItemTerm[] | null;
      weaponMastery: ItemTerm[] | null;
      weaponSubtype: ItemTerm[] | null;
      itemProperties: Array<{
        name: string;
        effect: Array<{ text: Array<{ processed: string }> }> | null;
      }> | null;
      image: { mediaImage: { url: string; alt: string } | null } | null;
    } | null;
  } | null;
}

/* ────────────────────────────────────────────────────────────
   Helpers
   ──────────────────────────────────────────────────────────── */

import { rarityColor } from '../utils/rarityColor';

function isHomebrew(item: ItemPageData['drupal']): boolean {
  const node = item?.node;
  if (!node) return true;
  const edition = node.edition?.name ?? '';
  return !edition || edition.toLowerCase() === 'homebrew';
}

/* ────────────────────────────────────────────────────────────
   Page
   ──────────────────────────────────────────────────────────── */

type ItemPageProps = PageProps<ItemPageData>;

const ItemPage: React.FC<ItemPageProps> = ({ data, location }) => {
  const item = data?.drupal?.node ?? null;
  const [lightboxOpen, setLightboxOpen] = React.useState(false);

  if (!item) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <div style={{ padding: '48px 32px', textAlign: 'center' }}>
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
            Item not found.
          </p>
        </div>
      </BaseTemplate>
    );
  }

  const imageUrl = item.image?.mediaImage?.url ?? null;
  const rarity = rarityColor(item.itemRarity);
  const homebrew = isHomebrew(data?.drupal);
  const editionName = item.edition?.name ?? (homebrew ? 'Homebrew' : 'Official');

  /* Flatten description paragraphs */
  const descriptionHtml = item.description
    ?.flatMap(d => d.text ?? [])
    .map(t => t.processed ?? '')
    .filter(Boolean)
    .join('') || null;

  const notesHtml = item.notes?.processed ?? null;

  /* Magical property effects — each itemProperty has a name + HTML effect block */
  const magicalProps = (item.itemProperties ?? []).map(p => ({
    name: p.name,
    effectHtml: (p.effect ?? [])
      .flatMap(e => e.text ?? [])
      .map(t => t.processed ?? '')
      .filter(Boolean)
      .join('') || null,
  }));

  const stats: Array<{ label: string; value: string; accent?: string }> = [
    item.weaponSubtype?.length ? { label: 'Class', value: item.weaponSubtype.map(t => t.name).join(', ') } : null,
    item.damage != null ? { label: 'Damage', value: item.damage + (item.damageTypes?.length ? ` ${item.damageTypes.map(t => t.name).join('/')}` : '') } : null,
    item.armorAcBase != null ? { label: 'AC', value: `${item.armorAcBase}${item.armorCategory ? ` (${item.armorCategory})` : ''}` } : null,
    item.itemBonus != null ? { label: 'Bonus', value: `+${item.itemBonus}` } : null,
    item.armorStrRequirement != null ? { label: 'Str req', value: `${item.armorStrRequirement}` } : null,
    item.itemCost != null ? { label: 'Cost', value: item.itemCost } : null,
    item.itemWeight != null ? { label: 'Weight', value: `${item.itemWeight} lb` } : null,
    item.weaponMastery?.length ? { label: 'Mastery', value: item.weaponMastery.map(t => t.name).join(', ') } : null,
    item.weaponProperties?.length ? { label: 'Properties', value: item.weaponProperties.map(t => t.name).join(', ') } : null,
    item.itemRequiresAttunement ? { label: 'Attunement', value: 'Required', accent: 'var(--color-warning)' } : null,
    item.vestigeLevel != null && item.itemRarity?.toLowerCase() === 'vestige' ? { label: 'Vestige state', value: item.vestigeLevel.name } : null,
  ].filter((s): s is NonNullable<typeof s> => s !== null);

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>

        {/* Hero */}
        <header className={styles.hero}>
          <div
            onClick={imageUrl ? () => setLightboxOpen(true) : undefined}
            style={imageUrl ? { cursor: 'zoom-in' } : undefined}
          >
            <Portrait
              name={item.title}
              size={120}
              imageUrl={imageUrl}
              className={styles.heroPortrait}
            />
          </div>

          {lightboxOpen && imageUrl && (
            <ImageLightbox src={imageUrl} alt={item.title} onClose={() => setLightboxOpen(false)} />
          )}

          <div className={styles.heroBody}>
            <div className={styles.heroTop}>
              <h1 className={styles.name}>{item.title}</h1>
            </div>

            {item.nonidentifiedName != null && item.nonidentifiedName !== '' && (
              <p className={styles.pronouns}>&ldquo;{item.nonidentifiedName}&rdquo;</p>
            )}

            <p className={styles.pronouns}>
              {[item.itemType, item.itemRarity].filter(Boolean).map(v => (v ?? '').charAt(0).toUpperCase() + (v ?? '').slice(1)).join(' · ')}
            </p>

            <div className={styles.heroBadges}>
              {item.isMagic && (
                <span className={styles.typeBadge} style={{ color: 'var(--color-gold-bright)', borderColor: 'var(--color-gold-border)' }}>
                  Magic
                </span>
              )}
              <span
                className={styles.factionBadge}
                style={{
                  color: homebrew ? '#c98ad1' : '#7fb0e8',
                  borderColor: homebrew ? '#c98ad133' : '#5b9bd533',
                  background: homebrew ? '#c98ad10a' : '#5b9bd50a',
                }}
              >
                {editionName}
              </span>
              {item.itemRarity != null && (
                <span className={styles.factionBadge} style={{ color: rarity, borderColor: `color-mix(in srgb, ${rarity} 30%, transparent)` }}>
                  {item.itemRarity.charAt(0).toUpperCase() + item.itemRarity.slice(1)}
                </span>
              )}
            </div>

            {/* Stat chips */}
            {stats.length > 0 && (
              <div className={styles.vitalsStrip}>
                {stats.map(s => (
                  <div key={s.label} className={styles.vital} style={s.accent ? { borderColor: s.accent, background: `color-mix(in srgb, ${s.accent} 6%, transparent)` } : {}}>
                    <span className={styles.vitalLabel}>{s.label}</span>
                    <span className={styles.vitalVal} style={{ fontSize: 'var(--text-sm)', color: s.accent }}>{s.value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <a href="/items/" className={styles.backLink}>All Items</a>
        </header>

        <div className={styles.divider} />

        {/* Body — lore left, mechanics right */}
        <div className={styles.mainGrid}>

          {/* Left — lore: description + notes */}
          <div className={styles.leftCol}>
            {descriptionHtml != null && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Description</h2>
                <div className={styles.richText} dangerouslySetInnerHTML={{ __html: descriptionHtml }} />
              </section>
            )}

            {notesHtml != null && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Item Description</h2>
                <div className={styles.richText} dangerouslySetInnerHTML={{ __html: notesHtml }} />
              </section>
            )}

            {descriptionHtml == null && notesHtml == null && (
              <section className={styles.panel}>
                <p style={{ fontFamily: 'var(--font-body)', fontStyle: 'italic', fontSize: 14, color: 'var(--color-text-disabled)', margin: 0 }}>
                  No lore or description added yet.
                </p>
              </section>
            )}
          </div>

          {/* Right — mechanics: magical properties + gameplay stats */}
          <div className={styles.rightCol}>
            {/* Each magical property as its own panel */}
            {magicalProps.map((p, i) => p.effectHtml != null && (
              <section key={i} className={styles.panel}>
                <h2 className={styles.panelTitle}>{p.name}</h2>
                <div className={styles.richText} dangerouslySetInnerHTML={{ __html: p.effectHtml }} />
              </section>
            ))}

            {/* Gameplay stat rows — only shown when data exists */}
            {stats.length > 0 && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Stats</h2>
                {stats.map(s => (
                  <div key={s.label} className={styles.propRow}>
                    <span className={styles.propLabel}>{s.label}</span>
                    <span className={styles.propVal} style={s.accent ? { color: s.accent } : {}}>
                      {s.value}
                    </span>
                  </div>
                ))}
              </section>
            )}
          </div>
        </div>
      </div>
    </BaseTemplate>
  );
};

export const query = graphql`
  query ItemPage($drupalId: ID!) {
    drupal {
      node(id: $drupalId) {
        __typename
        ... on Drupal_NodeItem {
          id title path source
          itemType isMagic itemRarity itemRequiresAttunement
          damage itemBonus itemCost itemWeight
          nonidentifiedName armorCategory armorAcBase armorStrRequirement
          notes        { processed }
          description  { ... on Drupal_ParagraphWysiwyg { text { processed } } }
          edition      { ... on Drupal_TermGameEdition     { name } }
          vestigeLevel { ... on Drupal_TermVestigeLevel    { name } }
          damageTypes      { ... on Drupal_TermDamageType     { name } }
          weaponProperties { ... on Drupal_TermWeaponProperty { name } }
          weaponMastery    { ... on Drupal_TermWeaponMastery  { name } }
          weaponSubtype    { ... on Drupal_TermWeaponSubtype  { name } }
          itemProperties {
            ... on Drupal_TermMagicalProperty {
              name
              effect { ... on Drupal_ParagraphWysiwyg { text { processed } } }
            }
          }
          image { ... on Drupal_MediaImage { mediaImage { url alt } } }
        }
      }
    }
  }
`;

export const Head: HeadFC<ItemPageData> = ({ data }) => (
  <title>{data?.drupal?.node?.title ?? 'Item'} | D&amp;D Consultant</title>
);

export default ItemPage;
