# Drupal Character Entity - Missing Fields Added

This document summarizes all the new fields added to the Drupal character content type to match the Python JSON structure.

## Summary

**Total New Fields Added:** 29 fields across the character content type and paragraph types
**New Paragraph Types:** 2 (spell_slot, relationship)
**New Field Groups:** 5 (Equipment, Spells, Abilities, Relationships, AI Configuration, Voice)

---

## New Fields Added to Character Content Type

### Identity Fields
| Field | Machine Name | Type | Description |
|-------|--------------|------|-------------|
| Pronouns | `field_pronouns` | String | Character pronouns (e.g., he/him, she/her, they/them) |

### Combat & Stats Fields
| Field | Machine Name | Type | Description |
|-------|--------------|------|-------------|
| Proficiency Bonus | `field_proficiency_bonus` | Integer | Character proficiency bonus (2-6) |

### Equipment Fields (Equipment Tab)
| Field | Machine Name | Type | Description |
|-------|--------------|------|-------------|
| Weapons | `field_weapons` | String (multiple) | Character weapons |
| Armor | `field_armor` | String (multiple) | Character armor |
| Items | `field_items` | String (multiple) | Character equipment items |
| Gold | `field_gold` | Integer | Gold pieces |

### Spell Fields (Spells Tab)
| Field | Machine Name | Type | Description |
|-------|--------------|------|-------------|
| Spell Slots | `field_spell_slots` | Paragraph (multiple) | Spell slots by level |
| Magic Items | `field_magic_items` | String (multiple) | Magic items possessed |

### Abilities Fields (Abilities Tab)
| Field | Machine Name | Type | Description |
|-------|--------------|------|-------------|
| Class Abilities | `field_class_abilities` | String (multiple) | Class features |
| Specialized Abilities | `field_specialized_abilities` | String (multiple) | Custom abilities |
| Feats | `field_feats` | String (multiple) | Character feats |
| Major Plot Actions | `field_major_plot_actions` | String (multiple) | Significant story actions |

### Relationship Fields (Relationships Tab)
| Field | Machine Name | Type | Description |
|-------|--------------|------|-------------|
| Relationships | `field_relationships` | Paragraph (multiple) | Character relationships |

### AI Configuration Fields (AI Configuration Tab)
| Field | Machine Name | Type | Description |
|-------|--------------|------|-------------|
| AI Enabled | `field_ai_enabled` | Boolean | Enable AI consultation |
| AI Model | `field_ai_model` | String | AI model name |
| AI Temperature | `field_ai_temperature` | Decimal | AI temperature (0.0-2.0) |
| AI Max Tokens | `field_ai_max_tokens` | Integer | Max tokens for responses |
| AI System Prompt | `field_ai_system_prompt` | Text (long) | Custom system prompt |

### Voice Fields (Voice Tab)
| Field | Machine Name | Type | Description |
|-------|--------------|------|-------------|
| Voice ID | `field_voice_id` | String | Piper TTS voice identifier |
| Voice Speed | `field_voice_speed` | Decimal | TTS speed multiplier |
| Voice Pitch | `field_voice_pitch` | Integer | TTS pitch shift |

---

## New Paragraph Types

### Spell Slot Paragraph
Fields:
- `field_spell_level` (Integer, required) - Spell level (1-9)
- `field_spell_slots_total` (Integer, required) - Total slots for this level
- `field_spell_slots_available` (Integer, required) - Available slots

### Relationship Paragraph
Fields:
- `field_related_character` (Entity Reference, required) - Reference to character
- `field_relationship_type` (List, required) - Type (ally, enemy, friend, etc.)
- `field_relationship_description` (String) - Description
- `field_relationship_strength` (Integer) - Strength 1-10

---

## Updated Paragraph Types

### Class Paragraph
Added field:
- `field_subclass` (String) - Class subclass/archetype

---

## Configuration Files Created

### Field Storage Files
1. `field.storage.node.field_pronouns.yml`
2. `field.storage.node.field_proficiency_bonus.yml`
3. `field.storage.node.field_feats.yml`
4. `field.storage.node.field_class_abilities.yml`
5. `field.storage.node.field_specialized_abilities.yml`
6. `field.storage.node.field_major_plot_actions.yml`
7. `field.storage.node.field_weapons.yml`
8. `field.storage.node.field_armor.yml`
9. `field.storage.node.field_items.yml`
10. `field.storage.node.field_gold.yml`
11. `field.storage.node.field_magic_items.yml`
12. `field.storage.node.field_spell_slots.yml`
13. `field.storage.node.field_relationships.yml`
14. `field.storage.node.field_ai_enabled.yml`
15. `field.storage.node.field_ai_temperature.yml`
16. `field.storage.node.field_ai_max_tokens.yml`
17. `field.storage.node.field_ai_system_prompt.yml`
18. `field.storage.node.field_ai_model.yml`
19. `field.storage.node.field_voice_id.yml`
20. `field.storage.node.field_voice_speed.yml`
21. `field.storage.node.field_voice_pitch.yml`
22. `field.storage.paragraph.field_subclass.yml`
23. `field.storage.paragraph.field_spell_level.yml`
24. `field.storage.paragraph.field_spell_slots_total.yml`
25. `field.storage.paragraph.field_spell_slots_available.yml`
26. `field.storage.paragraph.field_related_character.yml`
27. `field.storage.paragraph.field_relationship_type.yml`
28. `field.storage.paragraph.field_relationship_description.yml`
29. `field.storage.paragraph.field_relationship_strength.yml`

### Paragraph Type Files
1. `paragraphs.paragraphs_type.spell_slot.yml`
2. `paragraphs.paragraphs_type.relationship.yml`

### Field Instance Files (Character)
1. `field.field.node.character.field_pronouns.yml`
2. `field.field.node.character.field_proficiency_bonus.yml`
3. `field.field.node.character.field_feats.yml`
4. `field.field.node.character.field_class_abilities.yml`
5. `field.field.node.character.field_specialized_abilities.yml`
6. `field.field.node.character.field_major_plot_actions.yml`
7. `field.field.node.character.field_weapons.yml`
8. `field.field.node.character.field_armor.yml`
9. `field.field.node.character.field_items.yml`
10. `field.field.node.character.field_gold.yml`
11. `field.field.node.character.field_magic_items.yml`
12. `field.field.node.character.field_spell_slots.yml`
13. `field.field.node.character.field_relationships.yml`
14. `field.field.node.character.field_ai_enabled.yml`
15. `field.field.node.character.field_ai_temperature.yml`
16. `field.field.node.character.field_ai_max_tokens.yml`
17. `field.field.node.character.field_ai_system_prompt.yml`
18. `field.field.node.character.field_ai_model.yml`
19. `field.field.node.character.field_voice_id.yml`
20. `field.field.node.character.field_voice_speed.yml`
21. `field.field.node.character.field_voice_pitch.yml`

### Field Instance Files (Paragraphs)
1. `field.field.paragraph.class.field_subclass.yml`
2. `field.field.paragraph.spell_slot.field_spell_level.yml`
3. `field.field.paragraph.spell_slot.field_spell_slots_total.yml`
4. `field.field.paragraph.spell_slot.field_spell_slots_available.yml`
5. `field.field.paragraph.relationship.field_related_character.yml`
6. `field.field.paragraph.relationship.field_relationship_type.yml`
7. `field.field.paragraph.relationship.field_relationship_description.yml`
8. `field.field.paragraph.relationship.field_relationship_strength.yml`

### Form Display Files
1. `core.entity_form_display.node.character.default.yml` (updated)
2. `core.entity_form_display.paragraph.class.default.yml` (updated)
3. `core.entity_form_display.paragraph.spell_slot.default.yml` (new)
4. `core.entity_form_display.paragraph.relationship.default.yml` (new)

---

## Next Steps to Apply Changes

1. **Start DDEV** (if not already running):
   ```bash
   ddev start
   ```

2. **Import the configuration**:
   ```bash
   ddev drush cim -y
   ```

3. **Clear cache**:
   ```bash
   ddev drush cr
   ```

4. **Verify fields** by editing a character node in Drupal admin

---

## Field Groups in Form Display

The character edit form is now organized into tabs:

1. **Character Details** - Name, identity, background, personality
2. **Game Abilities** - Ability scores, class, level, combat stats
3. **Equipment** - Weapons, armor, items, gold (NEW)
4. **Spells** - Spell slots, magic items (NEW)
5. **Abilities** - Class abilities, feats, specialized abilities, plot actions (NEW)
6. **Relationships** - Character relationships (NEW)
7. **AI Configuration** - AI settings (NEW)
8. **Voice** - TTS voice settings (NEW)

---

## Notes

- Equipment fields are organized as simple text fields (multiple values) rather than entity references, matching the JSON structure
- Spell slots use a paragraph type to track level, total slots, and available slots
- Relationships use a paragraph type to track target character, type, description, and strength
- AI and Voice configuration fields are optional and default to sensible values
- All new fields have appropriate validation (min/max values where applicable)
