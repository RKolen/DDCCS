# Frontend — D&D Campaign Console

The Gatsby frontend is the primary interface to the system. A user manages
characters, NPCs, stories, items, monsters, party, and search from here without
ever logging into Drupal. It reads content from Drupal over GraphQL and performs
writes and live AI through its own serverless functions.

- **Get it running:**
  [docs/FRONTEND_QUICKSTART.md](../docs/FRONTEND_QUICKSTART.md)
- **Architecture context:** [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- **Agent coding rules:** [CLAUDE.md](CLAUDE.md)
- **Design system:** [DESIGN.md](DESIGN.md)

---

## Stack

| Tool | Version | Purpose |
| ---- | ------- | ------- |
| Gatsby | 5.x | Static site generator, dev server, serverless functions |
| React | 18.x | Component rendering |
| TypeScript | 6.x | Strict type safety |
| gatsby-source-graphql | 5.x | Stitches the remote Drupal `graphql_compose` schema into Gatsby |
| gatsby-plugin-image / sharp | 3.x / 5.x | Optimised images |
| lucide-react | 1.x | Icon set |

---

## Project layout

```text
frontend/
|-- gatsby-config.ts      # Plugins; bridges root .env vars; sets the GraphQL URL
|-- gatsby-node.ts        # createPages for character/story/item/monster templates
|-- gatsby-browser.ts / gatsby-ssr.ts
`-- src/
    |-- api/              # Gatsby serverless functions (writes + live AI)
    |-- components/
    |   |-- atoms/        # Smallest UI units
    |   |-- molecules/    # Atoms combined
    |   |-- organisms/    # Self-contained sections
    |   |-- templates/    # Page layout shells (no data)
    |   |-- console/      # Admin/console screens (create, edit, validate, forge)
    |   `-- layout/       # Global chrome: topbar, campaign state, activity log
    |-- pages/            # Gatsby pages (run GraphQL page queries)
    |-- templates/        # Per-node detail templates (built by gatsby-node.ts)
    |-- types/            # Shared TS interfaces (Drupal shapes, query results)
    |-- utils/            # Helpers
    `-- styles/           # tokens.css + global / module CSS
```

### Pages (`src/pages/`)

| Page | Purpose |
| ---- | ------- |
| `index.tsx` | Campaign dashboard / landing |
| `characters.tsx` | Character roster |
| `npcs.tsx` | NPC roster (character nodes filtered by type) |
| `stories.tsx` | Story list |
| `campaign-reader.tsx` | Continuous campaign story reader |
| `items.tsx` | Item registry |
| `spells.tsx` | Spell compendium (level-grouped index over `node--spell`) |
| `monsters.tsx` | Monster list |
| `party.tsx` | Party / campaign membership management |
| `search.tsx` | Search (backed by the sidecar) |
| `404.tsx` | Not found |

### Templates (`src/templates/`)

Per-node detail pages generated in `gatsby-node.ts`: `character.tsx`,
`story.tsx`, `item.tsx`, `monster.tsx` (each with a co-located `.module.css`).

### Editing a character

`characters/edit` (and its NPC twin `npcs/n-edit`) is the one place a character
record is edited — `CharacterEditScreen.tsx`, built from the field primitives in
`components/console/FieldEditors.tsx` and writing through
`api/update-character-profile.ts`.

Three field groups are **not** editable there; the screen shows a card with a
button to the screen that owns them:

| Group | Owner screen |
| ----- | ------------ |
| Portrait | `characters/ascii` — Portrait Studio |
| Voice | `characters/consult` — voice picker with live preview |
| Arc analysis | `characters/arc` — Character Arc Analysis |

Notes on behaviour worth knowing before changing this screen:

- **The player roster is scoped to the active campaign; the NPC roster is not.**
  `rosterForScreen()` in `ConsoleContext.tsx` skips campaign scoping entirely in
  `npcMode`, because an NPC carries no `field_campaign` and never joins a
  campaign's `currentParty` — scoping NPCs by campaign empties the roster
  outright. NPCs are shared across campaigns by design, and there is
  deliberately no `npcsForCampaign()`. `CharacterListScreen` and
  `CharacterDetailScreen` make the same carve-out inline.
- **The deep-link pin escapes campaign scope but not PC/NPC scope.**
  `rosterForScreen()` resolves `pinnedId` against the roster the screen asked
  for, so a `?char=` link to a player character cannot surface in the NPC editor
  after a section switch.
- **The route sets `npcMode`, not the inherited context.** `npcMode` persists in
  `ctx` across section switches, so every `characters/*` screen pins it to
  `false` and every `npcs/*` screen to `true`. A screen that just forwards `ctx`
  renders whichever roster the operator happened to visit last. Switching
  sections in the sidebar also resets `charIdx` and drops the deep-link pin,
  because an index into one roster means nothing in the other.
- **Jumps translate the index.** The handoff buttons compute the target's index
  in *that screen's* roster, because this screen's roster is campaign-scoped and
  the Portrait Studio's is not.
- **NPCs use the same screens** with `npcMode` set. `field_recurring` gates how
  much of the form an NPC gets: off, the stat-oriented groups are hidden; on, it
  gets the full character profile.
- **The Antagonist group is the NPC-only one** — Recurring, encounter tactics,
  defeat conditions, lair actions, legendary actions and regional effects. It is
  shown whenever the form's record type reads NPC, and starts expanded when the
  record was already saved as one, since it is what the NPC editor is for.
- **Faction and Key traits sit together in Roleplay** — taxonomy fields backed
  by the `factions` and `traits` vocabularies, offered to player characters and
  NPCs alike. Both are ungated by `field_recurring`, matching the group they sit
  in.
- **Multi-value text fields are one row per Drupal delta.** Values arrive
  normalised by `utils/richTextToLines.ts`, which strips legacy HTML and splits
  a delta holding several entries into several rows.
- **Campaign, record type and source flag are editable** in the Identity group.
  The campaign select is built from the same `termCampaigns` list the campaign
  switcher uses. Switching the record type between Player character and NPC
  moves the record between the Characters and NPCs rosters on the next build;
  the form reveals or hides the NPC-only groups straight away, while the handoff
  buttons keep pointing at the roster the record was last built into.
- **Ability scores are editable in Vitals**, sent as a partial map of only the
  abilities that changed. A blank box means "leave that score as it is" — the
  write path cannot clear a score.

### The character list card

`characters/list` (and `npcs/n-list`) shows each record as a `.char-card`:
portrait, name, nickname, then class — with subclass in brackets, and each
class's own level when the character is multiclassed — followed by species and
heritage, background, and pronouns, with AC and HP in the card footer.

Classes come from the `characterClasses` paragraphs, mapped in
`utils/buildConsoleData.ts` into `DrupalCharacter.classes`, with the first one
also flattened onto `characterClass` for the many one-line summaries that show a
single class. Only `index.tsx` queries them; the narrower console routes
(`/party`, `/characters`, `/npcs`) leave the list empty.

### Deep links into the console

`/?section=<id>&item=<id>&char=<uuid>` opens the console on a given screen with
a character selected — this is how the "Edit character" button on
`/character/pc/...` and `/character/npc/...` works. `index.tsx` validates the
section and item against `MENU_DATA` and falls back to the default landing
screen if they do not match.

Valid `section` ids are `characters`, `stories`, `npcs`, `items`, `spells`,
`monsters`, `config`, `model`, and `tools`; the console lands on `stories` when
no section is named. There is no longer a `read` section — it held four menu items backed
by one unique screen, with `r-story`/`r-session` pointing at the same component
and `r-char` duplicating `characters/view`. Its two real destinations moved to
`stories/read` (story reader) and `characters/development` (development log).
This is console IA only: the public reader at `/stories/` and
`src/templates/story.tsx` is a separate surface and is unchanged.

`stories/read` now renders the story itself, in the same unfurling chronicle
scroll the story page uses — the markup moved into
`src/components/molecules/StoryScroll.tsx` and both surfaces render it, so the
console cannot drift from the public page. The scroll stays **furled by
default** on both: the unfurl is a deliberate flourish, not friction. Its
`onUnfurl` fires on the opening edge only, which is where a scroll sound goes
when there is one. The body is fetched per story through `story-body.ts`
rather than carried in the console's page data, and the old "Read full story"
link is gone — there is nothing left to go elsewhere for.

`spells` was likewise promoted out of `stories/spells` into a top-level section
with its own `/spells/` topbar link — a compendium is not a property of a story.
Its console item list is deliberately minimal (`sp-list` only) pending design;
menu items added without a `ScreenRouter` case fall through to
`PlaceholderScreen`, which says so loudly.

---

## Data layer

### Reads — GraphQL (Drupal)

`gatsby-source-graphql` stitches Drupal's `graphql_compose` schema into Gatsby
under the `drupal` field. The endpoint is `${DRUPAL_BASE_URL}/graphql`, set in
`gatsby-config.ts` — **not** the Gatsby dev server at `localhost:$GATSBY_PORT`,
whose GraphQL explorer (`/___graphql`) views the stitched schema for local
development only.

```tsx
export const query = graphql`
  query StoryPage($id: ID!) {
    drupal {
      node(id: $id) {
        ... on Drupal_NodeStory { title storyNumber body { processed } }
      }
    }
  }
`;
```

GraphQL field names are camelCase without the `field_` prefix (`storyNumber`,
not `fieldStoryNumber`). NPCs are **character** nodes filtered by
`field_character_type` — there is no `nodeNpcs` type (deprecated). See
[docs/DRUPAL.md](../docs/DRUPAL.md).

### Writes and live AI — serverless functions (`src/api/`)

Each file under `src/api/` is a Gatsby Function (an HTTP endpoint). These handle
everything that mutates state or calls the LLM, so the browser never holds
Drupal credentials.

| Function | Method | Talks to | Purpose |
| -------- | ------ | -------- | ------- |
| `campaigns.ts` | POST | Drupal (`createCampaign`) | Create a campaign |
| `create-character.ts` | POST | Sidecar + Drupal (`createCharacter`, `addCharacterToCampaign`) | Derive a sheet via the sidecar, enrich equipment with descriptions/types (`/character/equipment/describe`), persist a source character, clone into the active campaign |
| `resolve-background.ts` | POST | Sidecar | Resolve a background's granted data (skills/feat/abilities/gold/equipment) from the rules wiki (`RAG_RULES_BASE_URL`) |
| `skill-plan.ts` | POST | Sidecar | Class + species/subspecies plan for the skills step: granted + skill/tool choice groups, class equipment A/B choices (items vs gold), and the subclass choice (from the `class`/`subclasses` taxonomy, template/RAG fallback) |
| `campaign-party.ts` | POST | Drupal (`addCharacterToCampaign`) | Add a character to a campaign |
| `create-story.ts` | POST | Drupal (`createStory`, `setSessionSummary`) + LLM | Persist a finished story, then (best-effort) summarise the session and refresh the campaign overview |
| `create-story-arc.ts` | POST | Drupal (`createStoryArc`) | Create a story arc for a campaign (`{ campaignId, title, fields? }`). Only campaign + title are required |
| `update-story-arc.ts` | POST | Drupal (`updateStoryArc`) | PATCH an arc's fields (`{ id, fields }`); only the keys sent are written |
| `save-arc-relations.ts` | POST | Drupal (`saveStoryArcRelations`) | Replace an arc's party and/or NPC relations; returns the counts Drupal actually saved, since unresolvable pairs are skipped |
| `suggest-arc-relations.ts` | POST | Sidecar (`/relations/suggest`) | Suggest one subject's relationships (one model call) |
| `merge-arc-relations.ts` | POST | Sidecar (`/relations/merge`) | Collapse the per-subject batches into one deduplicated set |
| `run-arc-relations.ts` | POST | Self (loops the two above) | Whole-side run for the queued job, which has no browser to loop in |
| `campaign-recaps.ts` | POST | Drupal (read `TermCampaign`) | Read a campaign's stored session recaps and overview (`{ campaignId }` -> `{ campaignName, recaps, overview }`); no AI. The arc backfill starts here so it only pays to summarise what has never been summarised |
| `summarize-story.ts` | POST | Drupal (read one story) + LLM (fast model) + Drupal (`setSessionSummary`) | Summarise one stored story by id and persist the recap on its campaign (`{ campaignId, storyId }` -> `{ storyNumber, summary }`). Unlike `store-session-summary.ts` the body is fetched, not supplied, which is what a backfill has; persisting per story is what makes the run resumable |
| `draft-arc.ts` | POST | Sidecar (`/arc-draft/propose`) | Propose the story arc a campaign's played sessions add up to (`{ campaignName, recaps, party, npcs }` -> `{ draft }`). One model call over the **recaps**, never the story bodies |
| `run-arc-backfill.ts` | POST | Self (loops the three above) | Whole backfill for the queued job, which has no browser to loop in |
| `extract-story-npcs.ts` | POST | Sidecar (`/arc-draft/npcs`) | Read the NPC cast a campaign's sessions name (`{ campaignName, recaps, party, known }` -> `{ npcs: [{ name, role, known }] }`). A separate call from `draft-arc`: the NPC roster is not the cast |
| `create-npc.ts` | POST | Drupal (`createNpcStub`) | Create a minimal NPC for a campaign (name + one-line role + provenance). Returns the existing NPC when the campaign already has that name, so a rerun cannot duplicate |
| `story-body.ts` | POST | Drupal (read one story) | One story's processed HTML (`{ storyId }` -> `{ title, storyNumber, body }`); no AI. Backs the console reader, which fetches per story rather than carrying every body in page data |
| `summarize-session.ts` | POST | Ollama-compatible LLM (fast model) | Summarise one story body into a concise recap (`{ storyBody }` -> `{ summary }`) |
| `campaign-overview.ts` | POST | Ollama-compatible LLM (fast model) | Synthesize per-session recaps into one "story so far" (`{ summaries }` -> `{ overview }`) |
| `update-character.ts` | POST | Drupal (`updateCharacter`) | PATCH voice settings and the image prompt |
| `update-character-profile.ts` | POST | Drupal (`updateCharacterProfile`) | PATCH the character editor's profile fields |
| `arc-story-chunks.ts` | POST | Drupal (read one story) | Split one story's body into small analysis chunks (`{ storyId }` -> `{ title, storyNumber, chunks }`); no AI. The console analyses each chunk separately so no request runs long |
| `arc-analyze-story.ts` | POST | Sidecar (`/character/arc/story`) | Analyse one story chunk into one arc data point (one model call). The console loops this per chunk with a progress counter |
| `arc-aggregate.ts` | POST | Sidecar (`/character/arc/aggregate`) | Aggregate the collected per-story data points into the full arc (fallback path when there is no `character_analysis` node to persist to) |
| `upsert-analysis.ts` | POST | Drupal (`upsertCharacterAnalysis`) | Persist one story's analysis prose and/or the synthesized summary onto the `character_analysis` node (crash-safe, per story as each completes) |
| `get-analysis.ts` | POST | Drupal (read `character_analysis`) | Read one character's stored record (`{ storyNumbers, storyAnalyses, summary }`): `storyNumbers` is the resume signal (skip already-analysed stories); the rest backs the arc screen's stored-analysis display |
| `list-analyses.ts` | POST | Drupal (read `character_analysis`) | List every stored record (`{ analyses: [{ characterId, storyCount, hasSummary }] }`) in one call so the arc hub can show a "Synthesize summary" affordance per character card |
| `synthesize-analysis.ts` | POST | Drupal (read node) + Sidecar (`/character/arc/aggregate`) + Drupal (`saveCharacterArc` + `upsertCharacterAnalysis`) | Read the node's stored per-story **data points**, aggregate them into a full arc (real metric trend lines, direction, relationships, goals, summary), save it onto the character so the sparkline display renders, and return it — the resume-safe finish for a run |
| `delete-analysis.ts` | POST | Drupal (`deleteCharacterAnalysis`) | Discard a character's `character_analysis` node (the arc screen's Discard action) |
| `save-arc.ts` | POST | Drupal (`saveCharacterArc`) | Persist an accepted arc (direction/stage/summary + metric/relationship/goal paragraphs) |
| `generate-story.ts` | POST | Ollama-compatible LLM | Stream an AI-generated story (SSE) |
| `consult.ts` | POST | Ollama-compatible LLM | Stream an in-character chat reply for the character consultation (SSE) |
| `tts.ts` | POST | Sidecar (`/tts/speak`) | Synthesise a reply or story segment to speech (Piper, using the character's voice + speed/pitch), returns `audio/wav` |
| `tts-segment.ts` | POST | Sidecar (`/tts/segment`) | Split story text into multi-voice segments (`{ text, speaker, voiceId, speed, pitch }[]`) for sequential playback; used by the story page Narrate medallion |
| `list-character-voices.ts` | GET | Drupal (`nodeCharacters`) | Page through every character's voice id / pitch / speed (cursor loop past the graphql_compose 100-cap); used when the story Narrate button starts |
| `update-voice.ts` | POST | Drupal (`updateCharacter`) | Save a character's voice id / pitch / speed (consultation voice mini-wizard) |
| `spotlight.ts` | POST | Sidecar (`localhost:$SIDECAR_PORT`) | Spotlight scores for a party |
| `generate-portrait.ts` | POST | Sidecar (`/character/portrait`) + Drupal (`setCharacterPortrait`) | Generate a character portrait with local ComfyUI (long, timeout-free call), then persist it onto the character's `field_image`; returns the new `imageUrl`. Accepts an explicit `positive` / `negative` prompt (blank falls back to the profile-built prompt and the standard negative), and an optional `referenceImageUrl` / `identityWeight` that keeps the character's likeness across a regeneration (IPAdapter); the response's `usedReference` says whether that was actually applied. Requires `COMFYUI_ENABLED=true` on the sidecar (503 otherwise) |
| `list-portrait-media.ts` | GET | Drupal (`mediaImages`) | List image media from the library (`{ media: [{ id, name, url, alt }] }`) for the portrait picker; `?type=character_portrait` filters by `mediaType` so the browser only receives the relevant subset (pages through the 100-cap connection) |
| `set-portrait-media.ts` | POST | Drupal (`setCharacterImage`) | Point a character's `field_image` at an existing media (no new file); returns the new `imageUrl` |
| `portrait-prompt.ts` | POST | Sidecar (`/character/portrait/prompt`) | Build a portrait prompt from the profile, or (with `enhance`) enrich the edited text via the fast model; returns `{ positive, negative }` |
| `describe-image.ts` | POST | Sidecar (`/character/describe-image`) | Image→prompt: run the local Ollama vision model (`IMAGE_TO_PROMPT_MODEL`) over an image URL, returns `{ positive }`. Slow on CPU |
| `save-image-prompt.ts` | POST | Drupal (`updateCharacter`) | Persist a character's reusable image prompt (`field_image_prompt`) |
| `enqueue-job.ts` | POST | Drupal (`enqueueAiJob`) | Queue a heavy AI job (`{ type, payload, label }`) and return its id immediately; nothing runs during the call |
| `job-status.ts` | GET | Drupal (`aiJob` / `aiJobs`) | Poll one job (`?id=`) or list recent ones (`?states=queued,processing&limit=`) for the activity drawer |
| `resolve-job.ts` | POST | Drupal (`resolveAiJob`) | Accept (`{ id, accepted: true }`) or discard a finished job's result. Accepting a portrait job is what points `field_image` at the render; discarding leaves the character alone and keeps the media in the library |
| `requeue-job.ts` | POST | Drupal (`requeueAiJob`) | Put a stalled job back on the queue (`{ id }`); for a job whose worker died mid-run. Drupal cron does this automatically once a lease expires |
| `clear-jobs.ts` | POST | Drupal (`clearAiJobs`) | Delete finished jobs, clearing the activity drawer (`{ states? }` -> `{ cleared, kept }`). Terminal states only; a result still awaiting a decision is kept back |
| `run-arc-analysis.ts` | POST | own API routes + Drupal | Run a character's whole arc analysis server-side (chunk -> analyse -> persist -> synthesize); called by the queued `dnd_arc_analysis` job, which has no browser to loop in |
| `generate-story-text.ts` | POST | Ollama-compatible LLM | Non-streaming twin of `generate-story.ts` (same prompt via `utils/storyPrompt.ts`), for the queued story job |
| `store-session-summary.ts` | POST | Ollama-compatible LLM + Drupal (`setSessionSummary`) | Summarise a session and save it in one call, for the queued summary job |

`generate-story.ts` streams Server-Sent Events from
`AI_CREATIVE_BASE_URL/chat/completions`. `spotlight.ts` calls the Python sidecar
(see [src/sidecar/README.md](../src/sidecar/README.md)).

The creation wizard's class, species, and background dropdowns are a build-time
`useStaticQuery` over `termClasses` / `termSpeciesItems` / `termBackgrounds`, so
they show exactly what those Drupal vocabularies contain. Adding options from a
new sourcebook is a Drupal-side seed followed by `npm run clean` here — see
[docs/DRUPAL.md](../docs/DRUPAL.md). A background typed in by hand rather than
picked from the list is treated as homebrew and opens the definition modal.

### Story arcs

A **story arc** (`story_arc` node) is the multi-story plan a run of stories is
written against — premise, act spine, antagonist faction, party, and the
relationship web. `stories/new-series` builds one through a five-step wizard
(`NewSeriesScreen`). The arc is created in Drupal at the end of step 1 and
patched as the user advances, so a refresh costs one step rather than the whole
arc.

Supporting modules:

| Module | Role |
| ------ | ---- |
| `src/utils/arcPayload.ts` | The payload contract shared by the console and the API functions; mirrors what Drupal's `StoryArcWriter` accepts |
| `src/utils/arcMarkdown.ts` | Parses an existing arc document into fields + relations (see below) |
| `src/utils/arcRoster.ts` | Builds the PC and NPC pickers, which cannot share a filter |
| `src/utils/arcRelationsEdit.ts` | `useArcRelations()` — editing state and the single save path for both relation editors |
| `src/utils/drupalMutation.ts` | Shared credentials + mutation transport for the arc endpoints |
| `src/components/console/ArcRelationsTable.tsx` | The editable relation rows, shared by both editors |
| `src/utils/arcBackfill.ts` | Drives the backfill run for a campaign with no arc, and maps an accepted draft onto the arc payload |
| `src/components/console/ArcBackfillPanel.tsx` | The empty state's run/queue controls and progress |
| `src/components/console/ArcDraftReview.tsx` | The editable accept/discard form a drafted arc lands in |
| `src/components/molecules/StoryScroll.tsx` | The unfurling chronicle scroll, shared by the story page and the console reader |

**Where relations are edited.** Two surfaces, one save path:

- `stories/arcs` (`StoryArcScreen`) is the authoring surface — one campaign's
  arcs, what each is made of, the stories attached to it, and the full
  relationship web with inline add/edit/delete.
- The **Relations** tab on a character sheet (`CharacterRelationsTab`) is the
  same data from one character's side. It reads across *every* arc, so a
  recurring NPC shows their whole web rather than one arc's slice, and filters
  to the rows that character is an end of.

Editing is scoped to one arc because that is the unit `saveStoryArcRelations`
replaces. `useArcRelations()` therefore holds **both sides of the arc in full**
even when the character tab is showing a filtered subset — saving from a
character sheet must not drop the bonds that sheet never displayed. After a
save the hook keeps its own state as the truth: the page's Drupal data comes
from a build-time query and would visibly revert the write until the next
source.

**The two rosters differ.** A player character exists twice — a canonical
template with no campaign, and a clone belonging to the campaign — and the arc
must point at the clone, so `partyRoster()` keeps only clones. NPCs have no
clones yet, so the same filter would return nothing; `npcRoster()` prefers a
campaign clone when one exists and falls back to canon, which keeps working once
NPCs are cloned too.

**Markdown import.** Step 1 accepts a pasted arc document and maps it onto
fields rather than dumping it into one box. It reads the shapes the DM's notes
already use: `ACT I, ... (Levels 6-8)` as a plain line (everything before the
first ACT line is the premise, everything after is the spine), `### TIER n`
setting the tier for the `####` pairs beneath it, `#### A <-> The Epithet (Real
Name) & The Other (Other Name)` as one source against two targets, the
party-internal `### A & B - description` heading, and pair tables written as
`| A & B | description |`. Names are resolved against the campaign roster;
anything unresolved is **listed in the preview, not guessed at**, and the
operator applies the import only after seeing what matched.

### Suggesting relations

One model call per party member, not one for the whole web: a large cast is
hundreds of possible connections, too many for a single local inference pass.
The console loops `suggest-arc-relations` per subject (showing progress), then
posts the batches to `merge-arc-relations`, which collapses the reciprocal
pairs — A->B and B->A are one bond.

Two ways to run it, both ending in the same accept/reject review:

- **Interactive** (`arcSuggest.ts`, driven by `ArcSuggestButtons`) loops in the
  browser so progress is visible. A failing subject is skipped rather than
  aborting the run.
- **Queued** (`dnd_arc_relations` -> `run-arc-relations.ts`) loops on the host,
  so the tab can be closed. Its suggestions are stored as the **job's result**
  and are not written to the arc: saving replaces a whole relation side, so an
  unattended job must never overwrite bonds written by hand. Opening the job
  from the activity bar loads them into `StoryArcScreen` for review.

The suggestion model must be an **instruct** model, not a "thinking" one — see
`RELATIONS_PROFILE` in `.env.example`.

### Drafting an arc for a campaign that predates arcs

A campaign played before story arcs existed has stories but no arc, so
`StoryArcScreen` had nothing to show and relationship suggestion had nothing to
hang on — its roster and context both come from an arc. The empty state is now
the way in rather than a dead end.

`ArcBackfillPanel` runs `arcBackfill.ts`, which:

1. reads the campaign's stored recaps (`campaign-recaps`),
2. summarises every session that has none, one call each
   (`summarize-story`, which persists as it goes so a rerun resumes),
3. asks for the arc they add up to (`draft-arc` -> sidecar), and
4. asks, separately, which NPCs those sessions name
   (`extract-story-npcs` -> sidecar).

**The cast is a second question, not a second job for the same prompt.** The
NPC roster is not the cast: a campaign ported from elsewhere has stories full
of people who have no character node at all, so offering the arc only the NPCs
already on record offers it people who never appear in the story. Names that
match something on record come back `known` and are ticked into the arc; the
rest are offered for creation as stubs — a name and one line, nothing invented
— through `create-npc`. Drupal returns the existing NPC for a name the campaign
already has, so a rerun cannot duplicate them.

**Level range and target-story count are deliberately not drafted.** Both stay
fluid for the life of an arc — a campaign can plan twenty-seven stories and
write fourteen — so a model reading the past has nothing to say about them.
They are set in the arc editor, where planning decisions belong.

The draft is read from the **recaps, not the story bodies**: a campaign's
bodies run to hundreds of thousands of characters and will not fit a local
context, while its recaps fit in one call.

Two ways to run it, both ending in the same review:

- **Interactive** (`arcBackfill.ts`, driven by `ArcBackfillPanel`) loops in the
  browser so the session being read is visible. A story with no body, or one
  call the model fumbles, is skipped rather than aborting the run.
- **Queued** (`dnd_arc_backfill` -> `run-arc-backfill.ts`) loops on the host, so
  the tab can be closed. The proposal is stored as the **job's result** and
  never written: an arc is the plan a campaign's stories hang off, so an
  unattended job must not create one nobody has read. Opening the job from the
  activity bar loads it into `StoryArcScreen`'s review form.

Nothing reaches Drupal until the operator accepts. `ArcDraftReview` makes every
field editable — title, premise, act spine, antagonist faction — and the party
and cast are ticked by hand, so the arc that gets created is the one that was
read and agreed to. Discarding leaves the campaign
untouched; the recaps the run produced are kept either way, since they are
useful on their own.

Like relationship suggestion, drafting needs an **instruct** model, not a
"thinking" one — see `ARC_DRAFT_PROFILE` in `.env.example`.

### Queued AI actions

Anything that takes minutes is queued rather than held open in a request. The
console calls `enqueueJob()` (`src/utils/aiJobs.ts`), gets a job id back
instantly, and polls with `useJobPolling()`; the work runs on the host one job
at a time, so navigating away no longer loses it. Portrait generation runs this
way today (`CharacterDetailScreen`, `PortraitStudioScreen`); the arc, story, and
session-summary job types exist and are callable, but their console screens
still run those actions inline.

The right-rail activity drawer is mounted **once by `GlobalLayout`**, as a
sibling of the page content, so it is on every route rather than only the
console. `ActivityProvider` (`src/components/layout/ActivityContext.tsx`) owns
the `useJobActivity()` polling, the open/full-screen state, and the row
handlers. Two things still need the console, which has the character roster:
resolving a character id to the screen showing it, and opening a row in place
without a page load. `StatelyLedger` registers both through
`useConsoleActivity()` while it is mounted; on any other page a row instead
deep-links to `/?section=…&item=…&char=…`, which the console route resolves
against its roster.

#### Results are reviewed, never auto-applied

A queued job can finish while you are on another screen, so it does not write
what it generated onto the content. A finished `dnd_portrait` job leaves the
render in the media library with `review: pending`, and the console decides:

- The activity row shows **Review result** and links to the character's screen
  (Portrait Studio for a party member, the NPC sheet for an NPC), carrying the
  job id in `ctx.reviewJobId`.
- That screen previews the render, amber-framed and labelled *not attached yet*,
  next to the portrait it would replace.
- **Accept** calls `resolveJob(id, true)` -> `api/resolve-job.ts`, which is what
  finally sets `field_image`. **Discard** changes nothing on the character; the
  render stays in the media library and can still be picked later.

`usePortraitReview()` (`src/utils/portraitProfile.ts`) owns that whole cycle -
queue, follow, pick a job back up by id, accept, discard - and both portrait
screens drive it, so neither can grow a path that attaches without asking.

#### Story scene illustrations

**Generate image** on the story reader (`ReadStoryFileScreen`) and the public
story page is a queued wizard, not a fake timeout. Stories are too large for one
prompt, so the work is two jobs:

1. `dnd_story_events` posts the body to sidecar `/story/events`, which chunks
   it and returns selectable moments. The operator picks one.
2. `dnd_story_illustration` posts that excerpt plus the checked cast to
   `/story/scene`. ComfyUI renders 768x512 DreamShaper with at most two
   IPAdapter leads, then staggered ReActor swaps. The PNG is stored pending
   review; **Accept** appends it to `field_illustrations`.

The activity bar links both job types to `stories / read` (`?story=` + `?job=`
off-console). Minutes-to-tens-of-minutes is expected; the browser never holds
the ComfyUI request.

Helpers live in `src/utils/storyImage.ts` and
`src/components/console/StoryImageWizard.tsx`.

#### Reading the drawer

- **Queued** and **Running** are separate states with separate dots. A job
  waiting for the host processor is not being worked on, and drawing it as busy
  made us chase a render that had never started.
- **Stalled** rows (`AiJob.stalled`) are jobs whose worker died. They show red
  with a **Requeue** button rather than a spinner that will never resolve.
- **Clear completed** deletes the rows in Drupal - the drawer holds no state of
  its own. It reports how many it kept back for review, and disables itself when
  there is nothing to clear.
- `useJobActivity()` returns a `refresh()` so an action that changes the list
  (clear, requeue) updates at once instead of waiting out the 3s poll.

Session-summary prompt logic (fast-model, non-streaming) lives in the
server-only helper `src/utils/aiSummary.ts`, shared by `summarize-session.ts`,
`campaign-overview.ts`, and `create-story.ts`. A gitignored one-off,
`scripts/backfill-summaries.mjs`, backfills summaries + overviews for existing
campaigns by reusing those endpoints (requires the dev server running).

---

## Environment variables

Two files load, root first:

1. **`../.env`** (project root) — shared service credentials. `gatsby-config.ts`
   loads it and bridges some values to the browser. Server-side / function use:
   `DRUPAL_BASE_URL`, `DRUPAL_GRAPHQL_TOKEN`, `AI_CREATIVE_BASE_URL`,
   `AI_CREATIVE_MODEL`, `OLLAMA_API_KEY`, `SIDECAR_HOST`, `SIDECAR_PORT`,
   `RAG_WIKI_BASE_URL`, `RAG_RULES_BASE_URL`.
2. **`.env.development`** (this folder, gitignored — copy from `.env.example`):
   `SITE_URL`, `SITE_TITLE`, `GATSBY_DRUPAL_BASE_URL`, `GATSBY_AI_MODEL`,
   `GATSBY_AI_MODELS`, `GATSBY_AI_BASE_URL`, `GATSBY_AI_TEMPERATURE`,
   `GATSBY_AI_MAX_TOKENS`, `GATSBY_RAG_WIKI_URL`, `GATSBY_RAG_RULES_URL`.

**Critical rule:** only variables prefixed `GATSBY_` are exposed to browser-side
code. Non-prefixed values are available only at build time and inside serverless
functions. `gatsby-config.ts` bridges `AI_CREATIVE_*` and `RAG_*` from the root
`.env` to their `GATSBY_` equivalents for display screens.

---

## Commands

```bash
npm run develop      # dev server
npm run type-check   # tsc --noEmit
npm run build        # production build
npm run serve        # preview production build
npm run clean        # clear Gatsby cache (fixes most schema/build oddities)
```

For the full first-time setup (DDEV, sidecar, env files, mkcert), follow
[docs/FRONTEND_QUICKSTART.md](../docs/FRONTEND_QUICKSTART.md).

---

## Conventions

See [CLAUDE.md](CLAUDE.md) for the enforced rules: strict TypeScript (no `any`,
no `@ts-ignore`), no emojis, hex-only colours via `tokens.css`, page queries in
`pages/`/`templates/` only, and named exports everywhere except Gatsby pages and
templates.

**The palette is `src/styles/tokens.css` and nothing else defines a colour.**
Feature stylesheets consume tokens; they never write a raw hex the palette
already holds, never redefine a token it declares (they load after it, so the
copy would silently win), and never write `--x: var(--x)`, which is invalid and
drops the colour. Where one value carries several token names, use the more
universal one - `tokens.css` runs from raw palette to semantic roles, so
`#c9a96e` is `--color-gold-mid` before it is `--color-partial`. A genuinely new
colour belongs in `tokens.css`, not in the sheet that needed it.

Enforced by `src/validation/css_palette.py`, which runs as a gate in
`./check.sh`. See AGENTS.md rule 0.6.
