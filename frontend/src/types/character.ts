export interface AbilityScores {
  strength:     number;
  dexterity:    number;
  constitution: number;
  intelligence: number;
  wisdom:       number;
  charisma:     number;
}

export interface AbilityModifiers {
  STR: number;
  DEX: number;
  CON: number;
  INT: number;
  WIS: number;
  CHA: number;
}

export interface CharacterSkill {
  name:       string;
  modifier:   number;
  proficient: boolean;
}

export type SpellSlots = Partial<Record<string, number>>;

export interface CharacterItem {
  name:        string;
  type:        string;
  rarity:      string;
  detail:      string;
  attunement?: boolean;
}

export interface CharacterSpell {
  name:          string;
  level:         number;
  school:        string;
  concentration: boolean;
  ritual?:       boolean;
  description?:  string;
}

export interface Character {
  name:              string;
  first_name:        string;
  nickname?:         string;
  pronouns?:         string;
  species:           string;
  dnd_class:         string;
  subclass?:         string;
  level:             number;
  background:        string;
  ability_scores:    AbilityScores;
  skills:            Record<string, number>;
  max_hit_points:    number;
  armor_class:       number;
  movement_speed:    number;
  proficiency_bonus: number;
  spell_slots:       Record<string, number>;
  known_spells:      string[];
  personality_traits: string[];
  ideals:            string[];
  bonds:             string[];
  flaws:             string[];
  backstory:         string;
  relationships:     Record<string, string>;
}

export interface CharacterQuery {
  nodeCharacter: {
    title:             string;
    fieldNickname?:    string;
    fieldBackground?:  string;
    fieldClass:        string;
    fieldSubclass?:    string;
    fieldLevel:        number;
    fieldSpecies:      string;
    fieldAlignment?:   string;
    fieldHp:           number;
    fieldMaxHp:        number;
    fieldAc:           number;
    fieldProfBonus:    number;
    fieldSpeed:        number;
    fieldPersonality?: string;
    fieldBackstory?:   string;
  } | null;
}
