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
  `field_ability_scores`, `field_skills`, `field_tools`, `field_languages`
  (-> `languages`), `field_spells_ref`, `field_campaign`,
  `field_character_type`, `field_ai_enabled` / `field_ai_model` /
  `field_ai_temperature` / `field_ai_max_tokens` / `field_ai_system_prompt`,
  `field_voice_id_ref` / `field_voice_pitch` / `field_voice_speed`,
  `field_personality_traits`, `field_bonds`, `field_ideals`, `field_flaws`,
  `field_major_plot_actions`, `field_relationships`.
- **story** — `field_body`, `field_story_number`, `field_campaign`,
  `field_session_date`, `field_session_results`, `field_story_hooks`,
  `field_locations`, `field_npcs`, `field_story_tags`.
- **item** — `field_item_type` (weapon/armor/item), `field_description`
  (a `wysiwyg` paragraph), `field_item_rarity`, `field_is_magic`,
  `field_item_properties`, `field_damage` / `field_damage_types`,
  `field_armor_*`, `field_weapon_*`, `field_item_cost`, `field_source`,
  `field_edition`. (`field_notes` was removed from the item bundle — it is now
  only on `character`.)
- **monster** — `field_challenge_rating`, `field_ability_scores`,
  `field_armor_class`, `field_maximum_hitpoints`, `field_monster_*` (actions,
  traits, senses, languages, legendary/lair actions), `field_type`.

---

## GraphQL exposure (`graphql_compose`)

Exposure is configured in
`drupal-cms/config/sync/graphql_compose.settings.graphql_compose_server.yml`.

**Exposed node bundles:** `character`, `story`, `item`, `spell`, `monster`,
`session` (each with `query_load_enabled`, `edges_enabled`, `simple_queries`).

**Tools (`TermToolProfiency`)** carry `field_tool_category` (list:
`artisan`/`other`/`gaming_set`/`musical_instrument`), seeded from the rules wiki.
A "choose any Musical Instrument / Gaming Set / Artisan's Tools" proficiency
resolves to a choice from that category's members (read from the taxonomy, not a
hardcoded list). A character proficient with a physical tool also **owns** it:
`createCharacter` adds the matching `item` node to `field_equipment_items` (one
per proficiency, deduplicated against the equipment package). The item's
description is resolved from the tool's rules-wiki entry — gaming sets and
musical instruments share their category's "(Varies)" description; artisan and
other tools have individual ones. A background whose tool proficiency is "choose
one kind of Musical Instrument / Gaming Set / Artisan's Tools" surfaces it as a
wizard tool **choice** from that category (not a literal "Choose one kind of…"
term).

**Exposed taxonomy vocabularies:** `abilities`, `campaign`, `class`, `skills`,
`species`, `lineage`, `backgrounds`, `feats`, `feat_type`, `ability_scores`,
`tool_profiencies`, `creature_types`, `factions`, `game_edition`,
`magical_properties`. A vocabulary must be listed here with `enabled: true`
before its term type appears in `TermUnion`.

**Term collection queries:** `abilities`, `class`, `skills`, `species`,
`lineage`, `backgrounds`, `feats`, `ability_scores`, and `tool_profiencies` set
`edges_enabled` + `simple_queries`, generating collection queries (`termClasses`,
`termSkills`, `termSpeciesItems`, `termLineages`, `termBackgrounds`, `termFeats`,
`termAbilityScores`, `termToolProfiencies`) consumed by the character-creation
wizard. Note the uncountable-noun quirk: the `species` collection is
`termSpeciesItems`, not `termSpecies`.

**Abilities (`TermAbility`)** carry the ability rules text and metadata:
`field_ability_description` (text), `field_ability_source_type` (list:
species/subspecies/class/background/feat), `field_ability_level` (int), and
`field_edition` (-> `game_edition`). Terms are created on demand during
character creation (see below).

**Backgrounds (`TermBackground`)** carry what a 2024 background grants:
`field_skills` (-> `skills`), `field_tools` (-> `tool_profiencies`), `field_feat`
(origin feat -> `feats`), `field_ability_options` (-> `ability_scores`, the
increase choices), `field_gold` (int) + `field_equipment_items` (-> `item` nodes;
same shape as the character node so the data transfers directly), and
`field_edition`. These term-level storages (`field_skills`, `field_tools`,
`field_feat`, `field_ability_options`, `field_gold`, `field_equipment_items`) are
shared across vocabularies — note that field storages are scoped per entity type,
so these are distinct from the identically named `node.*` storages.

When the creation wizard's background selector uses "Other (not on the list)", a
modal collects a homebrew definition (3 ability options, skills, tools, an
Origin-tagged feat, gold, equipment); `createCharacter` then upserts the
background term with those fields, `field_edition = Homebrew`, and find-or-creates
`item` nodes for the equipment package. New `item` nodes are typed
(weapon/armor/item) and given a `field_description` (a `wysiwyg` paragraph) from
the rules-wiki equipment catalogue when the payload carries an
`equipment_descriptions` map (see the data flow below); existing items are
reused untouched. The modal sources its options from
`termAbilityScores`, `termSkills`, `termToolProfiencies`, and `termFeats`
(filtered to `featType` = Origin) — `feats`, `feat_type`, `ability_scores`, and
`tool_profiencies` are exposed as term collections for this.

**Exposed paragraph types:** `ability_score`, `ability_scores`, `class`,
`class_grant`, `session_summary`, `arc_metric`, `arc_relationship`, `arc_goal`,
`spell_reference`, `spell_slot`, `relationship`, `wysiwyg`.

### Character arc analysis

The character node carries scalar arc fields `field_arc_direction`,
`field_arc_stage`, `field_arc_summary`, `field_arc_stories`,
`field_arc_updated`, plus three paragraph collections: `field_arc_metrics`
(-> `arc_metric`: `field_metric_key`/`field_metric_label`/
`field_metric_direction`/`field_metric_series` [comma-separated] /
`field_metric_obs`), `field_arc_relationships` (-> `arc_relationship`:
target/type/strength/trust/note), and `field_arc_goals` (-> `arc_goal`:
description/status/progress). Written by the `saveCharacterArc` mutation from a
JSON payload produced by the sidecar `/character/arc` endpoint; read back via
the camelCase `arcDirection`/`arcMetrics`/... fields on `NodeCharacter`.

### Campaign summaries (`session_summary` paragraph)

The `campaign` vocab carries `field_session_summaries` (-> `session_summary`
paragraphs, one per session) and `field_campaign_overview` (-> a single
`wysiwyg` paragraph holding the synthesized "story so far"). A `session_summary`
paragraph has `field_story_number` (int) + `field_text` (the recap). Exposed as
`sessionSummaries` (`ParagraphSessionSummary` with `storyNumber` + `text`) and
`campaignOverview` on `TermCampaign`. Both are written by the
`setSessionSummary` mutation (see below): `create-story.ts` summarises each new
session with the fast LLM and refreshes the overview; the gitignored
`frontend/scripts/backfill-summaries.mjs` backfills existing campaigns.

### Class grants (`class_grant` paragraph)

The `class` and `subclasses` taxonomies are the source of truth for what a class
grants per level. Each carries `field_class_grants` (-> `class_grant`
paragraphs); the `subclasses` vocab also carries `field_class` (-> `class`,
its parent) so its term knows which class it belongs to. A `class_grant`
paragraph has `field_level` (int), `field_grant_kind` (list: `skill_choice`,
`tool_choice`, `equipment_choice`, `feature`, `fixed_skill`, `fixed_tool`,
`subclass_choice`, `asi`, `expertise`), `field_choose_count` (int),
`field_skills` (-> `skills`), `field_tools` (-> `tool_profiencies`),
`field_equipment_items` (-> `item` nodes, option A), `field_gold` (int, option B),
`field_ability` (-> `abilities`), `field_feat` (-> `feats`), and `field_text`
(label / feature name). The `class`/`subclasses` collections are exposed
(`termClasses`, `termSubclasses`).

These terms are populated by gitignored seed scripts under `drupal-cms/scripts/`
(`build_class_specs.py` gathers per-class data from the JSON templates + rules
wiki; `seed_class_grants.php` and `seed_subclasses.php` materialise the grant
paragraphs). The sidecar's class-plan resolver reads them (see
[../src/sidecar/README.md](../src/sidecar/README.md)).

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
| `setSessionSummary` | `frontend/src/api/create-story.ts` + `scripts/backfill-summaries.mjs` |
| `saveCharacterArc` | `frontend/src/api/save-arc.ts` |
| `createCharacter` | `frontend/src/api/create-character.ts` |
| `updateCharacter` | `frontend/src/api/update-voice.ts` (voice id / pitch / speed) |

`createCharacter` persists a **source** character (`field_source_character =
TRUE`, no campaign) from a sidecar-derived payload, building the
`ability_scores`, `class`, `spell_slot`, `abilities_ref`, and `wysiwyg`
paragraphs. Unknown `species`/`background` names are created on the fly
(`findOrCreateTerm`). The payload's resolved `abilities` (class/species/
subspecies features from the rules wiki at `RAG_RULES_BASE_URL`) are upserted as `abilities` terms —
created on first use with their rules text, `source_type`, `level`, and
`edition` — and linked via `ability_reference` paragraphs. It also applies sensible AI/voice defaults
(`field_ai_enabled = TRUE`, default Piper voice `en_US-ryan-low`, speed 1.0,
pitch 0, and a character-derived system prompt); `field_ai_model`,
`field_ai_temperature`, and `field_ai_max_tokens` are left empty so they inherit
the global AI config. Equipment from the background package is created as `item`
nodes typed weapon/armor/item and given a `field_description` paragraph: before
calling the mutation, `create-character.ts` resolves the equipment names through
the sidecar's `/character/equipment/describe` (rules-wiki equipment catalogue at
`RAG_RULES_BASE_URL`) and passes the result as an `equipment_descriptions` map
in the payload. The clone into the active campaign is a separate
`addCharacterToCampaign` call.

`setSessionSummary(campaignId, storyNumber, summary, overview)` upserts the
`session_summary` paragraph for that story number on the campaign's
`field_session_summaries` (updating in place when the story number already
exists), and — when `overview` is supplied — replaces
`field_campaign_overview` with a `wysiwyg` paragraph. It returns the campaign's
`sessionSummaries`
so the caller can synthesize the overview from every recap. Requires the
`gatsby_user` role's `edit terms in campaign` permission.

`saveCharacterArc(id, payload)` takes the JSON arc result, sets the scalar arc
fields, and rebuilds the `arc_metric` / `arc_relationship` / `arc_goal`
paragraph collections on the character (requires `edit any character content`).
Note: a GraphQL DataProducer returning an entity must declare its `produces`
context as `data_type: "any"` (a plain `ContextDefinition`), never
`"entity:node"` — the latter trips an `EntityContextDefinition` assertion that
breaks the whole schema build.

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
