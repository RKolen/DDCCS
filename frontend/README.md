# Frontend — D&D Campaign Console

The Gatsby frontend is the primary interface to the system. A user manages
characters, NPCs, stories, items, monsters, party, and search from here without
ever logging into Drupal. It reads content from Drupal over GraphQL and performs
writes and live AI through its own serverless functions.

- **Get it running:** [docs/FRONTEND_QUICKSTART.md](../docs/FRONTEND_QUICKSTART.md)
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
    |   `-- layout/       # Global layout / chrome
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
| `update-character.ts` | POST | Drupal (`updateCharacter`) | PATCH optional character fields |
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
| `tts.ts` | POST | Sidecar (`/tts/speak`) | Synthesise a reply to speech (Piper, using the character's voice + speed), returns `audio/wav` |
| `update-voice.ts` | POST | Drupal (`updateCharacter`) | Save a character's voice id / pitch / speed (consultation voice mini-wizard) |
| `spotlight.ts` | POST | Sidecar (`localhost:$SIDECAR_PORT`) | Spotlight scores for a party |
| `generate-portrait.ts` | POST | Sidecar (`/character/portrait`) + Drupal (`setCharacterPortrait`) | Generate a character portrait with local ComfyUI (long, timeout-free call), then persist it onto the character's `field_image`; returns the new `imageUrl`. Requires `COMFYUI_ENABLED=true` on the sidecar (503 otherwise) |
| `list-portrait-media.ts` | GET | Drupal (`mediaImages`) | List image media from the library (`{ media: [{ id, name, url, alt }] }`) for the portrait picker |
| `set-portrait-media.ts` | POST | Drupal (`setCharacterImage`) | Point a character's `field_image` at an existing media (no new file); returns the new `imageUrl` |

`generate-story.ts` streams Server-Sent Events from
`AI_CREATIVE_BASE_URL/chat/completions`. `spotlight.ts` calls the Python sidecar
(see [src/sidecar/README.md](../src/sidecar/README.md)).

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
