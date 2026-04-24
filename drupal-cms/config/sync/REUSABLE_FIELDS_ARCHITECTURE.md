# Drupal Character Entity - Reusable Fields Architecture

This document describes the improved reusable architecture for the Drupal character entity.

## Overview

Instead of simple text fields, the character entity now uses:
- **Taxonomy vocabularies** for reusable terms (spells, feats, abilities, subclasses)
- **Content types** for complex reusable entities (items including weapons, armor, magic items)
- **Paragraphs** for structured data with entity references

---

## Taxonomy Vocabularies Created

### 1. Spells (`taxonomy.vocabulary.spells`)
For character spellcasting. Terms can have additional fields added later (level, school, components, etc.)

**Sample Terms:**
- Fireball
- Magic Missile
- Cure Wounds

### 2. Feats (`taxonomy.vocabulary.feats`)
For character feats.

**Sample Terms:**
- Alert
- Skilled

### 3. Abilities (`taxonomy.vocabulary.abilities`)
For class abilities and features.

**Sample Terms:**
- Favored Enemy
- Natural Explorer

### 4. Subclasses (`taxonomy.vocabulary.subclasses`)
For class subclasses and archetypes.

**Sample Terms:**
- Hunter
- Champion
- Life Domain

### 5. Equipment Types (`taxonomy.vocabulary.equipment_types`)
For categorizing equipment items.

**Sample Terms:**
- Longsword
- Longbow
- Leather Armor

---

## Content Types Created

### Item (`node.type.item`)
Reusable items that can be referenced by characters.

**Fields:**
- `field_item_type` (List): weapon, armor, item, magic_item
- `field_item_rarity` (List): common, uncommon, rare, very_rare, legendary, artifact
- `field_item_requires_attunement` (Boolean)
- `field_item_properties` (Entity Reference): References equipment_types taxonomy
- `body`: Item description

---

## Character Content Type - New Entity Reference Fields

### Spells
- **Field:** `field_spells`
- **Type:** Entity Reference (multiple)
- **Target:** spells taxonomy

### Feats
- **Field:** `field_feats_taxonomy`
- **Type:** Entity Reference (multiple)
- **Target:** feats taxonomy

### Class Abilities
- **Field:** `field_abilities_taxonomy`
- **Type:** Entity Reference (multiple)
- **Target:** abilities taxonomy

### Equipment
- **Field:** `field_equipment_items`
- **Type:** Entity Reference (multiple)
- **Target:** Item content type
- **Includes:** Weapons, armor, and regular items

### Magic Items
- **Field:** `field_magic_items_ref`
- **Type:** Entity Reference (multiple)
- **Target:** Item content type (filter by item_type = magic_item)

### Subclass (on Class paragraph)
- **Field:** `field_subclass_ref`
- **Type:** Entity Reference
- **Target:** subclasses taxonomy

---

## Retained Text Fields (Character-Specific Data)

These remain as text fields because they are unique to each character:

- `field_specialized_abilities` - Custom abilities unique to the character
- `field_major_plot_actions` - Character-specific story actions
- `field_backstory` - Unique character history
- `field_personality_traits` - Unique personality
- `field_ideals`, `field_bonds`, `field_flaws` - Unique roleplay elements

---

## Benefits of This Architecture

1. **Reusability:** Create a spell, feat, or item once, use it on multiple characters
2. **Consistency:** All characters reference the same canonical entity
3. **Maintainability:** Update a spell description in one place
4. **Extensibility:** Add fields to taxonomies/content types without modifying characters
5. **Search:** Find all characters with a specific spell, feat, or item
6. **Validation:** Can't accidentally create typos or duplicates

---

## Migration from Text Fields

To migrate existing text-based data to entity references:

1. Create taxonomy terms for existing text values
2. Use Drupal's migrate API or custom scripts to convert text → entity references
3. Or use the **Autocomplete Create** option to allow creating terms on-the-fly

---

## Configuration Files Added

### Taxonomy Vocabularies
- `taxonomy.vocabulary.spells.yml`
- `taxonomy.vocabulary.feats.yml`
- `taxonomy.vocabulary.abilities.yml`
- `taxonomy.vocabulary.subclasses.yml`
- `taxonomy.vocabulary.equipment_types.yml`

### Content Type
- `node.type.item.yml`

### Field Storage (New Entity Reference Fields)
- `field.storage.node.field_spells.yml`
- `field.storage.node.field_feats_taxonomy.yml`
- `field.storage.node.field_abilities_taxonomy.yml`
- `field.storage.node.field_equipment_items.yml`
- `field.storage.node.field_magic_items_ref.yml`
- `field.storage.paragraph.field_subclass_ref.yml`

### Field Instances
- `field.field.node.character.field_spells.yml`
- `field.field.node.character.field_feats_taxonomy.yml`
- `field.field.node.character.field_abilities_taxonomy.yml`
- `field.field.node.character.field_equipment_items.yml`
- `field.field.node.character.field_magic_items_ref.yml`
- `field.field.paragraph.class.field_subclass_ref.yml`

### Item Content Type Fields
- `field.storage.node.field_item_type.yml`
- `field.storage.node.field_item_rarity.yml`
- `field.storage.node.field_item_requires_attunement.yml`
- `field.storage.node.field_item_properties.yml`
- `field.field.node.item.field_item_type.yml`
- `field.field.node.item.field_item_rarity.yml`
- `field.field.node.item.field_item_requires_attunement.yml`
- `field.field.node.item.field_item_properties.yml`

### Sample Terms (for testing)
- Various `taxonomy.term.*.yml` files for spells, feats, abilities, subclasses, equipment

---

## Next Steps

1. Import the configuration:
   ```bash
   ddev drush cim -y
   ddev drush cr
   ```

2. Create items in the Item content type (weapons, armor, magic items)

3. Add more terms to the taxonomies as needed

4. Edit characters and use the autocomplete fields to select reusable entities

5. Consider using the **Entity Reference Views** module for filtered selections (e.g., only show magic items when selecting magic items)
