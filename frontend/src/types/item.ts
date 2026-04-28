import type { SpellSchool } from '../components/molecules/SpellCard';
import type { ItemRarity, ItemType } from '../components/molecules/ItemCard';

export type { SpellSchool, ItemRarity, ItemType };

export interface Item {
  name:        string;
  type:        ItemType;
  rarity:      ItemRarity;
  detail:      string;
  attunement?: boolean;
}

export interface Spell {
  name:          string;
  level:         number;
  school:        SpellSchool;
  concentration: boolean;
  ritual?:       boolean;
  castingTime?:  string;
  range?:        string;
  duration?:     string;
  description?:  string;
}

export interface AllSpellsQuery {
  allNodeSpell: {
    nodes: Array<{
      id:                 string;
      title:              string;
      fieldLevel:         number;
      fieldSchool:        string;
      fieldConcentration: boolean;
      fieldRitual?:       boolean;
      fieldCastingTime?:  string;
      fieldRange?:        string;
      fieldDescription?:  string;
    }>;
  };
}

export interface AllItemsQuery {
  allNodeItem: {
    nodes: Array<{
      id:               string;
      title:            string;
      fieldType:        string;
      fieldRarity:      string;
      fieldDetail:      string;
      fieldAttunement?: boolean;
    }>;
  };
}
