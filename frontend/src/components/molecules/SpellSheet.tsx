/**
 * SpellSheet — hero + parchment scroll for one spell.
 *
 * Shared by the public `/spells/{title}` page and the console Read Spell
 * tab so the two surfaces cannot drift.
 */

import * as React from 'react';
import { Badge } from '../atoms/Badge';
import { GameIcon } from '../atoms/GameIcon';
import type { GameIconName } from '../../types/icons';
import {
  type SpellRecord,
  type SpellSchoolName,
  levelLabel,
} from '../../types/spell';
import { StoryScroll } from './StoryScroll';
import * as styles from './SpellSheet.module.css';

interface SpellSheetProps {
  spell: SpellRecord;
}

const SCHOOL_ICONS: Record<SpellSchoolName, GameIconName> = {
  Abjuration:    'shield',
  Conjuration:   'magic-swirl',
  Divination:    'crystal-ball',
  Enchantment:   'charm',
  Evocation:     'fire-spell-cast',
  Illusion:      'magic-swirl',
  Necromancy:    'skull',
  Transmutation: 'magic-swirl',
};

function schoolIcon(school: string | null): GameIconName {
  if (school != null && school in SCHOOL_ICONS) {
    return SCHOOL_ICONS[school as SpellSchoolName];
  }
  return 'magic-swirl';
}

export function SpellSheet({ spell }: SpellSheetProps): React.ReactElement {
  const stats: Array<{ label: string; value: string }> = [
    spell.castingTime != null && spell.castingTime !== ''
      ? { label: 'Casting', value: spell.castingTime } : null,
    spell.spellRange != null && spell.spellRange !== ''
      ? { label: 'Range', value: spell.spellRange } : null,
    spell.spellComponents != null && spell.spellComponents !== ''
      ? { label: 'Components', value: spell.spellComponents } : null,
    spell.spellDuration != null && spell.spellDuration !== ''
      ? { label: 'Duration', value: spell.spellDuration } : null,
  ].filter((row): row is { label: string; value: string } => row !== null);

  const description = spell.descriptionHtml ?? '';

  return (
    <article className={styles.sheet}>
      <header className={styles.hero}>
        <div className={styles.sigil} aria-hidden="true">
          <GameIcon
            name={schoolIcon(spell.school)}
            size={36}
            colorFilter="var(--filter-gold-bright)"
            decorative
          />
        </div>
        <div className={styles.heroBody}>
          <h1 className={styles.name}>{spell.title}</h1>
          <div className={styles.badges}>
            <Badge label={levelLabel(spell.spellLevel)} size="sm" />
            {spell.school != null && spell.school !== '' && (
              <Badge label={spell.school} variant="school" size="sm" />
            )}
            {spell.concentration === true && (
              <Badge
                label="Concentration"
                variant="concentration"
                icon="concentration-orb"
                size="sm"
              />
            )}
            {spell.ritual === true && (
              <Badge label="Ritual" size="sm" />
            )}
          </div>
          {stats.length > 0 && (
            <div className={styles.vitals}>
              {stats.map(row => (
                <div key={row.label} className={styles.vital}>
                  <span className={styles.vitalLabel}>{row.label}</span>
                  <span className={styles.vitalVal}>{row.value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </header>

      {description !== '' ? (
        <StoryScroll
          html={description}
          unfurlHint="Tap to unfurl the spell"
          unfurlLabel="Unfurl the spell"
          rollUpLabel="Roll up the spell"
        />
      ) : (
        <p className={styles.empty}>No rules text recorded yet.</p>
      )}
    </article>
  );
}
