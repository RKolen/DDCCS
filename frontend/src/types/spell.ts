/**
 * Shared spell shapes and display helpers for the public page and console.
 *
 * Vault entries are `taxonomy_term.spells` (`Drupal_TermSpell`), not nodes.
 * graphql_compose exposes `field_spell_*` as `spellLevel`, `spellCastingTime`,
 * and so on. The display record still uses `title` so SpellSheet stays stable.
 */

/**
 * Connection page size for the vault. Requires graphql_compose
 * `settings.edge_max_limit` >= 500; the compose default is 100 and
 * rejects a larger `first`.
 */
export const SPELL_QUERY_FIRST = 500;

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

/** One `termSpells` / `TermSpell` node as graphql_compose returns it. */
export interface SpellTermNode {
  id: string;
  name: string;
  path: string | null;
  spellLevel: number | null;
  spellCastingTime: string | null;
  spellRange: string | null;
  spellComponents: string | null;
  spellDuration: string | null;
  spellConcentration: boolean | null;
  spellRitual: boolean | null;
  spellDescription: { processed?: string | null } | null;
  spellSchool: { name: string | null } | null;
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

/** Drupal text_long processed HTML (taxonomy spell description). */
export function flattenText(
  field: { processed?: string | null } | null | undefined,
): string | null {
  const html = field?.processed ?? '';
  return html === '' ? null : html;
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

function emptyToNull(value: string | null | undefined): string | null {
  if (value == null) return null;
  const trimmed = value.trim();
  return trimmed === '' ? null : trimmed;
}

/** Map a graphql_compose spell term onto the shared display record. */
export function spellTermToRecord(term: SpellTermNode): SpellRecord {
  return {
    id: term.id,
    title: term.name,
    path: emptyToNull(term.path),
    spellLevel: term.spellLevel ?? 0,
    school: schoolName(term.spellSchool),
    castingTime: emptyToNull(term.spellCastingTime),
    spellRange: emptyToNull(term.spellRange),
    spellComponents: emptyToNull(term.spellComponents),
    spellDuration: emptyToNull(term.spellDuration),
    concentration: term.spellConcentration,
    ritual: term.spellRitual,
    descriptionHtml: flattenText(term.spellDescription),
  };
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
