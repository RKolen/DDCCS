# Drupal Layer

Drupal CMS (`drupal-cms/`) is the **source of truth** for all content. It runs
headless: editors and the Python engine write to it, and the Gatsby frontend
reads from it over GraphQL. This document covers the project-specific schema and
how data flows in and out.

> For DDEV commands, PHP code quality (PHPCS + PHPStan level 6), the contrib
> patch policy, and the non-negotiable "Drupal is the source of truth for field
> names and GraphQL types" rule, see
> [drupal-cms/AGENTS.md](../drupal-cms/AGENTS.md). The stock
> `drupal-cms/README.md` is upstream Drupal CMS documentation and is not
> project-specific.

---

## Content types (node bundles)

Defined in `drupal-cms/config/sync/node.type.*.yml`:

| Bundle | Purpose | GraphQL-exposed |
| ------ | ------- | --------------- |
| `character` | Player characters **and NPCs** (see below) | Yes |
| `story` | Session narratives | Yes |
| `item` | Items / equipment (incl. homebrew) | Yes |
| `monster` | Statblocks | Yes |
| `spell` | Spells (incl. homebrew) | Yes |
| `session` | Session records | Yes |
| `ability` | Ability/feature reference entries | No |
| `wiki_cache` | Cached RAG wiki content | No |
| `basic_page` | Static site pages | No |

### NPCs are character nodes

There is **no separate NPC bundle.** NPCs are `character` nodes distinguished by
`field_character_type` (and related flags such as `field_recurring`,
`field_source_character`). Any legacy `nodeNpcs` / `Drupal_NodeNpc` GraphQL type
is **deprecated** — query NPCs through the character type and filter on
`field_character_type`.

### Key fields

Full field sets live in
`drupal-cms/config/sync/field.field.node.<bundle>.<field>.yml`. Highlights:

- **character** — `field_first_name`, `field_last_name`, `field_class`,
  `field_level`, `field_lineage`, `field_species`, `field_background`,
  `field_ability_scores`, `field_skills`, `field_spells_ref`, `field_campaign`,
  `field_character_type`, `field_ai_enabled` / `field_ai_model` /
  `field_ai_temperature` / `field_ai_max_tokens` / `field_ai_system_prompt`,
  `field_voice_id_ref` / `field_voice_pitch` / `field_voice_speed`,
  `field_personality_traits`, `field_bonds`, `field_ideals`, `field_flaws`,
  `field_major_plot_actions`, `field_relationships`.
- **story** — `field_body`, `field_story_number`, `field_campaign`,
  `field_session_date`, `field_session_results`, `field_story_hooks`,
  `field_locations`, `field_npcs`, `field_story_tags`.
- **item** — `field_item_type`, `field_item_rarity`, `field_is_magic`,
  `field_item_properties`, `field_damage` / `field_damage_types`,
  `field_armor_*`, `field_weapon_*`, `field_item_cost`, `field_source`.
- **monster** — `field_challenge_rating`, `field_ability_scores`,
  `field_armor_class`, `field_maximum_hitpoints`, `field_monster_*` (actions,
  traits, senses, languages, legendary/lair actions), `field_type`.

---

## GraphQL exposure (`graphql_compose`)

Exposure is configured in
`drupal-cms/config/sync/graphql_compose.settings.graphql_compose_server.yml`.

**Exposed node bundles:** `character`, `story`, `item`, `spell`, `monster`,
`session` (each with `query_load_enabled`, `edges_enabled`, `simple_queries`).

**Exposed taxonomy vocabularies:** `abilities`, `campaign`, `class`, `skills`,
`species`, `lineage`, `backgrounds`, `creature_types`, `factions`,
`game_edition`, `magical_properties`. A vocabulary must be listed here with
`enabled: true` before its term type appears in `TermUnion`.

**Term collection queries:** `abilities`, `class`, `skills`, `species`,
`lineage`, and `backgrounds` set `edges_enabled` + `simple_queries`, generating
collection queries (`termClasses`, `termSkills`, `termSpeciesItems`,
`termLineages`, `termBackgrounds`) consumed by the character-creation wizard.
Note the uncountable-noun quirk: the `species` collection is `termSpeciesItems`,
not `termSpecies`.

**Abilities (`TermAbility`)** carry the ability rules text and metadata:
`field_ability_description` (text), `field_ability_source_type` (list:
species/subspecies/class/background/feat), `field_ability_level` (int), and
`field_edition` (-> `game_edition`). Terms are created on demand during
character creation (see below).

**Exposed paragraph types:** `ability_score`, `ability_scores`, `class`,
`spell_reference`, `spell_slot`, `relationship`, `wysiwyg`.

After editing this config:

```bash
ddev drush config:import -y && ddev drush cache:rebuild
cd ../frontend && npm run clean      # so Gatsby re-pulls the schema
```

Field names in GraphQL are **camelCase without the `field_` prefix**
(e.g. `field_story_number` -> `storyNumber`).

### Verifying the schema

```graphql
# Introspect a type at
{ __type(name: "NodeCharacter") { fields { name type { name } } } }
```

---

## Data flow

### Reads — Gatsby <- Drupal

`gatsby-source-graphql` stitches the Drupal schema into Gatsby. Page and
template queries read content under the `drupal` field. See
[frontend/README.md](../frontend/README.md).

### Writes — user edits via Gatsby serverless functions

Per-action user writes go through custom GraphQL mutations called from
`frontend/src/api/`:

| Mutation | Called by |
| -------- | --------- |
| `createCampaign` | `frontend/src/api/campaigns.ts` |
| `addCharacterToCampaign` | `frontend/src/api/campaign-party.ts` |
| `createStory` | `frontend/src/api/create-story.ts` |
| `createCharacter` | `frontend/src/api/create-character.ts` |
| `updateCharacter` | `frontend/src/api/update-character.ts` |

`createCharacter` persists a **source** character (`field_source_character =
TRUE`, no campaign) from a sidecar-derived payload, building the
`ability_scores`, `class`, `spell_slot`, `abilities_ref`, and `wysiwyg`
paragraphs. Unknown `species`/`background` names are created on the fly
(`findOrCreateTerm`). The payload's resolved `abilities` (class/species/
subspecies features from the rules wiki) are upserted as `abilities` terms —
created on first use with their rules text, `source_type`, `level`, and
`edition` — and linked via `ability_reference` paragraphs. It also applies sensible AI/voice defaults
(`field_ai_enabled = TRUE`, default Piper voice `en_US-ryan-low`, speed 1.0,
pitch 0, and a character-derived system prompt); `field_ai_model`,
`field_ai_temperature`, and `field_ai_max_tokens` are left empty so they inherit
the global AI config. The clone into the active campaign is a separate
`addCharacterToCampaign` call.

### Writes — bulk/seed via the engine

The Python engine pushes content into Drupal through
`src/integration/drupal_sync.py`:

- `push_character(character_file)`
- `push_story(story_file, campaign)`
- `push_item(item_data, skip_existing=True)`
- `push_monster(monster_data, skip_existing=True)`
- `trigger_gatsby_build()`

This is the path used to seed or batch-sync engine-side JSON into Drupal.

---

## See also

- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — how Drupal fits the three tiers.
- [drupal-cms/AGENTS.md](../drupal-cms/AGENTS.md) — DDEV/PHP rules and the
  source-of-truth policy.
- `drupal-cms/config/sync/REUSABLE_FIELDS_ARCHITECTURE.md` and
  `NEW_FIELDS_SUMMARY.md` — field design notes.
