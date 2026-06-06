/**
 * ItemSheet — the full single-item detail view ("Reliquary Plate").
 *
 * Pure presentation. Pass a Drupal `ItemNode` and it renders. The rich
 * entity fields (epithet, mechanics, provenance, bearer, etc) are all
 * graceful-optional — when Drupal only has the base 6 fields you get a
 * smaller, equally-finished layout with hero + statistics.
 *
 * Designed at 1180px wide. Collapses to one body column at <=1080px and
 * stacks the hero portrait above the heading at <=760px.
 */

import * as React from 'react';
import { Link } from 'gatsby';
import { Badge } from '../atoms/Badge';
import { GameIcon } from '../atoms/GameIcon';
import { RarityFrame } from '../atoms/RarityFrame';
import { StatRow } from '../atoms/StatRow';
import type { GameIconName } from '../../types/icons';
import {
  type ItemNode,
  type ItemEntity,
  type ItemType,
  type ItemRarity,
  type ItemProvenanceEntry,
  toItemEntity,
} from '../../types/item';
import * as styles from './ItemSheet.module.css';

interface ItemSheetProps {
  item: ItemNode | ItemEntity;
}

const TYPE_ICONS: Record<ItemType, GameIconName> = {
  weapon:        'broadsword',
  ranged_weapon: 'arrow-flights',
  armor:         'round-shield',
  shield:        'round-shield',
  ring:          'ring',
  staff:         'magic-swirl',
  wondrous:      'gem-pendant',
  scroll:        'scroll-unfurled',
  potion:        'potion-ball',
  tool:          'swap-bag',
  gear:          'swap-bag',
};

const RARITY_CLASS: Record<ItemRarity, string> = {
  common:      styles.rarityCommon,
  uncommon:    styles.rarityUncommon,
  rare:        styles.rarityRare,
  'very-rare': styles.rarityVeryRare,
  legendary:   styles.rarityLegendary,
  artifact:    styles.rarityArtifact,
  vestige:     styles.rarityVestige,
};

function isEntity(it: ItemNode | ItemEntity): it is ItemEntity {
  return (it as ItemEntity).rarityLabel !== undefined;
}

export function ItemSheet({ item: input }: ItemSheetProps): React.ReactElement {
  const item: ItemEntity = isEntity(input) ? input : toItemEntity(input);
  const typeIcon  = TYPE_ICONS[item.type] ?? 'gem-pendant';
  const rarityCls = RARITY_CLASS[item.rarity];
  const isCursed  = !!item.attunementRequirement && /cursed/i.test(item.attunementRequirement);

  const hasRichBody =
    !!item.bodyHtml || item.mechanics.length > 0 || item.provenance.length > 0;

  return (
    <article className={`${styles.sheet} ${rarityCls}`} data-screen-label={`Item Sheet · ${item.title}`}>
      {/* ── HERO BAND ─────────────────────────────────────────────── */}
      <header className={styles.hero}>
        <div className={styles.heroPortrait}>
          <RarityFrame
            rarity={item.rarity}
            imageUrl={item.imageUrl}
            placeholder={`Portrait of ${item.title}`}
            size={320}
            radius={4}
            alt={item.imageAlt ?? item.title}
          />
        </div>

        <div className={styles.heroBody}>
          <div className={styles.typeLine}>
            <GameIcon name={typeIcon} size={14} color="currentColor" decorative />
            <span>{item.typeLabel}</span>
          </div>
          <h1 className={styles.name}>{item.title}</h1>
          {item.epithet && <p className={styles.epithet}>&ldquo;{item.epithet}&rdquo;</p>}

          <div className={styles.heroBadges}>
            <Badge label={item.rarityLabel} variant={item.rarity} />
            {item.requiresAttunement && (
              <Badge
                label={isCursed ? 'Cursed Attunement' : 'Requires Attunement'}
                variant={isCursed ? 'danger' : 'concentration'}
              />
            )}
            {item.isMagic && !item.requiresAttunement && (
              <Badge label="Magic" variant="school" />
            )}
            {item.school && <Badge label={item.school} variant="school" />}
            {item.homebrew && <Badge label="Homebrew" variant="default" />}
            {item.tags.map(t => <Badge key={t} label={t} variant="default" />)}
          </div>

          {item.shortFlavour && <p className={styles.short}>{item.shortFlavour}</p>}
        </div>
      </header>

      {/* ── BODY ──────────────────────────────────────────────────── */}
      {hasRichBody ? (
        <div className={styles.body}>
          {/* Lore column — long description + benefits */}
          <section className={styles.colLore}>
            {item.bodyHtml && (
              <>
                <SectionTitle icon="scroll-unfurled">Lore</SectionTitle>
                <div
                  className={styles.description}
                  dangerouslySetInnerHTML={{ __html: item.bodyHtml }}
                />
              </>
            )}

            {item.benefits.length > 0 && (
              <>
                <SectionTitle icon="crossed-swords" topGap={!!item.bodyHtml}>Benefits</SectionTitle>
                <ul className={styles.benefits}>
                  {item.benefits.map((b, i) => (
                    <li key={i} className={styles.benefit}>
                      <span className={styles.benefitDot} aria-hidden="true" />
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </section>

          {/* Mechanics column */}
          <section className={styles.colMechanics}>
            {item.mechanics.length > 0 && (
              <>
                <SectionTitle icon="dice-d20">Mechanics</SectionTitle>
                <div className={styles.mechanics}>
                  {item.mechanics.map(m => (
                    <StatRow key={m.label} label={m.label} value={m.value} unit={m.unit} />
                  ))}
                </div>
              </>
            )}

            <SectionTitle icon="swap-bag" topGap={item.mechanics.length > 0}>Vital Statistics</SectionTitle>
            <div className={styles.vitals}>
              <MiniStat label="Type"    value={item.typeLabel} italic />
              <MiniStat label="Rarity"  value={item.rarityLabel} italic />
              {item.weight && <MiniStat label="Weight" value={item.weight} />}
              {item.value  && <MiniStat label="Value"  value={item.value} />}
              {item.school && <MiniStat label="School" value={item.school} italic />}
              {item.attunementRequirement && (
                <MiniStat label="Attune" value={item.attunementRequirement} italic />
              )}
            </div>
          </section>

          {/* Provenance column */}
          {item.provenance.length > 0 && (
            <section className={styles.colProvenance}>
              <SectionTitle icon="book-cover">Provenance</SectionTitle>
              <ol className={styles.timeline}>
                {item.provenance.map((p, i) => (
                  <ProvenanceRow key={i} entry={p} isLast={i === item.provenance.length - 1} />
                ))}
              </ol>
            </section>
          )}
        </div>
      ) : (
        <div className={styles.bodySlim}>
          <section>
            <SectionTitle icon="scroll-unfurled">Vital Statistics</SectionTitle>
            <div className={styles.vitalsSlim}>
              <MiniStat label="Type"   value={item.typeLabel} italic />
              <MiniStat label="Rarity" value={item.rarityLabel} italic />
              <MiniStat label="Magic"  value={item.isMagic ? 'Yes' : 'No'} italic />
              <MiniStat
                label="Attune"
                value={item.requiresAttunement ? 'Required' : 'Not required'}
                italic
              />
              {item.weight && <MiniStat label="Weight" value={item.weight} />}
              {item.value  && <MiniStat label="Value"  value={item.value} />}
            </div>
          </section>
          {item.shortFlavour === null && (
            <p className={styles.emptyNote}>
              No description recorded for this item yet. Add a body in Drupal to fill out the chronicle.
            </p>
          )}
        </div>
      )}

      {/* ── FOOTER BAND ───────────────────────────────────────────── */}
      {(item.bearer || item.lastSeen || item.related.length > 0) && (
        <footer className={styles.footer}>
          {item.bearer && (
            <div className={styles.footerCol}>
              <div className={styles.footerEyebrow}>Current Bearer</div>
              <BearerView bearer={item.bearer} />
            </div>
          )}

          {item.lastSeen && (
            <div className={styles.footerCol}>
              <div className={styles.footerEyebrow}>Last Seen</div>
              <div className={styles.lastSeen}>{item.lastSeen}</div>
            </div>
          )}

          {item.related.length > 0 && (
            <div className={styles.footerCol}>
              <div className={styles.footerEyebrow}>Related Lore</div>
              <div className={styles.related}>
                {item.related.map(r => (
                  r.path ? (
                    <Link key={r.id} to={r.path} className={styles.relatedChip}>{r.title}</Link>
                  ) : (
                    <span key={r.id} className={styles.relatedChip}>{r.title}</span>
                  )
                ))}
              </div>
            </div>
          )}
        </footer>
      )}
    </article>
  );
}

/* ──────────────────────────────────────────────────────────────────── */

interface SectionTitleProps {
  icon:    GameIconName;
  topGap?: boolean;
  children: React.ReactNode;
}
function SectionTitle({ icon, topGap, children }: SectionTitleProps): React.ReactElement {
  return (
    <div className={`${styles.sectionTitle}${topGap ? ` ${styles.sectionTitleGap}` : ''}`}>
      <GameIcon name={icon} size={13} color="currentColor" decorative />
      <span>{children}</span>
      <span className={styles.sectionRule} aria-hidden="true" />
    </div>
  );
}

function MiniStat({ label, value, italic }: { label: string; value: string; italic?: boolean }) {
  return (
    <div className={styles.miniStat}>
      <div className={styles.miniStatLabel}>{label}</div>
      <div className={`${styles.miniStatValue}${italic ? ` ${styles.miniStatItalic}` : ''}`}>{value}</div>
    </div>
  );
}

function ProvenanceRow({ entry, isLast }: { entry: ItemProvenanceEntry; isLast: boolean }) {
  return (
    <li className={`${styles.provRow}${isLast ? ` ${styles.provRowLast}` : ''}`}>
      <div className={styles.provBullet}>
        <span className={styles.provDot} aria-hidden="true" />
        {!isLast && <span className={styles.provLine} aria-hidden="true" />}
      </div>
      <div>
        <div className={styles.provEra}>{entry.era}</div>
        <div className={styles.provNote}>{entry.note}</div>
      </div>
    </li>
  );
}

function BearerView({ bearer }: { bearer: NonNullable<ItemEntity['bearer']> }) {
  const inner = (
    <>
      <span className={styles.bearerSigil} aria-hidden="true">
        <GameIcon name="charm" size={22} color="currentColor" decorative />
      </span>
      <span className={styles.bearerInfo}>
        <span className={styles.bearerName}>{bearer.name}</span>
        <span className={styles.bearerStatus}>{bearer.status}</span>
      </span>
    </>
  );
  return bearer.charPath ? (
    <Link to={bearer.charPath} className={styles.bearer}>{inner}</Link>
  ) : (
    <div className={styles.bearer}>{inner}</div>
  );
}
