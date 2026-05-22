import React from 'react';
import { graphql, Link } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { Portrait } from '../components/atoms/Portrait';
import { cleanHtml } from '../utils/cleanHtml';
import * as styles from './character.module.css';

// ── Types ─────────────────────────────────────────────────────────────────────

interface ScoreItem { score: number | null; }

interface AbilityScoresParagraph {
  strength?:     ScoreItem | null;
  dexterity?:    ScoreItem | null;
  constitution?: ScoreItem | null;
  intelligence?: ScoreItem | null;
  wisdom?:       ScoreItem | null;
  charisma?:     ScoreItem | null;
}

interface ClassParagraph {
  level:        number | null;
  classRef:     { name: string } | null;
  subclassRef:  { name: string } | null;
}

interface BackstoryParagraph {
  text: TextValue[] | null;
}

interface ItemNode {
  title:                  string;
  path:                   string | null;
  itemType:               string | null;
  itemRarity:             string | null;
  isMagic:                boolean | null;
  itemRequiresAttunement: boolean | null;
}

interface TextValue { value: string; }

interface CharacterNode {
  title:               string;
  firstName:           string | null;
  nickname:            string | null;
  pronouns:            string | null;
  role:                string | null;
  characterType:       boolean | null;
  level:               number | null;
  armorClass:          number | null;
  maximumHitpoints:    number | null;
  movementSpeed:       number | null;
  proficiencyBonus:    number | null;
  gold:                number | null;
  sourceCharacter:     boolean | null;
  characterClasses:    ClassParagraph[] | null;
  personalityTraits:   TextValue[] | null;
  bonds:               TextValue[] | null;
  ideals:              TextValue[] | null;
  flaws:               TextValue[] | null;
  specializedAbilities: TextValue[] | null;
  abilityScores: AbilityScoresParagraph | null;
  backstory:     BackstoryParagraph[] | null;
  image: { mediaImage: { url: string; alt: string } | null } | null;
  equipmentItems:  ItemNode[] | null;
  magicItemsRef:   ItemNode[] | null;
}

interface CharacterData {
  drupal: { node: Partial<CharacterNode> | null } | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function rarityClass(rarity: string | null | undefined): string {
  switch ((rarity ?? '').toLowerCase()) {
    case 'uncommon':  return styles.rarityUncommon;
    case 'rare':      return styles.rarityRare;
    case 'very rare': return styles.rarityVeryRare;
    case 'legendary': return styles.rarityLegendary;
    case 'artifact':  return styles.rarityArtifact;
    case 'vestige':   return styles.rarityVestige;
    default:          return '';
  }
}

function mod(score: number): string {
  const m = Math.floor((score - 10) / 2);
  return m >= 0 ? `+${m}` : String(m);
}

function AbilityTile({ label, score }: { label: string; score: number | null }): React.ReactElement {
  const s = score ?? 0;
  return (
    <div className={styles.abilityTile}>
      <span className={styles.abilityLabel}>{label}</span>
      <span className={styles.abilityScore}>{s}</span>
      <span className={styles.abilityMod}>{mod(s)}</span>
    </div>
  );
}

function HtmlList({ items }: { items: TextValue[] | null | undefined }): React.ReactElement | null {
  if (!items?.length) return null;
  return (
    <ul className={styles.textList}>
      {items.map((it, i) => (
        it.value.includes('<') ? (
          <li key={i} dangerouslySetInnerHTML={{ __html: cleanHtml(it.value) }} />
        ) : (
          <li key={i}>{it.value}</li>
        )
      ))}
    </ul>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const CharacterPage: React.FC<PageProps<CharacterData>> = ({ data, location }) => {
  const char = data.drupal?.node as CharacterNode | null;

  if (!char?.title) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p style={{ padding: '40px', color: 'var(--color-text-secondary)' }}>
          Character not found.
        </p>
      </BaseTemplate>
    );
  }

  const cls        = char.characterClasses?.[0] ?? null;
  const className  = cls?.classRef?.name ?? null;
  const subclass   = cls?.subclassRef?.name ?? null;
  const imageUrl   = char.image?.mediaImage?.url ?? null;

  const as = char.abilityScores;
  const scores: Record<string, number | null> | null = as ? {
    STR: as.strength?.score    ?? null,
    DEX: as.dexterity?.score   ?? null,
    CON: as.constitution?.score ?? null,
    INT: as.intelligence?.score ?? null,
    WIS: as.wisdom?.score      ?? null,
    CHA: as.charisma?.score    ?? null,
  } : null;

  const backstoryText = char.backstory?.[0]?.text?.[0]?.value ?? null;

  /* Merge equipment + magic refs, deduplicate by path (or title as fallback) */
  const seen = new Set<string>();
  const allItems = [...(char.equipmentItems ?? []), ...(char.magicItemsRef ?? [])].filter(i => {
    const key = i.path ?? i.title;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  const weapons = allItems.filter(i => i.itemType === 'weapon');
  const magic   = allItems.filter(i => i.isMagic && i.itemType !== 'weapon');
  const gear    = allItems.filter(i => !i.isMagic && i.itemType !== 'weapon');

  return (
    <BaseTemplate currentPath={location.pathname}>
      <div className={styles.page}>

        {/* ── Hero ── */}
        <header className={styles.hero}>
          <Portrait name={char.title} size={120} imageUrl={imageUrl} className={styles.heroPortrait} />

          <div className={styles.heroBody}>
            <div className={styles.heroTop}>
              <h1 className={styles.name}>{char.title}</h1>
              {char.sourceCharacter && <span className={styles.canonPill}>Canon</span>}
            </div>

            {char.nickname && (
              <p className={styles.nickname}>&ldquo;{char.nickname}&rdquo;</p>
            )}
            {char.pronouns && (
              <p className={styles.pronouns}>{char.pronouns}</p>
            )}

            {/* Role shown for NPCs (characterType === false) */}
            {char.role && char.characterType === false && (
              <p className={styles.pronouns}>{char.role}</p>
            )}

            <div className={styles.heroBadges}>
              {className && (
                <span className={styles.classBadge}>
                  {className}{subclass ? ` — ${subclass}` : ''}
                </span>
              )}
              {char.level !== null && (
                <span className={styles.levelBadge}>Level {char.level}</span>
              )}
            </div>

            {/* Inline vitals strip */}
            <div className={styles.vitalsStrip}>
              {char.maximumHitpoints !== null && (
                <div className={`${styles.vital} ${styles.vitalHp}`}>
                  <span className={styles.vitalLabel}>HP</span>
                  <span className={styles.vitalVal}>{char.maximumHitpoints}</span>
                </div>
              )}
              {char.armorClass !== null && (
                <div className={styles.vital}>
                  <span className={styles.vitalLabel}>AC</span>
                  <span className={styles.vitalVal}>{char.armorClass}</span>
                </div>
              )}
              {char.movementSpeed !== null && (
                <div className={styles.vital}>
                  <span className={styles.vitalLabel}>Speed</span>
                  <span className={styles.vitalVal}>{char.movementSpeed} ft</span>
                </div>
              )}
              {char.proficiencyBonus !== null && (
                <div className={styles.vital}>
                  <span className={styles.vitalLabel}>Prof</span>
                  <span className={styles.vitalVal}>+{char.proficiencyBonus}</span>
                </div>
              )}
              {char.gold !== null && (
                <div className={styles.vital}>
                  <span className={styles.vitalLabel}>Gold</span>
                  <span className={styles.vitalVal}>{char.gold} gp</span>
                </div>
              )}
            </div>
          </div>

          <Link to="/characters/" className={styles.backLink}>All characters</Link>
        </header>

        {/* ── Divider ── */}
        <div className={styles.divider} />

        {/* ── Main grid ── */}
        <div className={styles.mainGrid}>

          {/* ── Left column ── */}
          <div className={styles.leftCol}>

            {/* Ability scores */}
            {scores && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Ability Scores</h2>
                <div className={styles.abilityGrid}>
                  {(Object.entries(scores) as [string, number | null][]).map(([label, val]) => (
                    <AbilityTile key={label} label={label} score={val} />
                  ))}
                </div>
              </section>
            )}

            {/* Personality traits */}
            {char.personalityTraits && char.personalityTraits.length > 0 && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Personality Traits</h2>
                <HtmlList items={char.personalityTraits} />
              </section>
            )}

            {/* Ideals + Bonds + Flaws 2×2 */}
            {(char.ideals?.length || char.bonds?.length || char.flaws?.length) && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Character</h2>
                <div className={styles.characterGrid}>
                  {char.ideals && char.ideals.length > 0 && (
                    <div className={styles.characterBox}>
                      <h3 className={styles.boxLabel}>Ideals</h3>
                      <HtmlList items={char.ideals} />
                    </div>
                  )}
                  {char.bonds && char.bonds.length > 0 && (
                    <div className={styles.characterBox}>
                      <h3 className={styles.boxLabel}>Bonds</h3>
                      <HtmlList items={char.bonds} />
                    </div>
                  )}
                  {char.flaws && char.flaws.length > 0 && (
                    <div className={styles.characterBox}>
                      <h3 className={styles.boxLabel}>Flaws</h3>
                      <HtmlList items={char.flaws} />
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* Backstory — parchment scroll */}
            {backstoryText && <BackstoryScroll html={cleanHtml(backstoryText)} />}
          </div>

          {/* ── Right column — game abilities + items ── */}
          <div className={styles.rightCol}>

            {/* Special abilities */}
            {char.specializedAbilities && char.specializedAbilities.length > 0 && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Special Abilities</h2>
                {char.specializedAbilities.map((a, i) => (
                  <div
                    key={i}
                    className={styles.prose}
                    dangerouslySetInnerHTML={{ __html: cleanHtml(a.value) }}
                  />
                ))}
              </section>
            )}

            {/* Weapons */}
            {weapons.length > 0 && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Weapons</h2>
                <ul className={styles.itemList}>
                  {weapons.map((item, i) => <ItemRow key={i} item={item} />)}
                </ul>
              </section>
            )}

            {/* Magic items */}
            {magic.length > 0 && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Magic Items</h2>
                <ul className={styles.itemList}>
                  {magic.map((item, i) => <ItemRow key={i} item={item} />)}
                </ul>
              </section>
            )}

            {/* Gear */}
            {gear.length > 0 && (
              <section className={styles.panel}>
                <h2 className={styles.panelTitle}>Gear</h2>
                <ul className={styles.itemList}>
                  {gear.map((item, i) => <ItemRow key={i} item={item} />)}
                </ul>
              </section>
            )}
          </div>
        </div>
      </div>
    </BaseTemplate>
  );
};

// ── Backstory scroll ──────────────────────────────────────────────────────────

function BackstoryScroll({ html }: { html: string }): React.ReactElement {
  const [open, setOpen] = React.useState(false);

  /* Add drop-cap span to the very first letter */
  const withDropCap = html.replace(
    /^(<p[^>]*>)\s*([A-Za-z])/,
    (_, tag, letter) =>
      `${tag}<span style="float:left;font-family:var(--font-display);font-size:3.4em;line-height:0.85;margin:4px 10px 0 0;color:var(--parchment-shadow);font-weight:700;">${letter}</span>`,
  );

  return (
    <section className={styles.panel}>
      <h2 className={styles.panelTitle}>Backstory</h2>
      <div className={styles.backstoryScroll}>

        {/* Top cap — always visible, click to toggle */}
        <button
          type="button"
          className={styles.scrollDowelBtn}
          onClick={() => setOpen(o => !o)}
          aria-expanded={open}
          aria-label={open ? 'Roll up chronicle' : 'Unfurl the chronicle'}
        >
          <div className={styles.scrollDowel} aria-hidden="true" />
          {!open && (
            <span className={styles.scrollHint}>Unfurl the chronicle</span>
          )}
        </button>

        {/* Parchment body — collapses/expands */}
        <div className={`${styles.scrollBody}${open ? ` ${styles.scrollBodyOpen}` : ''}`}>
          <div className={styles.scrollBodyInner}>
            <div className={styles.parchment}>
              <div
                className={styles.parchmentBody}
                dangerouslySetInnerHTML={{ __html: withDropCap }}
              />
            </div>
          </div>
        </div>

        {/* Bottom cap — always visible, sits below the content */}
        <button
          type="button"
          className={styles.scrollDowelBtn}
          onClick={() => setOpen(o => !o)}
          aria-label={open ? 'Roll up chronicle' : 'Unfurl the chronicle'}
        >
          {open && (
            <span className={styles.scrollHint}>Close chronicle</span>
          )}
          <div className={styles.scrollDowel} aria-hidden="true" />
        </button>

      </div>
    </section>
  );
}

// ── Item row ──────────────────────────────────────────────────────────────────

function ItemRow({ item }: { item: ItemNode }): React.ReactElement {
  const nameEl = item.path
    ? <Link to={item.path} className={styles.itemLink}>{item.title}</Link>
    : <span>{item.title}</span>;

  return (
    <li className={styles.itemRow}>
      {nameEl}
      <span className={styles.itemMeta}>
        {item.itemRequiresAttunement && (
          <span className={styles.attuneChip}>Attune</span>
        )}
        {item.itemRarity && item.itemRarity !== 'common' && (
          <span className={`${styles.rarityChip} ${rarityClass(item.itemRarity)}`}>
            {item.itemRarity}
          </span>
        )}
      </span>
    </li>
  );
}

// ── Query ─────────────────────────────────────────────────────────────────────

export const query = graphql`
  query CharacterPage($id: ID!) {
    drupal {
      node(id: $id) {
        ... on Drupal_NodeCharacter {
          title
          firstName
          nickname
          pronouns
          role
          characterType
          level
          armorClass
          maximumHitpoints
          movementSpeed
          proficiencyBonus
          gold
          sourceCharacter
          characterClasses {
            ... on Drupal_ParagraphClass {
              level
              classRef     { ... on Drupal_TermClass { name } }
              subclassRef  { ... on Drupal_TermClass { name } }
            }
          }
          personalityTraits { value }
          bonds  { value }
          ideals { value }
          flaws  { value }
          specializedAbilities { value }
          abilityScores {
            ... on Drupal_ParagraphAbilityScore {
              strength     { ... on Drupal_AbilityScoreItem { score } }
              dexterity    { ... on Drupal_AbilityScoreItem { score } }
              constitution { ... on Drupal_AbilityScoreItem { score } }
              intelligence { ... on Drupal_AbilityScoreItem { score } }
              wisdom       { ... on Drupal_AbilityScoreItem { score } }
              charisma     { ... on Drupal_AbilityScoreItem { score } }
            }
          }
          backstory {
            ... on Drupal_ParagraphWysiwyg {
              text { value }
            }
          }
          image {
            ... on Drupal_MediaImage {
              mediaImage { url alt }
            }
          }
          equipmentItems {
            ... on Drupal_NodeItem {
              title path itemType itemRarity isMagic itemRequiresAttunement
            }
          }
          magicItemsRef {
            ... on Drupal_NodeItem {
              title path itemType itemRarity isMagic itemRequiresAttunement
            }
          }
        }
      }
    }
  }
`;

export const Head: HeadFC<CharacterData> = ({ data }) => {
  const char = data.drupal?.node as CharacterNode | null;
  return <title>{char?.title ?? 'Character'} | D&amp;D Consultant</title>;
};

export default CharacterPage;
