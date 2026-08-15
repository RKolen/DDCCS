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
