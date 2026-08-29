/**
 * Shared spell shapes and display helpers for the public page and console.
 */

export interface SpellRecord {
  id: string;
  title: string;
  path: string | null;
  spellLevel: number;
  school: string | null;
  castingTime: string | null;
  spellRange: string | null;
  spellComponents: string | null;
  spellDuration: string | null;
  concentration: boolean | null;
  ritual: boolean | null;
  descriptionHtml: string | null;
}

export const SPELL_SCHOOLS = [
  'Abjuration',
  'Conjuration',
  'Divination',
  'Enchantment',
  'Evocation',
  'Illusion',
  'Necromancy',
  'Transmutation',
] as const;

export type SpellSchoolName = (typeof SPELL_SCHOOLS)[number];

export function levelLabel(level: number): string {
  if (level === 0) return 'Cantrip';
  return `Level ${String(level)}`;
}

export function flattenDescription(
  description: Array<{ text: Array<{ processed: string }> | null }> | null,
): string | null {
  if (description == null) return null;
  const html = description
    .flatMap(block => block.text ?? [])
    .map(part => part.processed ?? '')
    .filter(part => part !== '')
    .join('');
  return html === '' ? null : html;
}

/** Read a school name from graphql_compose's TermUnion field. */
export function schoolName(
  spellSchool: { name?: string | null } | null | undefined,
): string | null {
  const name = spellSchool?.name;
  return name != null && name !== '' ? name : null;
}

/** Casting time, range, and ritual/concentration flags as a single line. */
export function spellMetaLine(spell: SpellRecord): string {
  const parts: string[] = [];
  if (spell.school != null && spell.school !== '') parts.push(spell.school);
  if (spell.castingTime != null && spell.castingTime !== '') parts.push(spell.castingTime);
  if (spell.spellRange != null && spell.spellRange !== '') parts.push(spell.spellRange);
  if (spell.concentration === true) parts.push('concentration');
  if (spell.ritual === true) parts.push('ritual');
  return parts.join(' · ');
}
