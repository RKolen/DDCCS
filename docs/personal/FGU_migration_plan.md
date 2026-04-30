# FGU to Drupal Migration Plan

Migrate items and NPCs/monsters from Fantasy Grounds Unity (FGU) to the Drupal
CMS instance, making them available to the Gatsby frontend.

## Background

FGU on Linux stores campaign data at:
`~/.smiteworks/fgdata/campaigns/New beginnings/db.xml`

Two push paths are needed:

- **Python live-sync** (incremental delta pushes from the CLI)
- **Drupal Migrate API** (bulk initial import, handles paragraph sub-entities
  correctly)

### Critical distinction: FGU "NPCs" are monster stat blocks

FGU's `<npc>` root element contains creature/monster stat blocks (AC, HP, CR,
actions, traits etc.). These map to `node.monster` in Drupal, NOT `node.npc`.

The CLI's `game_data/npcs/*.json` files are rich narrative profiles (backstory,
personality, relationships, plot hooks). These map to `node.npc` and are
already handled by the existing `dnd_npc_*` migrations. That pipeline must not
be changed.

---

## What is actually in the FGU db.xml

Verified against `New beginnings/db.xml` (59 items, 6 monster stat blocks).

### FGU item fields (all 59 items surveyed)

| FGU tag       | Count | Notes                                          |
| ------------- | ----- | ---------------------------------------------- |
| `name`        | 59    | Always present                                 |
| `type`        | 59    | Adventuring Gear / Amulet / Armor / Weapon / Wondrous Item |
| `description` | 59    | `formattedtext` with HTML children             |
| `weight`      | 59    | number, can be 0                               |
| `version`     | 59    | Always "2024"                                  |
| `locked`      | 59    | Internal FGU flag, skip                        |
| `rarity`      | 58    | Encodes both rarity and attunement (see below) |
| `picture`     | 56    | Token path string, skip for now                |
| `cost`        | 54    | String e.g. "1200 gp"                         |
| `nonid_name`  | 54    | Unidentified display name                      |
| `nonidentified` | 48  | Description shown before identified            |
| `properties`  | 29    | Comma-separated property tags                  |
| `subtype`     | 27    | Weapon/armor sub-category                      |
| `bonus`       | 21    | Enhancement bonus integer (+1/+2/+3)           |
| `damage`      | 17    | e.g. "2d6 Slashing"                           |
| `mastery`     | 16    | e.g. "Graze, Cleave, Topple"                  |
| `attune`      | 16    | `"1"` when item requires attunement            |
| `carried`     | 16    | Inventory state, skip                          |
| `count`       | 16    | Stack count, skip                              |
| `spells`      | 12    | Child nodes listing spells, skip for now       |
| `ac`          | 4     | Armor AC value                                 |
| `dexbonus`    | 4     | Max Dex bonus for armor                        |
| `stealth`     | 4     | Stealth disadvantage flag                      |
| `strength`    | 4     | Armor Str requirement                          |
| `isidentified` | 3    | Internal FGU state, skip                      |

### FGU npc (monster) fields

| FGU tag             | Notes                                              |
| ------------------- | -------------------------------------------------- |
| `name`              | Always present                                     |
| `type`              | Creature type e.g. "Fiend (Devil)"                |
| `size`              | Tiny / Small / Medium / Large / Huge / Gargantuan  |
| `alignment`         | e.g. "Lawful Evil"                                |
| `cr`                | String, may be "0", "1", "1/2", "1/4"            |
| `ac`                | Integer                                            |
| `hp`                | Integer                                            |
| `hd`                | Hit dice string e.g. "(6d4 + 6)"                 |
| `xp`                | Integer                                            |
| `speed`             | String e.g. "20 ft., Fly 40 ft."                 |
| `senses`            | String                                             |
| `languages`         | String                                             |
| `skills`            | String e.g. "Deception +4, Insight +3"           |
| `abilities`         | 6 child nodes (strength/dex/con/int/wis/cha) each with score, bonus, savemodifier |
| `actions`           | Child nodes each with `name` + `desc`             |
| `bonusactions`      | Child nodes each with `name` + `desc`             |
| `reactions`         | Child nodes each with `name` + `desc`             |
| `traits`            | Child nodes each with `name` + `desc`             |
| `legendaryactions`  | Child nodes each with `name` + `desc`             |
| `lairactions`       | Child nodes each with `name` + `desc`             |
| `damageimmunities`  | String                                             |
| `damageresistances` | String                                             |
| `damagethreshold`   | Integer, skip (niche)                             |
| `picture`           | Token path, skip for now                          |
| `token`             | Token path, skip for now                          |
| `text`              | Formatted stat block HTML, redundant with fields  |
| `innatespells`      | May be null                                        |
| `spells`            | May be null                                        |
| `spellslots`        | Child nodes for slot counts                        |
| `summon_*`          | Summoning stats, skip (internal FGU)              |

---

## Step 1 - Extend Drupal Content Types

**Side:** Drupal/PHP (DDEV)

### 1A - Item content type additions

The existing `node.item` already has most fields. Only add what is genuinely
missing after mapping (see Step 3A for why these are needed):

| New field machine name   | FGU tag      | Drupal type | Notes                     |
| ------------------------ | ------------ | ----------- | ------------------------- |
| `field_item_cost`        | `cost`       | `string`    | e.g. "1200 gp"           |
| `field_item_weight`      | `weight`     | `decimal`   | in pounds                 |
| `field_item_bonus`       | `bonus`      | `integer`   | enhancement bonus +1/+2/+3 |
| `field_nonidentified_name` | `nonid_name` | `string`  | unidentified display name |

Also extend the `field_item_type` allowed values list to cover all FGU types:

| Add to allowed values | Label           |
| --------------------- | --------------- |
| `wondrous_item`       | Wondrous Item   |
| `adventuring_gear`    | Adventuring Gear |
| `amulet`              | Amulet          |

### 1B - Monster content type additions

The existing `node.monster` has stat-block numerics but is missing all the
textual combat blocks that FGU provides:

| New field machine name          | FGU tag            | Drupal type   |
| ------------------------------- | ------------------ | ------------- |
| `field_monster_size`            | `size`             | `list_string` |
| `field_monster_alignment`       | `alignment`        | `string`      |
| `field_monster_speed`           | `speed`            | `string`      |
| `field_monster_senses`          | `senses`           | `string`      |
| `field_monster_languages`       | `languages`        | `string`      |
| `field_monster_skills`          | `skills`           | `string`      |
| `field_monster_hit_dice`        | `hd`               | `string`      |
| `field_monster_xp`              | `xp`               | `integer`     |
| `field_monster_actions`         | `actions`          | `text_long`   |
| `field_monster_bonus_actions`   | `bonusactions`     | `text_long`   |
| `field_monster_reactions`       | `reactions`        | `text_long`   |
| `field_monster_traits`          | `traits`           | `text_long`   |
| `field_monster_legendary_actions` | `legendaryactions` | `text_long` |
| `field_monster_lair_actions`    | `lairactions`      | `text_long`   |
| `field_monster_damage_immunities` | `damageimmunities` | `string`    |
| `field_monster_damage_resistances` | `damageresistances` | `string`  |
| `field_source`                  | (campaign name)    | `string`      |

`field_monster_size` allowed values: `tiny`, `small`, `medium`, `large`,
`huge`, `gargantuan`.

**Implementation:** Create field storage and field instance YAML files in
`drupal-cms/web/modules/custom/dnd_migrate/config/install/`, then export with
`ddev drush cex`.

---

## Step 2 - FGU XML Parser

**File:** `src/integration/fgu_xml_parser.py`

Pure Python, stdlib `xml.etree.ElementTree` only. Lives in `src/integration/`
because it is FGU-specific.

```python
class FguXmlParser:
    def __init__(self, db_xml_path: Path, campaign: str = "") -> None: ...

    def iter_items(self) -> Iterator[Dict[str, Any]]:
        """Yield one normalized item dict per FGU <item> node."""

    def iter_monsters(self) -> Iterator[Dict[str, Any]]:
        """Yield one normalized monster dict per FGU <npc> node."""
```

### 2A - Normalized item dict keys

```
name, item_type, subtype, cost, weight, bonus, description_html,
rarity, attunement, attunement_restriction, damage, damage_type,
properties, mastery, nonid_name, nonidentified,
ac, dex_bonus, stealth_disadvantage, str_requirement,
version, source_campaign
```

**Rarity parsing** - FGU encodes both rarity and attunement in one string:

| FGU rarity string                           | Drupal rarity  | attunement |
| ------------------------------------------- | -------------- | ---------- |
| `"common"` / `"Common"`                     | `common`       | false      |
| `"Uncommon"`                                | `uncommon`     | false      |
| `"Rare"` / `"rare (requires attunement)"`   | `rare`         | depends    |
| `"Legendary"`                               | `legendary`    | false      |
| `"Legendary (Requires Attunement)"`         | `legendary`    | true       |
| `"Legendary (Requires Attunement By A X)")` | `legendary`    | true       |

Parse by: lowercasing, stripping the `(Requires Attunement...)` suffix to get
base rarity, setting `attunement=True` if suffix was present OR if the
`attune` field equals `"1"`. Store the class restriction (e.g. "By A Bard")
in `attunement_restriction` for the notes field.

**Item type mapping** (`_ITEM_TYPE_MAP` decision table at module level):

| FGU `type`        | Drupal `field_item_type` |
| ----------------- | ------------------------ |
| `Weapon`          | `weapon`                 |
| `Armor`           | `armor`                  |
| `Wondrous Item`   | `wondrous_item`          |
| `Adventuring Gear` | `adventuring_gear`      |
| `Amulet`          | `amulet`                 |

**Description extraction:** FGU `description` is `formattedtext` with HTML
children (`<p>`, `<h>`, `<b>` etc.). Use
`ET.tostring(el, encoding="unicode", method="text")` to strip tags and get
plain text for `field_notes`. This avoids the paragraph sub-entity complexity.

### 2B - Normalized monster dict keys

```
name, creature_type, size, alignment, cr, ac, hp, hit_dice, xp, speed,
str_score, dex_score, con_score, int_score, wis_score, cha_score,
str_bonus, dex_bonus, con_bonus, int_bonus, wis_bonus, cha_bonus,
skills, senses, languages,
actions_text, bonus_actions_text, reactions_text,
traits_text, legendary_actions_text, lair_actions_text,
damage_immunities, damage_resistances,
source_campaign
```

**Ability score parsing:** FGU `abilities` has 6 child nodes in order
(strength, dexterity, constitution, intelligence, wisdom, charisma). Each
has `score`, `bonus`, and `savemodifier` sub-elements. Iterate by position
rather than by tag name since FGU uses positional ordering.

**Action block flattening:** For `actions`, `bonusactions`, `reactions`,
`traits`, `legendaryactions`, `lairactions` - each child node has `name` and
`desc` sub-elements. Flatten to:
`"<Name>\n<Desc>\n\n<Name2>\n<Desc2>\n\n..."` for readability in Drupal's
`text_long` fields.

**CR conversion:** Use `float(Fraction(cr_str))` from stdlib `fractions`.
Handles `"0"`, `"1"`, `"1/2"`, `"1/4"`, `"1/8"` cleanly.

### 2C - Implementation rules

- Use `element.findtext("field", default="")` on all optional fields.
- Never access `.text` directly on a potentially-missing element.
- Define `_ITEM_TYPE_MAP` and `_SIZE_MAP` as module-level constants.
- Skip `locked`, `carried`, `count`, `isidentified`, `summon_*`, `text`,
  `token`, `token3Dflat` fields entirely.

---

## Step 3 - Field Mapping (Static Methods on DrupalSync)

**File:** `src/integration/drupal_sync.py` (additions)

Static methods following the existing `build_character_payload()` pattern.

### 3A - `build_item_payload(data: Dict[str, Any]) -> Dict[str, Any]`

| JSON:API attribute             | Source key              | Notes                                    |
| ------------------------------ | ----------------------- | ---------------------------------------- |
| `title`                        | `name`                  | Required                                 |
| `field_item_type`              | `item_type`             | From `_ITEM_TYPE_MAP`                    |
| `field_is_magic`               | derived                 | True if rarity is uncommon or higher     |
| `field_item_rarity`            | `rarity`                | Drupal slug from rarity parsing          |
| `field_item_requires_attunement` | `attunement`          | bool                                     |
| `field_notes`                  | `description_html` + `attunement_restriction` | Plain text + class restriction appended |
| `field_damage`                 | `damage`                | string e.g. "2d6 Slashing"             |
| `field_weapon_subtype`         | `subtype`               | For weapons                              |
| `field_weapon_mastery`         | `mastery`               | string                                   |
| `field_weapon_properties`      | `properties`            | string                                   |
| `field_armor_ac_base`          | `ac`                    | int, only set if item_type is armor      |
| `field_armor_str_requirement`  | `str_requirement`       | int                                      |
| `field_armor_category`         | `subtype`               | For armor (Heavy Armor etc.)             |
| `field_item_cost`              | `cost`                  | string                                   |
| `field_item_weight`            | `weight`                | decimal                                  |
| `field_item_bonus`             | `bonus`                 | int                                      |
| `field_nonidentified_name`     | `nonid_name`            | string                                   |
| `field_edition`                | `version`               | string "2024"                            |

`field_is_magic` logic:

```python
_MAGIC_RARITIES = {"uncommon", "rare", "very_rare", "legendary", "artifact", "vestige"}
is_magic = data.get("rarity", "") in _MAGIC_RARITIES
```

### 3B - `build_monster_payload(data: Dict[str, Any]) -> Dict[str, Any]`

Maps FGU `<npc>` nodes to `node.monster`. Does NOT touch `node.npc` — that
content type is reserved for CLI-sourced narrative NPC profiles.

| JSON:API attribute                    | Source key               | Notes                          |
| ------------------------------------- | ------------------------ | ------------------------------ |
| `title`                               | `name`                   | Required                       |
| `field_challenge_rating`              | `cr`                     | float via Fraction             |
| `field_armor_class`                   | `ac`                     | int                            |
| `field_maximum_hitpoints`             | `hp`                     | int                            |
| `field_movement_speed`                | `speed` (numeric)        | int, parse first number from string |
| `field_monster_speed`                 | `speed`                  | full string                    |
| `field_monster_size`                  | `size`                   | lowercase slug                 |
| `field_monster_alignment`             | `alignment`              | string                         |
| `field_monster_senses`                | `senses`                 | string                         |
| `field_monster_languages`             | `languages`              | string                         |
| `field_monster_skills`                | `skills`                 | string                         |
| `field_monster_hit_dice`              | `hit_dice`               | string                         |
| `field_monster_xp`                    | `xp`                     | int                            |
| `field_specialized_abilities`         | `traits_text`            | text_long (existing field)     |
| `field_monster_actions`               | `actions_text`           | text_long                      |
| `field_monster_bonus_actions`         | `bonus_actions_text`     | text_long                      |
| `field_monster_reactions`             | `reactions_text`         | text_long                      |
| `field_monster_legendary_actions`     | `legendary_actions_text` | text_long                      |
| `field_monster_lair_actions`          | `lair_actions_text`      | text_long                      |
| `field_monster_damage_immunities`     | `damage_immunities`      | string                         |
| `field_monster_damage_resistances`    | `damage_resistances`     | string                         |
| `field_source`                        | `source_campaign`        | string                         |

Note: `field_ability_scores` is a paragraph sub-entity (entity_reference_revisions).
The Python push path skips it and logs a warning. The Migrate API path (Step 5)
handles it via the ability scores sub-migration. `field_type` (taxonomy term for
creature type) is also skipped in the Python path - handled in Step 5.

---

## Step 4 - New DrupalSync Methods

**File:** `src/integration/drupal_sync.py`

```python
def push_item(self, item_data: Dict[str, Any]) -> str:
    """Push a single parsed FGU item to Drupal as a node/item node."""

def push_monster(self, monster_data: Dict[str, Any]) -> str:
    """Push a single parsed FGU npc stat block to Drupal as a node/monster node."""
```

Both delegate to a new private `_upsert_node(node_type, title, payload)`
helper. Refactor existing `push_character` and `push_story` to also use
`_upsert_node` to eliminate the R0801 duplicate-code violation.

---

## Step 5 - Drupal Migrate API (Bulk Import Path)

**Side:** Drupal/PHP (DDEV)

### 5A - Source plugin

**File:**
`drupal-cms/web/modules/custom/dnd_migrate/src/Plugin/migrate/source/DndFguXmlSource.php`

- Config: `db_xml_path` and `entity_type` (`item` or `npc` - matching the
  actual FGU root element tag names).
- Parses via PHP `SimpleXMLElement`.
- Yields one row per `id-XXXXX` child.
- Flattens action/reaction/trait child nodes to `"Name\nDesc\n\n"` text.
- Uses FGU internal key as source ID.
- PHPCS + PHPStan level 6.

### 5B - Migration YAML: items

**File:**
`drupal-cms/web/modules/custom/dnd_migrate/config/install/migrate_plus.migration.dnd_fgu_items.yml`

Source: `dnd_fgu_xml_source` with `entity_type: item`.
Destination: `entity:node` bundle `item`.
No sub-migration dependencies.

### 5C - Monster ability scores sub-migration

**File:**
`drupal-cms/web/modules/custom/dnd_migrate/config/install/migrate_plus.migration.dnd_fgu_monster_ability_scores.yml`

Maps `str_score`/`dex_score` etc. to `paragraph:ability_scores`.
Must run before 5D.

### 5D - Migration YAML: monsters

**File:**
`drupal-cms/web/modules/custom/dnd_migrate/config/install/migrate_plus.migration.dnd_fgu_monsters.yml`

Source: `dnd_fgu_xml_source` with `entity_type: npc`.
Destination: `entity:node` bundle `monster`.
Uses `entity_lookup` with `auto_create: true` for `field_type` taxonomy
against the `creature_types` vocabulary.
Depends on `dnd_fgu_monster_ability_scores`.

Run order: `dnd_fgu_monster_ability_scores` -> `dnd_fgu_items` ->
`dnd_fgu_monsters`

```bash
ddev drush migrate:import --group=dnd --execute-dependencies
```

---

## Step 6 - CLI Entry Point

**File:** `scripts/fgu_migrate.py`

Same pattern as `scripts/migrate_relationships.py`.

| Flag          | Description                                               |
| ------------- | --------------------------------------------------------- |
| `--db-xml`    | Path to FGU `db.xml` (required)                          |
| `--campaign`  | Campaign name tag written to `field_source`               |
| `--type`      | `items`, `monsters`, or `all` (default: `all`)            |
| `--dry-run`   | Parse and print normalized dicts without pushing          |

Default `--db-xml` path: `~/.smiteworks/fgdata/campaigns/New beginnings/db.xml`

---

## Step 7 - Tests

- `tests/integration/test_fgu_xml_parser.py` - covers parser with inline XML
  fixture constants (FGU db.xml is an external file, not game_data)
- `tests/integration/test_drupal_sync_fgu.py` - covers `build_item_payload`,
  `build_monster_payload`, `push_item`, `push_monster`

Shared helpers (`make_drupal_config`, `make_mock_urlopen`) go in
`tests/test_helpers.py` to avoid R0801.

All tests: Pylint 10.00/10, mypy clean, full type annotations, Google
docstrings.

---

## Step 8 - Documentation Updates

| Document | What to update |
| -------- | -------------- |
| `AGENTS.md` | Add `fgu_xml_parser.py` to integration section of Project Structure |
| `src/README.md` | Add `FguXmlParser` to `src/integration/` |
| `drupal-cms/AGENTS.md` | Add new migration YAMLs and `DndFguXmlSource` plugin; update run-order list |
| `tests/README.md` | Add rows for the two new test files |

---

## Sequencing

1. Step 1 - Drupal field additions (fields must exist before any push)
2. Step 2 - `fgu_xml_parser.py` (pure Python, testable immediately)
3. Step 3 - payload builder static methods (depends on Step 1 field names)
4. Step 4 - `push_item` and `push_monster` (depends on Steps 2 and 3)
5. Step 7 - Tests (after Steps 2-4)
6. Step 5A - PHP source plugin (parallel with Python work)
7. Steps 5B-5D - Migration YAMLs (after Step 5A and Step 1 config export)
8. Step 6 - CLI script (after Steps 2 and 4)
9. Step 8 - Documentation (last, single commit with code)

---

## Key Challenges

**Rarity string parsing:** FGU encodes rarity AND attunement in one string
with many variants. Parse by detecting the `(Requires Attunement...)` suffix,
stripping it for the base rarity slug, and setting `attunement=True`. Also
check the separate `attune` field as a fallback.

**`field_item_type` allowed values:** Must extend the Drupal list_string config
before import (Step 1A), otherwise unknown values will be rejected by JSON:API.

**CR fractions:** `float(Fraction("1/2"))` from stdlib `fractions` — no regex
needed.

**Ability score ordering:** FGU `abilities` child nodes are positional, not
named. Parse in index order: 0=STR, 1=DEX, 2=CON, 3=INT, 4=WIS, 5=CHA.

**R0801:** Extract `_upsert_node()` on `DrupalSync` for all four push methods.

**mypy:** Always use `findtext("tag", default="")` — never `.text` on an
`Optional[Element]`.

**NPC/monster separation:** FGU `<npc>` nodes go to `node.monster` only.
The CLI NPC JSON pipeline (`dnd_npc_*` migrations) stays unchanged.
