# DDCCS Frontend — Design Feedback & Open Work

This file is maintained alongside CLAUDE.md and HANDOFF.md. Use it as a prompt
for Claude Design when iterating on visual polish or spec gaps.

---

## 1. Character Sheet — partially built

**Route:** `/character/pc/:slug/` and `/character/npc/:slug/` (same template)

Both PCs and NPCs use `src/templates/character.tsx` — `npc.tsx` was removed.
`characterType === false` identifies an NPC; the template adjusts the hero
section accordingly (shows role instead of class badges).

**What currently renders:**

- Hero: portrait (Portrait atom), name, nickname, pronouns, role (NPCs),
  class/level badges, vitals strip (HP · AC · Speed · Prof · Gold)
- Left column: ability scores 3×2, personality traits, ideals/bonds/flaws,
  backstory parchment scroll (with drop cap + grain texture)
- Right column: special abilities, weapons, magic items, gear

**Sections not yet wired to the template** (data exists in Drupal for
complete characters like Triara):

| Section | What to add to `character.tsx` |
| ------- | ------------------------------ |
| Skills panel | Enable `skills` taxonomy in graphql_compose, add `skills { ... on Drupal_TermSkills { name } }` to query |
| Features & Traits | Enable `ability_reference` paragraph bundle, query `abilitiesRef` |
| Magic panel | Already enabled (`spell_reference`, `spell_slot`) — add to query + render |
| Languages & Proficiencies | Enable `languages` + `tools` taxonomies in graphql_compose, add to query |
| Relationships grid | Enable `relationship` paragraph fields, add `relationships` to query |
| Save throws on ability tiles | Derive from ability modifier + proficiency bonus (no extra field needed) |
| Passive Perception | Derive: `10 + WIS modifier + (perception proficient ? profBonus : 0)` |
| Layout toggle: spread / scroll / tabbed | UI only — no new data required |

---

## 2. Characters & NPCs pages — card spec partially done

**Routes:** `/characters/` and `/npcs/`

**What currently works:** Portrait atom, name, nickname, pronouns, Canon badge,
stat chips (Lv/HP/AC), party dot, text search, party-only toggle, Canon filter.
Both pages share the `CharacterRoster` organism.

**Still missing from canonical spec:**

- Class filter chip row (single-select, "All classes" reset)
- Level range slider (dual-thumb, 1–20)
- Spellcaster-only checkbox
- Sort select
- Table view (portrait + name + class + lv + species + campaign + HP + AC)
- Species chip on card (blocked: `Drupal_TermSpecies` not in `TermUnion`)
- Fallen character treatment (0.78 opacity + "Fallen" badge + dash for HP)
- Campaign sigil icon on card
- HP shown as `current / max` (currently only shows max HP)

**Drupal/GraphQL blocker:** enable `species` vocabulary in graphql_compose
(`entity_config.taxonomy_term.species: enabled: true`), then add to the
`CharactersList` and `NPCList` queries.

---

## 3. Portrait atom — species watermark not active

`src/components/atoms/Portrait.tsx` is built and in use on character cards and
sheets. The `SPECIES_ICON` map is fully defined (Human, Elf, Dwarf, etc.) but
`species` is not queryable yet — always falls back to `crossed-swords`.

Fix: same blocker as §2 — enable `Drupal_TermSpecies` in graphql_compose.

---

## 4. Current Party — partial implementation

**Canonical:** `Current Party.html`. Route: `/party/`

**What currently renders:** `CurrentPartyScreen` — campaign name/status header,
member count + session count blurb, "Story log" and "New session" action
buttons, character card grid (portrait, name, nickname, HP/AC stats, "Full
sheet" link). Falls back to campaign-name filter if `field_current_party` is
not set.

**What the canonical design still requires:**

1. **Campaign banner** — sigil watermark background, Cinzel 32px, session
   number, last played, "Active" badge, campaign switcher.
2. **Objective / Hooks / Gold strip** — 3 columns: italic objective paragraph ·
   quest hooks list · Fira Code 30px gold number.
3. **Combat readout** — HP block with gradient (green→amber→red), 4-stat row
   (AC/Speed/Init/Prof), spell-slot mini rows.
4. **RP cards** — 36px portrait + alignment + lead trait + primary bond + party
   relationship callouts. Behind `showFlavor` toggle.
5. **Shared inventory** — auto-fill grid, item cards with rarity badge.

**Drupal fields needed:** `field_campaign_objective`, `field_quest_hooks`,
`field_gold_pool`, `field_shared_inventory` on the campaign taxonomy term.

---

## 5. Session Reader — not yet built

**Canonical:** `Session Reader.html`. Route: `/stories/:slug/`

The existing story template (`src/templates/story.tsx`) has the parchment
scroll + unfurl animation and prev/next session navigation. What it lacks:

- Party rail (right sidebar): portraits + names linking to character sheets
- End-of-chronicle action panel: "+ Begin next session" CTA + Authoring /
  Generation / Analysis action groups with AI/slow tags
- Pagination dots (one pip per session in campaign)
- FX dock: Sound on/off · Motion on/off pill buttons
- Web Audio unfurl sound (synthesised, no asset)
- Tweaks panel: sound, motion, unfurl duration slider (400–3500ms)

---

## 6. Utility commands — not wired

`MENU_DATA.utilityCommands` (`--reindex`, `--milvus-status`, `--sync-drupal`)
render in the sidebar footer but have no dispatch endpoint. Buttons need an
`onClick` handler that calls the Python AI worker.

---

## 7. Activity drawer — SSE not connected

Drawer renders with an empty state ("No activity yet"). `activityItems` is
held in `useState([])` — needs SSE/websocket from the Python AI worker to push
job status into `StatelyLedger.activityItems`. The `ActivityItem[]` shape is
already correct; only the transport is missing.

---

## 8. Console screens — remaining PlaceholderScreen routes

Two routes still fall through to `PlaceholderScreen`:

| Route | Screen needed |
| ----- | ------------- |
| `read/r-dev` | Character development reader |
| `npcs/n-validate` | NPC validator output |

All other previously-stubbed routes now have real screens: `TimelineScreen`,
`SpellRegistryScreen`, `StorySeriesWorkspaceScreen`, `NewSeriesScreen`,
`SettingsScreen`, `ModelProfileScreen`, `ToolsScreen`, `CurrentPartyScreen`,
`DeprecatedScreen` (for `characters/ascii`), and `CreateCharacterScreen` (for
`characters/template`).

### `characters/template` — Create Character from Template (Done)

A derive-not-ask wizard (`CreateCharacterScreen`), 5 steps (Identity, Class &
Level, Ability Scores, Skills, Roleplay). The user supplies only what cannot be
computed; the Python sidecar derives HP/proficiency/saves/spell slots and
resolves class/species/subspecies abilities (rules text, source type, level)
from the rules wiki (`RAG_RULES_BASE_URL`) at create time. Class, skills, species, subspecies, and
background are populated from the Drupal taxonomy (`termClasses`, `termSkills`,
`termSpeciesItems`, `termLineages`, `termBackgrounds`) via `useStaticQuery`,
each with an "Other (not on the list)" option that creates the term on submit.
Resolved abilities are upserted as `abilities` terms and linked to the
character. Choosing "Other" for background opens `CreateBackgroundModal` to
define a homebrew background (3 ability options, skills, tools, an Origin-tagged
feat, gold, equipment); on create it is saved as a Homebrew-edition background
term with item nodes find-or-created for the equipment (typed weapon/armor/item
and given a rules-wiki description where one exists). Selecting an **official**
background instead resolves it from the rules wiki (`RAG_RULES_BASE_URL`) on Identity-step confirm
(`/api/resolve-background`, spinner) and, if its term is empty, populates it
(2024 edition) on create; its granted skills/feat/equipment are applied to the
character. The **Skills** step is rules-aware: on entry it loads a class plan
(`/api/skill-plan`) sourced from the `class` taxonomy (`class_grant` paragraphs,
template/RAG fallback) — class-restricted skill choices plus species/subspecies
trait choices, class tool proficiencies (e.g. Bard's three Musical Instruments),
**equipment A/B choices** (class and background: take the items or the gold), and
a **subclass** dropdown (shown once the character reaches the subclass level,
options from the `subclasses` vocab filtered by parent class) — and layers on
background grants (granted skills/tools pre-checked but editable; a Skilled origin
feat adds a "choose 3 skills or tools" group). Tool selections persist to
`field_tools`; the resolved equipment list and gold total flow to the character. Feat terms (e.g. the background's origin
feat) are backfilled with their rules text from the wiki when empty. Creating
persists a **source** character via the `createCharacter` GraphQL mutation —
with sensible AI/voice defaults applied server-side — and clones it into the
active campaign via `addCharacterToCampaign`. All writes go through
`src/api/create-character.ts`.

---

## Acceptance checklist — current status

| Item | Status |
| ---- | ------ |
| Homepage renders StatelyLedger | Done |
| Sidebar: sections with icon + label + blurb + count | Done — counts derived from Drupal data |
| Topbar: brand + nav links + campaign chip + search | Done |
| Topbar sticky on all pages including character sheets | Done |
| Campaign switcher updates all console screens reactively | Done |
| All campaigns visible (including empty ones) | Done — via `termCampaigns` |
| Activity drawer: empty state until SSE wired | Done (§8) |
| Default landing: read / r-story | Done |
| Characters / NPCs pages: Portrait, filters, party dot | Partially done (§2) |
| Character Sheet: hero + ability scores + equipment | Done |
| Character Sheet: personality + backstory parchment scroll | Done |
| Character Sheet: skills / features / spells / languages | Missing (§1) |
| Character Sheet: layout toggle spread/scroll/tabbed | Missing (§1) |
| NPC character sheet — same template as PC | Done — merged into character.tsx |
| Portrait atom: colour block + initials + species watermark | Done — watermark disabled until species queryable (§3) |
| GameIcon: inline SVG, no black squares | Done |
| `/characters/` and `/npcs/` standalone pages | Done — shared `CharacterRoster` organism |
| Current Party screen | Partial — card grid done, canonical layout missing (§4) |
| Session Reader | Partially done — scroll + prev/next built, party rail + actions missing (§5) |
| Story Series Workspace action sub-screens | Done — all 13 actions wired (§6) |
| No prototype mock strings in production | Done |
| All CSS colours via tokens (no hardcoded hex/rgba) | Done — `color-mix()` throughout |
