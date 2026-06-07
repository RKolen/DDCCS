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
| `campaign-party.ts` | POST | Drupal (`addCharacterToCampaign`) | Add a character to a campaign |
| `create-story.ts` | POST | Drupal (`createStory`) | Persist a finished story |
| `update-character.ts` | POST | Drupal (`updateCharacter`) | PATCH optional character fields |
| `generate-story.ts` | POST | Ollama-compatible LLM | Stream an AI-generated story (SSE) |
| `spotlight.ts` | POST | Sidecar (`localhost:$SIDECAR_PORT`) | Spotlight scores for a party |

`generate-story.ts` streams Server-Sent Events from
`AI_CREATIVE_BASE_URL/chat/completions`. `spotlight.ts` calls the Python sidecar
(see [src/sidecar/README.md](../src/sidecar/README.md)).

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
