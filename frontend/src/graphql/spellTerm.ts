import { graphql } from 'gatsby';

/**
 * Shared TermSpell selection. graphql_compose maps field_spell_* onto these
 * camelCase names. `name` is the term label (there is no node title).
 */
export const spellTermFields = graphql`
  fragment SpellTermFields on Drupal_TermSpell {
    id
    name
    path
    spellLevel
    spellCastingTime
    spellRange
    spellComponents
    spellDuration
    spellConcentration
    spellRitual
    spellDescription { processed }
    spellSchool { ... on Drupal_TermSpellSchool { name } }
  }
`;
