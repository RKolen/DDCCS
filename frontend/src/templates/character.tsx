import React from 'react';
import { graphql } from 'gatsby';
import type { HeadFC, PageProps } from 'gatsby';
import { BaseTemplate } from '../components/templates/BaseTemplate';
import { CharacterSheetTemplate } from '../components/templates/CharacterSheetTemplate';
import { CharacterHeader } from '../components/organisms/CharacterHeader';
import { AbilityScoreGrid } from '../components/organisms/AbilityScoreGrid';
import { SkillPanel } from '../components/organisms/SkillPanel';
import { SpellList } from '../components/organisms/SpellList';
import { SpellSlotRow } from '../components/molecules/SpellSlotRow';
import { ItemCard } from '../components/molecules/ItemCard';
import type { SpellSchool } from '../components/molecules/SpellCard';
import type { ItemRarity, ItemType } from '../components/molecules/ItemCard';
import type { AbilityKey } from '../components/molecules/AbilityScore';

interface AbilityScoresParagraph {
  fieldStrength:     number;
  fieldDexterity:    number;
  fieldConstitution: number;
  fieldIntelligence: number;
  fieldWisdom:       number;
  fieldCharisma:     number;
}

interface ClassParagraph {
  fieldClass:       Array<{ name: string }> | null;
  fieldSubclassRef: Array<{ name: string }> | null;
}

interface SpellSlotParagraph {
  fieldSpellLevel:          string;
  fieldSpellSlotsTotal:     number;
  fieldSpellSlotsAvailable: number;
}

interface SpellRefParagraph {
  fieldSpell: Array<{
    title:             string;
    fieldSpellLevel:   number;
    fieldSpellSchool:  Array<{ name: string }> | null;
    fieldConcentration: boolean;
  }> | null;
}

interface EquipmentItem {
  title:           string;
  fieldItemType:   string | null;
  fieldItemRarity: string | null;
  fieldDescription: { value: string } | null;
}

interface CharacterData {
  nodeCharacter: {
    title:                 string;
    fieldFirstName:        string | null;
    fieldNickname:         string | null;
    fieldSpecies:          Array<{ name: string }> | null;
    fieldBackground:       Array<{ name: string }> | null;
    fieldLevel:            number | null;
    fieldArmorClass:       number | null;
    fieldMaximumHitpoints: number | null;
    fieldMovementSpeed:    number | null;
    fieldProficiencyBonus: number | null;
    fieldPersonality:      { value: string } | null;
    fieldClass:            ClassParagraph[] | null;
    fieldAbilityScores:    AbilityScoresParagraph[] | null;
    fieldSpellSlots:       SpellSlotParagraph[] | null;
    fieldSpellsRef:        SpellRefParagraph[] | null;
    fieldSkills:           Array<{ name: string }> | null;
    fieldEquipmentItems:   EquipmentItem[] | null;
  } | null;
}

function calcModifier(score: number): number {
  return Math.floor((score - 10) / 2);
}

const VALID_SCHOOLS = new Set<string>([
  'Abjuration', 'Conjuration', 'Divination', 'Enchantment',
  'Evocation', 'Illusion', 'Necromancy', 'Transmutation',
]);

function toSpellSchool(s: string): SpellSchool {
  const capitalised = s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
  return VALID_SCHOOLS.has(capitalised) ? (capitalised as SpellSchool) : 'Evocation';
}

const VALID_RARITIES = new Set<string>([
  'common', 'uncommon', 'rare', 'very-rare', 'legendary', 'artifact',
]);

function toItemRarity(s: string): ItemRarity {
  const lower = s.toLowerCase().replace(' ', '-');
  return VALID_RARITIES.has(lower) ? (lower as ItemRarity) : 'common';
}

const ITEM_TYPE_MAP: Record<string, ItemType> = {
  weapon:         'Melee Weapon',
  melee_weapon:   'Melee Weapon',
  ranged_weapon:  'Ranged Weapon',
  armor:          'Armor',
  ring:           'Ring',
  staff:          'Staff',
  wondrous:       'Wondrous',
  wondrous_item:  'Wondrous',
};

function toItemType(s: string): ItemType {
  return ITEM_TYPE_MAP[s.toLowerCase()] ?? 'Wondrous';
}

const CharacterPage: React.FC<PageProps<CharacterData>> = ({ data, location }) => {
  const char = data.nodeCharacter;

  if (!char) {
    return (
      <BaseTemplate currentPath={location.pathname}>
        <p style={{ padding: '40px', color: 'var(--color-text-secondary)' }}>Character not found.</p>
      </BaseTemplate>
    );
  }

  const cls      = char.fieldClass?.[0];
  const clsName  = cls?.fieldClass?.[0]?.name ?? 'Adventurer';
  const subclass = cls?.fieldSubclassRef?.[0]?.name;
  const species  = char.fieldSpecies?.[0]?.name ?? '';
  const hp       = char.fieldMaximumHitpoints ?? 0;

  const ab = char.fieldAbilityScores?.[0];
  const scores: Record<AbilityKey, number> = {
    STR: ab?.fieldStrength     ?? 10,
    DEX: ab?.fieldDexterity    ?? 10,
    CON: ab?.fieldConstitution ?? 10,
    INT: ab?.fieldIntelligence ?? 10,
    WIS: ab?.fieldWisdom       ?? 10,
    CHA: ab?.fieldCharisma     ?? 10,
  };
  const modifiers: Record<AbilityKey, number> = {
    STR: calcModifier(scores.STR),
    DEX: calcModifier(scores.DEX),
    CON: calcModifier(scores.CON),
    INT: calcModifier(scores.INT),
    WIS: calcModifier(scores.WIS),
    CHA: calcModifier(scores.CHA),
  };

  const skills = (char.fieldSkills ?? []).map(s => ({
    name: s.name,
    modifier: 0,
    proficient: true,
  }));

  const spells = (char.fieldSpellsRef ?? [])
    .flatMap(ref => ref.fieldSpell ?? [])
    .map(sp => ({
      name:          sp.title,
      level:         sp.fieldSpellLevel,
      school:        toSpellSchool(sp.fieldSpellSchool?.[0]?.name ?? ''),
      concentration: sp.fieldConcentration,
    }));

  const equipment = (char.fieldEquipmentItems ?? []).map(item => ({
    name:   item.title,
    rarity: toItemRarity(item.fieldItemRarity ?? 'common'),
    type:   toItemType(item.fieldItemType ?? 'wondrous'),
    detail: item.fieldDescription?.value ?? '',
  }));

  return (
    <BaseTemplate currentPath={location.pathname}>
      <CharacterSheetTemplate
        header={
          <CharacterHeader
            name={char.title}
            nickname={char.fieldNickname ?? undefined}
            background={char.fieldBackground?.[0]?.name}
            cls={clsName}
            subclass={subclass}
            level={char.fieldLevel ?? 1}
            species={species}
            hp={hp}
            maxHp={hp}
            ac={char.fieldArmorClass ?? 10}
            profBonus={char.fieldProficiencyBonus ?? 2}
            speed={char.fieldMovementSpeed ?? 30}
          />
        }
        stats={<AbilityScoreGrid scores={scores} modifiers={modifiers} />}
        spellSlots={
          char.fieldSpellSlots && char.fieldSpellSlots.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {char.fieldSpellSlots.map(slot => (
                <SpellSlotRow
                  key={slot.fieldSpellLevel}
                  level={slot.fieldSpellLevel}
                  total={slot.fieldSpellSlotsTotal}
                  available={slot.fieldSpellSlotsAvailable}
                />
              ))}
            </div>
          ) : undefined
        }
        skills={<SkillPanel skills={skills} />}
        spells={spells.length > 0 ? <SpellList spells={spells} /> : undefined}
        equipment={
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {equipment.map(item => (
              <ItemCard key={item.name} {...item} />
            ))}
          </div>
        }
      />
    </BaseTemplate>
  );
};

export const query = graphql`
  query CharacterPage($id: String!) {
    nodeCharacter(id: { eq: $id }) {
      title
      fieldFirstName
      fieldNickname
      fieldLevel
      fieldArmorClass
      fieldMaximumHitpoints
      fieldMovementSpeed
      fieldProficiencyBonus
      fieldPersonality { value }
      fieldSpecies { name }
      fieldBackground { name }
      fieldClass {
        ... on paragraph__class {
          fieldClass { name }
          fieldSubclassRef { name }
        }
      }
      fieldAbilityScores {
        ... on paragraph__ability_scores {
          fieldStrength
          fieldDexterity
          fieldConstitution
          fieldIntelligence
          fieldWisdom
          fieldCharisma
        }
      }
      fieldSpellSlots {
        ... on paragraph__spell_slot {
          fieldSpellLevel
          fieldSpellSlotsTotal
          fieldSpellSlotsAvailable
        }
      }
      fieldSpellsRef {
        ... on paragraph__spell_reference {
          fieldSpell {
            ... on node__spell {
              title
              fieldSpellLevel
              fieldSpellSchool { name }
              fieldConcentration
            }
          }
        }
      }
      fieldSkills { name }
      fieldEquipmentItems {
        ... on node__item {
          title
          fieldItemType
          fieldItemRarity
          fieldDescription { value }
        }
      }
    }
  }
`;

export const Head: HeadFC<CharacterData> = ({ data }) => (
  <title>{data.nodeCharacter?.title ?? 'Character'} | D&D Consultant</title>
);

export default CharacterPage;
