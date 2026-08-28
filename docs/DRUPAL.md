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
| `story_arc` | Multi-story campaign arc: premise, antagonist faction, party, relationship web | Yes |
| `character_analysis` | Per-(campaign, character) arc analysis record: stored per-story analysis prose + a synthesized summary | Yes |
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
  `field_major_plot_actions`, `field_relationships`, `field_faction`
  (-> `factions`, cardinality 1), `field_key_traits` (-> `traits`,
  cardinality -1).
  NPCs additionally use `field_recurring` plus the antagonist set
  `field_encounter_tactics`, `field_defeat_conditions`, `field_lair_actions`,
  `field_legendary_actions`, `field_regional_effects` — all `text_list`.
  `field_faction` and `field_key_traits` declare no target-bundle restriction in
  their field config, so the vocabulary they belong to is enforced by the
  mutation's `FIELD_MAP` rather than by Drupal's reference handler.
  `field_faction` holds a **real faction** (cardinality 1); the ally / neutral /
  BBEG axis lives on `field_role` — see "Story arcs" below.
  The four personality fields are all `text_long` with cardinality -1, so a
  bond or flaw can hold real prose rather than a one-line note. `field_bonds`,
  `field_ideals`, and `field_flaws` started as `text` (varchar 255) and were
  converted in place by the gitignored
  `drupal-cms/scripts/widen_personality_fields.php`; the GraphQL type is
  `[Text!]` either way, so nothing downstream changed.
- **story** — `field_body`, `field_story_number`, `field_campaign`,
  `field_session_date`, `field_session_results`, `field_story_hooks`,
  `field_locations`, `field_npcs`, `field_story_tags`, `field_story_arc`
  (-> the `story_arc` node this story belongs to), `field_characters_present`
  (-> `character` nodes). `field_characters_present` is **optional and means
  "narrow the scene"**: empty = the whole party is present, set = only these
  PCs, which is what lets Spotlight score a split party without loading all
  thirteen.
- **story_arc** — `field_campaign`, `field_body` (the full premise, not a
  one-liner), `field_overall_plot` (act structure / campaign spine),
  `field_level_range` (string, e.g. `4-10`), `field_target_stories` (int),
  `field_faction` (-> the antagonist faction term; its members resolve the
  antagonist roster), `field_npcs` and `field_party` (-> `character` nodes),
  and two `arc_relationship_pair` paragraph collections,
  `field_arc_party_relations` (party-internal bonds) and
  `field_arc_npc_relations` (party <-> NPC connections).
- **item** — `field_item_type` (weapon/armor/item, defaults to `item`, whose
  label is "Gear"), `field_description` (a `wysiwyg` paragraph),
  `field_item_rarity`, `field_is_magic`, `field_item_properties`,
  `field_damage` / `field_damage_types`, `field_armor_*`, `field_weapon_*`,
  `field_item_cost`, `field_source`, `field_edition`. (`field_notes` was
  removed from the item bundle — it is now only on `character`.)

  Melee vs ranged is **not** in `field_item_type`, which only distinguishes
  weapon/armor/gear. It lives in `field_weapon_range` (Melee/Ranged), paired
  with `field_weapon_category` (Simple/Martial). Both are single-value
  taxonomy references rendered as selects in the Weapon tab of the item form.
  They replaced `field_weapon_subtype`, one unlimited-cardinality autocomplete
  that carried both axes at once and which editors routinely half-filled,
  leaving ranged weapons indistinguishable from melee ones. Anything deriving
  a weapon's range must read `field_weapon_range` — never infer it from
  `field_item_type`.
- **monster** — `field_challenge_rating`, `field_ability_scores`,
  `field_armor_class`, `field_maximum_hitpoints`, `field_monster_*` (actions,
  traits, senses, languages, legendary/lair actions), `field_type`.

---

## GraphQL exposure (`graphql_compose`)

Exposure is configured in
`drupal-cms/config/sync/graphql_compose.settings.graphql_compose_server.yml`.

**Exposed node bundles:** `character`, `story`, `story_arc`, `item`, `spell`,
`monster` (each with `query_load_enabled`, `edges_enabled`, `simple_queries`).

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
`magical_properties`, `weapon_category`, `weapon_range`, `weapon_properties`,
`weapon_mastery`, `damage_types`, `vestige_level`, `traits`. A vocabulary must
be listed here with `enabled: true` before its term type appears in `TermUnion`.

**Term collection queries:** `abilities`, `class`, `skills`, `species`,
`lineage`, `backgrounds`, `feats`, `ability_scores`, `tool_profiencies`,
`factions`, and `traits` set `edges_enabled` + `simple_queries`, generating
collection queries (`termClasses`, `termSkills`, `termSpeciesItems`,
`termLineages`, `termBackgrounds`, `termFeats`, `termAbilityScores`,
`termToolProfiencies`, `termFactions`, `termTraits`) consumed by the
character-creation wizard and the profile editor. Note the uncountable-noun
quirk: the `species` collection is `termSpeciesItems`, not `termSpecies`.

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

The wizard offers whatever `backgrounds`, `species`, and `class` terms exist, so
those vocabularies define which options a player can pick. They are seeded from
the rules wiki by the gitignored scripts under `drupal-cms/scripts/`:
`build_catalog.py` enumerates the wiki's `background:all` / `species:all` /
`class:all` index pages, keeps the entries whose `Source:` line matches
`RAG_SOURCEBOOKS`, resolves each background's grants, and writes `catalog.json`;
`seed_catalog.php` then creates the missing terms and back-fills the background
fields, find-or-creating any `feats`, `tool_profiencies`, and `item` nodes they
reference. It is additive and idempotent: existing terms keep their identity and
only gain fields they are missing, so hand-authored and homebrew terms survive a
reseed. Wiki names use curly apostrophes where the taxonomy uses straight ones,
so the seeder compares normalised names rather than duplicating terms.

```bash
.venv/bin/python drupal-cms/scripts/build_catalog.py   # from the project root
ddev drush scr scripts/seed_catalog.php                # from drupal-cms/
cd ../frontend && npm run clean                        # re-pull the schema
```

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
`class_grant`, `session_summary`, `arc_metric`, `arc_relationship`,
`arc_relationship_pair`, `arc_goal`, `spell_reference`, `spell_slot`,
`relationship`, `wysiwyg`.

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

### Story arcs (`story_arc` node)

A `story_arc` is the plan a run of stories is written against — a premise that
spans levels and sessions, not a single session's narrative. Stories point at
their arc through `story.field_story_arc`; the arc points at its campaign
through `field_campaign`, so campaign -> arc -> story is the full chain.

**Antagonists are resolved through the faction, not a dedicated field.** The arc
carries `field_faction` (cardinality 1), and every antagonist `character` node
carries the same term. That keeps one source of truth: adding a member to the
faction adds them to every arc that opposes it. `field_npcs` on the arc is the
*curated* roster — who actually appears — and may be a subset.

`field_role` carries the ally / neutral / BBEG axis that the `factions` vocab
used to overload. The `factions` vocab is now for real factions only; its
leftover `ally`, `bbeg`, and `neutral` terms are unused.

### Arc relationships (`arc_relationship_pair` paragraph)

Distinct from `arc_relationship`, which hangs off a **character** and therefore
has an implicit source. `arc_relationship_pair` is arc-scoped and directed, so
it stores both ends: `field_pair_source` and `field_pair_target` (-> `character`
nodes), `field_pair_type` (short label), `field_pair_tier` (1 = direct and
personal, 2 = thematic, 3 = incidental), `field_pair_note` (the connection and
how to play it). Exposed as `ParagraphArcRelationshipPair` with `pairSource`,
`pairTarget`, `pairType`, `pairTier`, `pairNote`.

Keeping these on the arc rather than on `character.field_relationships` is
deliberate: the content is spoiler-bearing and arc-specific, and a directed pair
lets one record be read from either character's page.

### Character analysis record (`character_analysis` node)

A `character_analysis` node is a persistent, crash-safe analysis record **keyed
by character** — one record per character. The campaign is optional metadata (a
character may have no campaign of its own, so keying on campaign would be
fragile); it is stored when known and kept current. Title is
`"<character> · <campaign>"` when a campaign is known, else just `"<character>"`.
Fields: `field_campaign` (-> `campaign` term, optional), `field_character` (->
`character` node, the key), `field_story_analyses` (-> `session_summary`
paragraphs, one per story: `field_story_number` + `field_text` [prose,
`plain_text`] + `field_datapoint` [the structured per-story data point as a JSON
string, `string_long`]), and `field_analysis_summary` (`plain_text` text_long).
Exposed on `NodeCharacterAnalysi` (graphql_compose singularises "analysis") as
`campaign`, `character`, `storyAnalyses` (`ParagraphSessionSummary` with
`storyNumber` + `text` + `datapoint`), and `analysisSummary`. The `datapoint`
JSON is what lets synthesis recompute real metric trend lines (via
`aggregate_arc`) instead of only re-reading prose.

The console persists each story's analysis prose as it completes (via
`upsertCharacterAnalysis`), so a crashed arc run **resumes**: `get-analysis.ts`
reads back the stored `storyNumbers` to skip already-analysed stories, and
`synthesize-analysis.ts` reads the stored per-story prose to narrate the whole-arc
summary server-side (sidecar `/character/arc/synthesize`) instead of holding every
story in memory. `deleteCharacterAnalysis` discards the record (the arc screen's
Discard action).

### Story arc mutations

`createStoryArc` needs only a campaign and a title; everything else arrives as
a JSON payload keyed by the console's camelCase names, applied as a **partial
patch**. `updateStoryArc` takes the same keys (plus `title` and `campaign`).
That is what lets the wizard create the arc at step 1 and fill it in as the
user advances, rather than holding a half-built arc in browser state.

Recognised payload keys: `body` (the full premise), `overallPlot`,
`levelRange`, `targetStories`, `faction`, `party`, `npcs`.

`saveStoryArcRelations` takes `{"party": [...], "npc": [...]}` where each entry
is `{source, target, type, tier, note}`. **Only the sides present are
replaced**, so the party run and the NPC run each save without clearing the
other's work. Within a side the replacement is wholesale, because the console
sends the set that survived accept/reject rather than a diff.

**Reference resolution.** Characters and terms may be given as a UUID *or* an
exact name, so the markdown importer and the AI suggestions can pass the names
they read. Names are ambiguous here — a canonical character and its campaign
clone share a title — so a name match prefers the clone belonging to the arc's
campaign, falling back to the canonical node. That resolves PCs to their
campaign clones and NPCs to canon, which is what each actually has. A reference
that resolves to nothing is **skipped, not fatal**: a relation pair missing
either end is dropped, and a partially matched import still saves what matched.

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
paragraphs). `seed_class_grants.php` skips any class that already has grants, so
it is safe to rerun after adding a class. `seed_subclasses.php` **clears and
rebuilds** the whole vocabulary; to add a new class's subclasses without
disturbing existing terms or the character references pointing at them, use the
additive `seed_new_subclasses.php` instead. The sidecar's class-plan resolver
reads them (see [../src/sidecar/README.md](../src/sidecar/README.md)).

A class also needs a JSON template under `templates/characters/`: the class-plan
fallback and `/character/build-from-template` both key off it, and
`list_available_templates()` drives which classes can be built at all.

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
| `createStoryArc` | the console's new-series wizard (step 1) |
| `updateStoryArc` | the wizard's later steps + the arc overview screen |
| `saveStoryArcRelations` | the party / NPC relation suggestion runs + the relations tabs |
| `setSessionSummary` | `frontend/src/api/create-story.ts` + `scripts/backfill-summaries.mjs` |
| `saveCharacterArc` | `frontend/src/api/save-arc.ts` |
| `createCharacter` | `frontend/src/api/create-character.ts` |
| `updateCharacter` | `frontend/src/api/update-voice.ts` (voice id / pitch / speed); `save-image-prompt.ts` (`imagePrompt` -> `field_image_prompt`) |
| `updateCharacterProfile` | `frontend/src/api/update-character-profile.ts` (the console's character editor) |
| `setCharacterPortrait` | `frontend/src/api/generate-portrait.ts` (ComfyUI portrait) |
| `setCharacterImage` | `frontend/src/api/set-portrait-media.ts` (pick an existing media) |
| `enqueueAiJob` | `frontend/src/api/enqueue-job.ts` (queue a heavy AI job) |
| `resolveAiJob` | `frontend/src/api/resolve-job.ts` (accept or discard a finished job's result) |

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

`updateCharacterProfile(id, payload)` is the console character editor's write
path. `payload` is a JSON object keyed by camelCase field names; **only the keys
it contains are written**, so the editor sends just what the operator changed.
Keys outside the producer's `FIELD_MAP` whitelist are ignored — that map, in
`UpdateCharacterProfile.php`, is the security boundary.

Not writable through it, by design:

| Excluded | Owned instead by |
| -------- | ---------------- |
| `field_image` | `setCharacterPortrait` / `setCharacterImage` |
| `field_image_prompt`, `field_voice_*` | `updateCharacter` |
| `field_arc_*` | `saveCharacterArc` |

Three behaviours worth knowing:

- **Multi-value text fields are always written one value per delta with the
  `plain_text` format.** Some records held `<p>Steadfast</p>`, and a few held
  several traits inside a single delta. Gatsby normalises that on read
  (`frontend/src/utils/richTextToLines.ts`) and this mutation writes the clean
  values back, so a character is repaired the first time it is saved.
- **Term references are resolved by term UUID and checked against the field's
  vocabulary.** A UUID from the wrong vocabulary is rejected with
  `No <vocabulary> term found for id <uuid>` rather than written.
- **`abilityScores` is handled outside `FIELD_MAP`**, because ability scores are
  a paragraph hierarchy rather than a field value: an `ability_scores` wrapper
  holding one `ability_score` paragraph (`field_ability` term + `field_score`)
  per ability. The payload is a partial map keyed `strength` … `charisma`, so
  only the abilities it names are rewritten; the wrapper and any missing
  sub-paragraph are created on demand. A non-numeric or absent value leaves that
  ability alone — the mutation has no way to clear a score.

`field_campaign`, `field_character_type` and `field_source_character` **are**
writable. Flipping `field_character_type` is how a record is reclassified: it
moves between the console's Characters and NPCs rosters on the next Gatsby
build.

Only the fields the mutation actually set are validated
(`$node->validate()->getByFields($changed)`), so unrelated pre-existing damage —
a dangling `field_equipment_items` reference, say — cannot block every edit.

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

`setCharacterPortrait(id, imageBase64, alt)` attaches a generated portrait to a
character. It is the only write path that creates **file and media** entities:
it decodes the base64 PNG from the sidecar's `/character/portrait` (ComfyUI)
endpoint, writes it via `file.repository->writeData()` into
`public://portraits/portrait-<uuid>-<timestamp>.png`, wraps that file in an
`image` media entity, and points the character's `field_image` at it. Because
the filename is timestamped, regenerating never overwrites a file an older
revision still references.

`alt` is required and rejected when blank — `field_media_image` sets
`alt_field_required: true`, so a media entity saved without it would fail
validation. Beyond `edit any character content`, this mutation needs the
`gatsby_user` role's `create media`, `create image media`, and `view media`
permissions (added for this feature).

`setCharacterImage(id, mediaId)` points `field_image` at an **existing** image
media (no file/media creation) — used by the console's media picker to select a
previously generated or library image as the active portrait. Listing that
library is a config-only capability: the `media/image` type has
`edges_enabled: true` + `simple_queries: '1'` in
`graphql_compose.settings.graphql_compose_server.yml`, which exposes the
`mediaImages(first: N) { nodes { id name mediaType mediaImage { url alt } } }`
query (read via `frontend/src/api/list-portrait-media.ts`, requires `view
media`).

Image media carry a `field_media_type` list field (`character_portrait`,
`npc_portrait`, `item`, `monster_portrait`, `story_scenario`), exposed as
`mediaType`. The picker filters by it (`?type=` on the list function) so a
character only offers character portraits, keeping the list and its thumbnail
downloads small. `SetCharacterPortrait` stamps the type on generation (PC ->
`character_portrait`, NPC -> `npc_portrait`), and existing media were backfilled
by inferring the type from the node that references each via `field_image`.

### Queued AI jobs (`dnd_jobs` module)

Drupal also **orchestrates** the long-running AI work. `drupal/advancedqueue`
(contrib) provides a DB-backed job store; the custom `dnd_jobs` module adds the
job types, the queue config, and the GraphQL surface the console polls.

| Piece | Where |
| ----- | ----- |
| Queue | `advancedqueue.advancedqueue_queue.dnd_ai` - `processor: daemon`, `lease_time: 900`, `stop_when_empty: false` |
| Job types | `dnd_portrait`, `dnd_arc_analysis`, `dnd_arc_relations`, `dnd_story_generation`, `dnd_session_summary` (`src/Plugin/AdvancedQueue/JobType/`) |
| Mutations | `enqueueAiJob(type, payload, label)`, `resolveAiJob(id, decision)`, `requeueAiJob(id)`, `clearAiJobs(states)` |
| Queries | `aiJob(id)`, `aiJobs(states, limit)` - resolved with `mergeCacheMaxAge(0)`, since job state changes outside any cache tag |
| Services | `dnd_jobs.job_queue` (enqueue/read/update/requeue/clear), `dnd_jobs.job_review` (accept/discard), `dnd_jobs.sidecar_client`, `dnd_jobs.console_client` |
| Cron | `dnd_jobs_cron()` - recovers jobs orphaned by a dead worker |
| Drush | `drush dnd-jobs:recover` (alias `dndjr`) - the same sweep on demand |

**Never give a mutation argument a GraphQL `Boolean!`.** `resolveAiJob` first
took `accepted: Boolean!`, and the data producer was resolved **twice per
request** - once with `false`, then with the real argument. The `false` pass
discarded renders the operator had just accepted. A `String` argument
(`decision: "accept" | "discard"`) resolves exactly once; both were measured.
Every other mutation here already passes strings, which is why none of them hit
this. Producers that write should be idempotent as well, as `JobReview` now is:
repeating a decision succeeds unchanged, only a contradicting one errors.

**One queue, one processor, one job at a time.** That serialization is the crash
protection: this box is CPU-only with 32 GB, and two large models resident at
once OOMs it. The processor is a host daemon (`start.sh`), not cron:
`ddev drush advancedqueue:queue:process dnd_ai --timeout=0`.

Payloads are JSON strings (same convention as `createCharacter`), and a finished
job writes a small `result` object back onto its payload - the processor
persists the mutated payload, so the console reads it on the next poll (e.g. the
portrait job's new `imageUrl`).

**A job never applies generated content by itself.** A job can finish while
nobody is looking at the screen that started it, so writing straight onto the
node would let a background render replace a portrait somebody chose. Job types
that generate content therefore store the output and mark the result
`review: pending`; `resolveAiJob` is the only thing that applies it:

- `accepted: true` - `JobReview` points `field_image` at the stored media (via
  `PortraitWriter::assign()`) and marks the result `accepted`.
- `accepted: false` - nothing on the node changes and the result is marked
  `discarded`. The media stays in the library, so a discarded render is still
  selectable from the portrait picker later.

Either way the decision lives on the job (`JobQueue::updateResult()` rewrites the
payload), which is what lets the console's activity drawer show what still needs
a decision and stop asking once one is made. `JobReview` checks `update` access
on the target node before writing, like the request-time mutations do.

#### Stall recovery

The processor claims a job, then calls out to the host. If that call never
returns - the sidecar restarted, the host ran out of memory - the row keeps a
`processing` state and a lease nobody is honouring, and this single-threaded queue
stops moving. Recovery has three parts:

- `dnd_jobs_cron()` calls `JobQueue::requeueStalled()`, which requeues jobs whose
  lease has expired. **Do not rely on this alone:** this site is headless, has no
  `automated_cron`, and nothing schedules `drush cron` - as of this writing cron
  had not run in 71 days. `start.sh` therefore calls `drush dnd-jobs:recover`
  from the queue processor's restart loop, which fires at exactly the moment a
  worker has died. The cron hook stays as a second net for whenever cron does run. Capped at `JobQueue::MAX_STALL_RETRIES` (2); past that the
  job is **failed** with `Timed out after N attempts...`, because a job that
  always stalls would otherwise sit at the head of the queue forever.
- `requeueAiJob(id)` is the operator's manual trigger, exposed as **Requeue** on a
  stalled activity row. A deliberate retry does not count against the cap.
- `AiJob.stalled` is computed from the lease, so the console can show a claimed
  job as dead rather than spinning. A `processing` row with `expires = 0` also
  counts: the backend sets state and lease in one claim and only claims rows with
  `expires = 0`, so that combination cannot arise from normal processing - and
  nothing would ever pick it up, since the claim loop only looks at queued jobs
  and contrib's `cleanupQueue()` only resets leases that exist.

**Two timing invariants.** `lease_time` (900s) must exceed the slowest legitimate
run, or a job still working gets requeued and duplicated. `SIDECAR_JOB_TIMEOUT`
(720s) must be *under* the lease, or a hung call outlives it. A CPU portrait
render is ~4 minutes, so both hold with room to spare. Note that contrib's own
`cleanupQueue()` also resets expired leases, without any retry accounting - if it
wins the race, that reset does not count against the cap.

The web container needs `SIDECAR_URL`, `GATSBY_SERVER_URL`, and
`SIDECAR_JOB_TIMEOUT` (see `.ddev/config.local.yaml`, which is gitignored and so
must be set per machine); `SIDECAR_SECRET` is sent as `X-Sidecar-Secret` when set.

#### Clearing the log

Nothing prunes the `advancedqueue` table (`threshold: {type: 0, limit: 0}`), and
the console's activity drawer is a live view of it with no copy of its own - so
the drawer's **Clear completed** has to delete rows. `clearAiJobs(states)`
accepts terminal states only, and keeps back any finished job whose result is
still awaiting a decision: deleting one would strand the render it produced in
the media library with nothing left to attach it. It returns
`{ cleared, kept }`.

`PortraitWriter` (`dnd_content`) owns the file + media + `field_image` write so
the synchronous `setCharacterPortrait` mutation and the queued portrait job
produce identical results. Its two halves are separately callable: `store()`
writes the file and media, `assign()` points `field_image` at a media, and
`attach()` does both. The synchronous mutation calls `attach()` because the user
asked for it in that request; the queued job calls `store()` and leaves
`assign()` to the review step.

### Writes — the engine's wiki cache

The Python engine writes to Drupal through `src/integration/drupal_sync.py`,
which backs the RAG system's wiki page cache:

- `get_wiki_page_cache(url_hash)` -> `wikiCacheEntry` query
- `set_wiki_page_cache(url_hash, url, fetched_at, content_json)` ->
  `setWikiCacheEntry` mutation
- `delete_wiki_page_cache(url_hash)` -> `deleteWikiCacheEntry` mutation
- `count_wiki_page_cache()` -> `wikiCacheCount` query

Entries are keyed by the MD5 hash of the page URL, stored as the node title.
The `wiki_cache` bundle is served by hand-written resolvers in `dnd_content`
rather than exposed through graphql_compose, so Gatsby never sources these
nodes. Writes need the `create` / `edit any` / `delete any wiki_cache content`
permissions, held by the `gatsby_user` role.

Reads degrade to a cache miss when Drupal is unreachable; writes raise, because
a write that silently does nothing is a data-loss bug.

**JSON:API is not used anywhere.** `jsonapi_extras.settings` sets
`default_disabled: true` with no resource configs re-enabling it, so every
JSON:API route returns 404.

---

## See also

- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — how Drupal fits the three tiers.
- [drupal-cms/AGENTS.md](../drupal-cms/AGENTS.md) — DDEV/PHP rules and the
  source-of-truth policy.
- `drupal-cms/config/sync/REUSABLE_FIELDS_ARCHITECTURE.md` and
  `NEW_FIELDS_SUMMARY.md` — field design notes.
