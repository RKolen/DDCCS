# Architecture

The D&D Character Consultant System is a three-tier application. A user drives
everything from the **Gatsby frontend**; the **Python engine** does the heavy
lifting (AI, RAG, validation, indexing); and **Drupal CMS** is the single source
of truth where all content lives.

```text
        +--------------------------+
        |     Gatsby frontend      |
        |  (React 18 + TS, SSG)    |
        +------------+-------------+
                     |
     +---------------+----------------+----------------------+
     | 1. GraphQL    | 2. Serverless  | (browser)            |
     |    reads      |    functions   |                      |
     v               v                v                      |
+----------+   +-----------------------------+        +-------------+
|  Drupal  |<--|  frontend/src/api/*.ts      |------->|   Ollama    |
|   CMS    |   |  (Gatsby Functions)         |        | (LLM, chat) |
| (truth/  |   +--------------+--------------+        +-------------+
|   DB)    |                  | 3. sidecar HTTP
+----+-----+                  v
     ^               +-------------------+        +-------------------+
     |               |  FastAPI sidecar  |------->| Python engine     |
     | drupal_sync   |  (search/spotlight)|       | (src/, imported)  |
     | (push/build)  +-------------------+        +-------------------+
     |                                                     |
+----+-----------------------------------------------------+
|                  Python engine (src/)                    |
|  validation - RAG/Milvus - calendar - spotlight - sync   |
+----------------------------------------------------------+
```

Drupal, Milvus, and Solr run as **DDEV** containers. Everything that loads a
model runs on the **host** (see `start.sh`): Ollama, the sidecar (which owns
Piper TTS), the AI job-queue processor, and - when `COMFYUI_ENABLED=true` -
ComfyUI, alongside the Gatsby dev server. Heavy models inside DDEV double-load
and crash the box, so that split is a rule, not a preference.

---

## The three tiers

### 1. Gatsby frontend (`frontend/`)

Static-site generator + dev server (React 18, TypeScript 6). Reads content from
Drupal at build/dev time via `gatsby-source-graphql` and renders character,
story, item, monster, NPC, party, and search pages. It also ships **Gatsby
serverless functions** (`frontend/src/api/`) that handle every write and every
live-AI call, so the user never logs into Drupal directly.

See [frontend/README.md](../frontend/README.md) for the full component and page
layout.

### 2. Drupal CMS (`drupal-cms/`) — source of truth

Headless Drupal holds every content entity (characters, stories, items,
monsters, spells, sessions) and exposes them over GraphQL via
`graphql_compose`. **Drupal is authoritative for all field names and GraphQL
type names** — never guess them.

See [docs/DRUPAL.md](DRUPAL.md) for content types and GraphQL exposure, and
[drupal-cms/AGENTS.md](../drupal-cms/AGENTS.md) for DDEV/PHP rules.

### 3. Python engine (`src/`)

The original system, now repositioned as a reusable engine. It powers:

- **Validation** of all JSON data (`src/validation/`).
- **RAG + semantic search** over a Milvus vector index (`src/ai/`).
- **Drupal wiki cache** — storing fetched wiki pages as Drupal nodes over
  GraphQL (`src/integration/drupal_sync.py`).
- **The sidecar** FastAPI service (`src/sidecar/`).
- **Spotlight** scoring, **calendar**, **timeline**, **character arc**, and
  more (see [src/README.md](../src/README.md)).

> The interactive Python CLI (`dnd_consultant.py`) is the **legacy `v1.0.0`
> path** and is deprecated. The engine changed enough that it likely no longer
> runs end to end. New work targets the frontend.

---

## How the frontend reaches the backend

The frontend uses three distinct channels.

### Channel 1 — GraphQL reads (Drupal)

`gatsby-source-graphql` stitches Drupal's `graphql_compose` schema into Gatsby
under the `drupal` field. Page queries in `frontend/src/pages/` and
`frontend/src/templates/` read all content this way. The endpoint is
`${DRUPAL_BASE_URL}/graphql` (configured in `frontend/gatsby-config.ts`),
**not** the Gatsby dev server at `localhost:$GATSBY_PORT`, whose `___graphql`
explorer is only a local IDE over the stitched schema.

### Channel 2 — Gatsby serverless functions (`frontend/src/api/`)

Each `.ts` file under `frontend/src/api/` is a Gatsby Function (an HTTP endpoint
served by the dev server / build). They handle writes and live AI:

| Function | Method | Talks to | Purpose |
| -------- | ------ | -------- | ------- |
| `campaigns.ts` | POST | Drupal (`createCampaign` mutation) | Create a campaign term |
| `create-character.ts` | POST | Sidecar + Drupal (`createCharacter`, `addCharacterToCampaign`) | Derive a sheet (sidecar), persist a source character, clone into the active campaign |
| `campaign-party.ts` | POST | Drupal (`addCharacterToCampaign`) | Add a character to a campaign |
| `create-story.ts` | POST | Drupal (`createStory` mutation) | Persist a finished story |
| `update-character.ts` | POST | Drupal (`updateCharacter` mutation) | PATCH voice settings and the image prompt |
| `update-character-profile.ts` | POST | Drupal (`updateCharacterProfile` mutation) | PATCH the character editor's profile fields |
| `arc-analyze-story.ts` | POST | Drupal (read) + Sidecar (`/character/arc/story`) | Analyse one story into a data point (looped per story with progress) |
| `arc-aggregate.ts` | POST | Sidecar (`/character/arc/aggregate`) | Aggregate the per-story data points into the full arc |
| `save-arc.ts` | POST | Drupal (`saveCharacterArc` mutation) | Persist an accepted arc analysis |
| `generate-story.ts` | POST | Ollama-compatible endpoint | Stream an AI-generated story (SSE) |
| `spotlight.ts` | POST | Sidecar | Get spotlight scores for a party |

Drupal mutations come from custom GraphQL resolvers in the Drupal layer. The AI
call streams directly from `AI_CREATIVE_BASE_URL` (an Ollama-compatible
`/chat/completions` endpoint).

### Channel 3 — FastAPI sidecar (`src/sidecar/`, `$SIDECAR_PORT`)

A small Python service that imports the engine in-process. It normalises search
queries and computes spotlight scores. Routes:

- `GET /health`
- `POST /search/parse-query` — natural-language query normalisation
- `POST /eval/spotlight` — spotlight scoring via `SpotlightEngine`
- `POST /character/arc/story` + `/character/arc/aggregate` — two-step character
  arc analysis (per-story data point, then aggregate); `/character/arc` is the
  single-shot equivalent
- `POST /relations/suggest` + `/relations/merge` — story-arc relationship
  suggestion, one subject per call, then a merge that collapses reciprocal
  pairs (`src/sidecar/relation_routes.py`)
- `POST /arc-draft/propose` + `/arc-draft/npcs` — propose the story arc a
  campaign's played sessions add up to, and read the NPC cast those sessions
  name (`src/sidecar/arc_draft_routes.py`)
- (plus the `/character/*` build/skill/equipment and `/tts/speak` +
  `/tts/segment` routes)

See [src/sidecar/README.md](../src/sidecar/README.md).

### Channel 4 — Queued AI jobs (Drupal Advanced Queue -> host)

Anything that takes minutes runs as a **job**, not a held-open request. The
console posts to `api/enqueue-job.ts`, Drupal's `enqueueAiJob` mutation drops it
on the single `dnd_ai` queue, and one processor on the host drains that queue
**one job at a time** — which is what keeps two large models from being resident
at once on a CPU-only box. The console polls `api/job-status.ts` (`aiJob` /
`aiJobs`), so navigating away no longer loses the work.

```text
console --enqueue--> Drupal (dnd_jobs)      queue: dnd_ai, one at a time
                          |
     drush advancedqueue:queue:process (host daemon, started by start.sh)
                          |
        +-----------------+------------------+
        |                                    |
  sidecar /character/portrait          console API routes
  (single model call; the job           (multi-step orchestrations:
   writes file + media itself)           run-arc-analysis,
                                          generate-story-text,
                                          store-session-summary)
```

Job types (`drupal-cms/web/modules/custom/dnd_jobs`):

| Job type | Runs | Stores |
| -------- | ---- | ------ |
| `dnd_portrait` | sidecar `/character/portrait` | file + media only; result carries `imageUrl`, `usedReference`, and `review: pending`, and **does not** set `field_image` |
| `dnd_arc_analysis` | console `run-arc-analysis` | per-story analyses + the saved arc |
| `dnd_arc_relations` | console `run-arc-relations` | the suggested relations on the job, for review; **does not** write them onto the arc |
| `dnd_story_generation` | console `generate-story-text` | the story text on the job, for review |
| `dnd_session_summary` | console `store-session-summary` | the summary on the campaign term |
| `dnd_arc_backfill` | console `run-arc-backfill` | the recaps it produced on the campaign term, and the proposed arc plus discovered cast on the job for review; **does not** create the arc or any NPC |

#### Story arcs and their relationship web

A `story_arc` node is the multi-story plan a run of stories is written against.
It carries the premise, the act spine, the antagonist faction, the party, and
two collections of `arc_relationship_pair` paragraphs — party-internal bonds and
party-to-NPC connections. Stories point back at their arc through
`field_story_arc`, so the chain is campaign -> arc -> story.

Suggesting the web is a fan-out, for the same reason arc analysis is: a large
cast is hundreds of possible connections, too many for one local inference pass.
One call per party member, then a merge:

```text
console (or queue worker)
   |  per subject
   +--> api/suggest-arc-relations --> sidecar /relations/suggest --> instruct model
   |
   +--> api/merge-arc-relations   --> sidecar /relations/merge    (dedupe pairs)
   |
   +--> accept/reject review --> api/save-arc-relations --> Drupal saveStoryArcRelations
```

The interactive run loops in the browser to show progress; the queued run
(`dnd_arc_relations`) loops on the host via `run-arc-relations` so the tab can
be closed. Either way the operator reviews before anything is written, because
`saveStoryArcRelations` replaces a whole relation side.

The suggestion model must be an **instruct** model. A local "thinking" model
ignores `think:false` over the OpenAI endpoint and spends its whole token budget
reasoning, returning empty content; `RELATIONS_PROFILE` selects the profile.

#### Backfilling an arc for a campaign that predates arcs

A campaign played before the arc feature has stories but no arc, which leaves
the arc screen empty and relationship suggestion with nothing to hang on — its
roster and context both come from an arc. The backfill reads the arc out of the
play history instead:

```text
console (or queue worker)
   |
   +--> api/campaign-recaps   --> Drupal (stored session_summary paragraphs)
   |
   |  per session with no recap
   +--> api/summarize-story   --> fast model --> Drupal setSessionSummary
   |
   +--> api/draft-arc         --> sidecar /arc-draft/propose --> instruct model
   |
   +--> api/extract-story-npcs --> sidecar /arc-draft/npcs   --> instruct model
   |
   +--> editable review --> api/create-npc      --> Drupal createNpcStub
                        --> api/create-story-arc --> Drupal createStoryArc
```

The cast is asked as its own question rather than bolted onto the arc prompt.
A campaign's NPC roster is not its cast: one ported from elsewhere has stories
full of people who have no character node, so offering the arc only the NPCs
already on record offers it people who never appear in the story. Names that
match the roster come back marked known; the rest are offered as stubs — a
name, one line on who they are, and where that line came from. `createNpcStub`
returns the existing NPC for a name the campaign already has, so a rerun of a
non-deterministic model cannot fill the roster with duplicates.

Level range and target-story count are deliberately not drafted. Both stay
fluid for the life of an arc, so a model reading the past has nothing to say
about them; they are set in the arc editor.

The draft is read from the **recaps, not the story bodies**: a campaign's
bodies run to hundreds of thousands of characters and will not fit a local
context, while its recaps fit in one call. Summarising persists per session, so
a run that dies halfway leaves the recaps it earned and a rerun resumes.

Nothing reaches Drupal until the operator accepts the proposal — an arc is the
plan a campaign's stories hang off, so an unattended job must not create one
nobody has read. The review form makes every field editable and both rosters
hand-ticked. Discarding leaves the campaign untouched; the recaps are kept
either way, since they are useful on their own.

Drafting needs an **instruct** model for the same reason suggestion does;
`ARC_DRAFT_PROFILE` selects the profile.

#### Nothing a job generates is applied unattended

A job finishes on its own schedule, which means it can finish while the operator
is on a different screen or away from the console entirely. Writing its output
straight onto the content would let a background render replace a portrait
somebody deliberately chose, so a job type that generates content stops one step
short: it stores the render in the media library and marks its result
`review: pending`.

```text
job finishes -> result: { mediaId, imageUrl, review: pending }
                          |
        activity drawer row: "Review result" -> the character's screen
                          |
        Accept --> resolveAiJob(id, accepted: true)  -> field_image = mediaId
        Discard -> resolveAiJob(id, accepted: false) -> content untouched
```

`resolveAiJob` is the only path that applies a generated result, and it records
the decision back on the job (`review: accepted | discarded`) so the activity
drawer stops asking. Discarding is not destructive: the render stays in the
media library and can still be chosen later from the portrait picker.

The console side is one shared hook, `usePortraitReview()`
(`frontend/src/utils/portraitProfile.ts`), used by both portrait entry points -
which is what keeps either screen from growing a path that attaches without
asking.

A job type only calls the sidecar directly when the work is a single model call.
Multi-step orchestrations already exist as console routes and are called there
rather than growing a second copy of the same prompt/chunking logic in PHP; what
the queue adds is serialization, persistence, and tracking.

The processor is started by `start.sh` (`JOB_QUEUE_ENABLED`, logs to
`.jobqueue.log`) and needs `SIDECAR_URL`, `GATSBY_SERVER_URL`, and
`SIDECAR_JOB_TIMEOUT` in the DDEV web container. Because the container reaches
the host over its Docker gateway rather than loopback, the sidecar listens on
`SIDECAR_BIND_HOST` (every interface) while host clients keep dialling
`SIDECAR_HOST`.

### Engine to Drupal — `drupal_sync`

`src/integration/drupal_sync.py` is the engine's wiki page cache client. It
stores fetched wiki pages as `wiki_cache` nodes so the CMS owns the RAG cache
and it survives restarts, over four GraphQL operations supplied by the
`dnd_content` module: `wikiCacheEntry`, `wikiCacheCount`, `setWikiCacheEntry`,
and `deleteWikiCacheEntry`.

All Drupal access is GraphQL. JSON:API is disabled server-side
(`jsonapi_extras.settings` sets `default_disabled: true`, and no
`jsonapi_resource_config` entities re-enable it), so every JSON:API path 404s.
The old `push_character` / `push_story` / `push_item` / `push_monster` seed
methods and the `--sync-drupal` flag were removed with it; content is written
by the Gatsby serverless functions above.

---

## Capability map (CLI feature -> where it lives now)

Everything the legacy CLI did is now reachable from the frontend, backed by the
engine and Drupal.

| Capability | Frontend entry | Backend |
| ---------- | -------------- | ------- |
| Browse characters / NPCs | `pages/characters.tsx`, `pages/npcs.tsx` | Drupal GraphQL |
| Character sheet | `templates/character.tsx` | Drupal GraphQL |
| Create a character (from template) | `CreateCharacterScreen` wizard | `api/create-character.ts` -> sidecar `/character/build-from-template` + Drupal (`createCharacter`, `addCharacterToCampaign`) |
| Edit character (optional fields) | character edit screen | `api/update-character.ts` -> Drupal |
| Create / AI-generate a story | story forge screens | `api/generate-story.ts` (AI), `api/create-story.ts` (save) |
| Read stories | `pages/stories.tsx`, `templates/story.tsx`, `pages/campaign-reader.tsx` | Drupal GraphQL |
| Multi-voice story narration | `templates/story.tsx` Narrate medallion | `api/tts-segment.ts` -> sidecar `/tts/segment`, then `api/tts.ts` -> `/tts/speak` per clip |
| Items / monsters / spells | `pages/items.tsx`, `pages/monsters.tsx`, `templates/*` | Drupal GraphQL |
| Manage party / campaigns | `pages/party.tsx` | `api/campaigns.ts`, `api/campaign-party.ts` -> Drupal |
| Search | `pages/search.tsx` | sidecar `/search/parse-query` + Milvus |
| Spotlight scoring | console screens | `api/spotlight.ts` -> sidecar `/eval/spotlight` |
| Character arc analysis | `CharacterArcScreen` (Characters tab) | `api/arc-analyze-story.ts` (per story) + `api/arc-aggregate.ts` -> sidecar `/character/arc/*`; `api/save-arc.ts` -> Drupal (`saveCharacterArc`) |
| Portrait generation | `CharacterDetailScreen`, `PortraitStudioScreen` | queued `dnd_portrait` job -> sidecar `/character/portrait` -> Drupal file + media (not attached until accepted). A regeneration passes the attached portrait as an IPAdapter reference so the likeness carries over; the Studio can turn that off or reweight it |
| Long-running AI (queue) | activity drawer (right rail) | `api/enqueue-job.ts` + `api/job-status.ts` -> Drupal `enqueueAiJob` / `aiJob(s)` |
| Accept / discard a generated result | activity row -> the target screen | `api/resolve-job.ts` -> Drupal `resolveAiJob` |
| Recover a stalled job | activity row **Requeue**, or `drush dnd-jobs:recover` (run by `start.sh` on every processor restart) | `api/requeue-job.ts` -> Drupal `requeueAiJob`; `dnd_jobs_cron()` sweeps expired leases, capped at 2 retries |
| Clear the activity log | activity drawer **Clear completed** | `api/clear-jobs.ts` -> Drupal `clearAiJobs` (deletes finished rows; keeps ones awaiting review) |
| NPC profile validation | NPC validator screen | Drupal GraphQL + engine |
| RAG / semantic retrieval | implicit in AI flows | `src/ai/` + Milvus |

---

## Runtime services and ports

Started by `start.sh` (values are `.env`-driven; defaults shown):

```bash
./start.sh --no-cli     # bring up Drupal + sidecar + Gatsby (no legacy CLI)
```

---

## Source-of-truth rules

- **Drupal owns field and GraphQL type names.** Verify against
  `drupal-cms/config/sync/field.field.node.<bundle>.<field>.yml` or by
  introspecting `${DRUPAL_BASE_URL}/graphql`. Never guess.
- **NPCs are character nodes**, distinguished by `field_character_type` — there
  is no separate NPC bundle. (A legacy `nodeNpcs` GraphQL type is deprecated.)
- After changing Drupal config, run
  `ddev drush config:import -y && ddev drush cache:rebuild`, then
  `npm run clean` in `frontend/`.

Full detail: [docs/DRUPAL.md](DRUPAL.md) and
[drupal-cms/AGENTS.md](../drupal-cms/AGENTS.md).
