# Drupal CMS Integration — D&D Character Consultant

## Architecture

```mermaid
+-------------------+     +-------------------+     +-------------------+
| Python App        |     | Drupal CMS        |     | Gatsby Frontend   |
+-------------------+     +-------------------+     +-------------------+
| JSON source files |---->| Migrate API       |     |                   |
| AI/TTS/RAG system |     | Content model     |---->| gatsby-source-    |
| Character mgmt    |     | Milvus AI search  |     | drupal plugin     |
+-------------------+     | Entity clone      |     | React components  |
                          +-------------------+     +-------------------+
                                  |
                          +-------------------+
                          | Milvus vector DB  |
                          | Ollama embeddings |
                          +-------------------+
```

**Source of truth:** Python JSON files → Drupal (via Migrate API) → Gatsby (via gatsby-source-drupal)

---

## Status Overview

| Phase | Area | Status |
| ----- | ---- | ------ |
| 1 | DDEV + Drupal install | Done |
| 2 | Content types (all 10) | Done |
| 3 | Taxonomies (27 vocabularies) | Done |
| 4 | Paragraph types | Done |
| 5 | Custom migrate module | Done |
| 6 | AI/Voice/Milvus config | Done (not yet enabled) |
| 7 | Entity clone module | Done |
| 7 | game_edition vocabulary | Done |
| 8 | Gatsby API layer (jsonapi + gatsby modules, CORS, gatsby_user) | Done |
| 9 | Gatsby frontend scaffold (gatsby-config.ts, gatsby-source-drupal) | Done |
| 10 | Python sync layer (src/integration/drupal_sync.py) | Done |
| **11** | **Milvus enable + index** | **Pending (infrastructure)** |
| 12 | Character instance fields (field_source_character boolean, field_campaign ref) | Done |
| **13** | **Gatsby React components** | **Pending** |

---

## Remaining Steps (non-content)

### Step 1 — Enable the API stack in Drupal

```bash
ddev drush en jsonapi gatsby basic_auth serialization -y
ddev drush config:export -y
```

The `gatsby` module provides the webhook endpoint Gatsby uses for incremental
builds and live preview. `jsonapi` is the data transport layer
`gatsby-source-drupal` reads from.

---

### Step 2 — Configure CORS

Gatsby dev server runs on `localhost:8000`. Drupal must allow cross-origin
requests from it.

Edit `drupal-cms/web/sites/default/services.yml` (or create it from
`default.services.yml`):

```yaml
parameters:
  cors.config:
    enabled: true
    allowedHeaders:
      - '*'
    allowedMethods:
      - GET
      - POST
      - PATCH
      - DELETE
      - OPTIONS
    allowedOrigins:
      - 'http://localhost:8000'
      - 'http://localhost:3000'
    exposedHeaders: false
    maxAge: false
    supportsCredentials: true
```

Then rebuild cache:

```bash
ddev drush cache:rebuild
```

---

### Step 3 — Create a Gatsby API user in Drupal

The Gatsby source plugin needs read access to all content via JSON:API.

```bash
# Create dedicated user
ddev drush user:create gatsby_user --password=<secure_password>

# Grant content viewer role (or configure permissions as needed)
ddev drush user:role:add authenticated gatsby_user
```

Configure JSON:API permissions at
`/admin/people/permissions#module-jsonapi` — ensure anonymous or the gatsby
user can read all content types.

For production, use **Simple OAuth** instead of Basic Auth:

```bash
ddev composer require drupal/simple_oauth
ddev drush en simple_oauth -y
```

---

### Step 4 — Add character instance fields via UI

These fields were removed because pushing config via `configFactory` does not
create DB tables. They must be added through the Drupal UI to create the
schema correctly.

Admin: Structure → Content types → Character → Manage fields

| Label | Machine name | Type | Settings |
| ----- | ------------ | ---- | -------- |
| Source Character (Template) | `field_source_character` | Entity reference | References: Character |
| Campaign Instance | `field_campaign` | Entity reference (reuse existing storage) | References: Campaign vocab |

After adding, export config:

```bash
ddev drush config:export -y
```

---

### Step 5 — Enable Milvus AI search

Config is already defined in sync. Enable the modules when the Milvus
instance is running:

```bash
ddev drush en search_api ai_search ai_vdb_provider_milvus ai_provider_ollama -y
ddev drush search-api:index milvus_ai_content
ddev drush config:export -y
```

The index covers all node content. It uses Ollama `nomic-embed-text` for
embeddings and cosine similarity for retrieval.

For the Milvus container, add to `.ddev/docker-compose.milvus.yaml`:

```yaml
services:
  milvus:
    image: milvusdb/milvus:v2.4.0
    ports:
      - "19530:19530"
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
```

---

### Step 6 — Initialize the Gatsby frontend project

```bash
# From project root
npm create gatsby-app frontend -- --template minimal
cd frontend
npm install gatsby-source-drupal gatsby-plugin-image gatsby-transformer-sharp
```

Configure `frontend/gatsby-config.js`:

```js
module.exports = {
  plugins: [
    {
      resolve: 'gatsby-source-drupal',
      options: {
        baseUrl: 'https://drupal-cms.ddev.site/',
        apiBase: 'jsonapi',
        basicAuth: {
          username: process.env.DRUPAL_USER,
          password: process.env.DRUPAL_PASSWORD,
        },
        // Enable Gatsby module fast builds
        fastBuilds: true,
      },
    },
  ],
}
```

Add `.env.development`:

```properties
DRUPAL_USER=gatsby_user
DRUPAL_PASSWORD=<password>
GATSBY_DRUPAL_URL=https://drupal-cms.ddev.site
```

---

### Step 7 — Configure Gatsby module webhook in Drupal

Once Gatsby is running, register the preview/build webhook:

Admin: Configuration → Gatsby → Settings

- Gatsby preview server URL: `http://localhost:8000`
- Build webhook URL: (Gatsby Cloud URL or local)

Or via drush:

```bash
ddev drush config:set gatsby.settings server_url 'http://localhost:8000' -y
```

---

### Step 8 — (Optional) Python sync layer

The Drupal Migrate API handles initial and re-imports from JSON files.
A lightweight Python sync class remains useful for programmatic updates
from the consultant app (e.g. updating a character's plot actions after
a session).

Create `src/integration/drupal_sync.py` — connects to Drupal JSON:API
to push delta updates from the Python app without a full migrate re-run.

Key methods needed:

- `push_character(file_id)` — PATCH existing character node
- `push_story(campaign, filename)` — POST or PATCH story node
- `trigger_gatsby_build()` — POST to Gatsby webhook after sync

---

## Content model — what exists

### Content types

| Machine name | Purpose |
| ------------ | ------- |
| `character` | PCs and major NPCs (unified) |
| `npc` | Simple/minor NPCs |
| `story` | Campaign story files |
| `session` | Session records |
| `item` | Weapons, armor, magic items |
| `spell` | Spell reference nodes |
| `feat` | Feat reference nodes |
| `ability` | Class ability nodes |
| `monster` | Encounter monster stat blocks |
| `basic_page` | Static CMS pages |

### Key taxonomies

| Vocabulary | Used for |
| ---------- | -------- |
| `species` / `lineage` | Character race/subrace |
| `class` / `subclasses` | D&D class and archetype |
| `campaign` | Campaign grouping (also drives character instances) |
| `game_edition` | 5e / 5.5e (2024) / Homebrew |
| `traits` | Personality, ideals, bonds, flaws |
| `skills` / `abilities` / `feats` / `spells` | Rulebook content |
| `locations` | In-world places |
| `factions` | Political/organizational groups |
| `voice_ids` | Piper TTS voice identifiers |

### Paragraph types

| Type | Used on |
| ---- | ------- |
| `class` | Character class + subclass + level |
| `ability_scores` + `ability_score` | Nested ability score wrapper |
| `spell_reference` / `feat_reference` / `ability_reference` | Rulebook item refs |
| `spell_slot` | Spell slot levels |
| `wysiwyg` | Rich text (backstory etc.) |
| `relationship` | Inter-character relationship graph |

### Character instance pattern

A base character (template) has no `field_campaign` set. When assigned to a
campaign, clone it with **Entity Clone**, then set:

- `field_source_character` → original template node
- `field_campaign` → target campaign term

Story and session nodes reference campaign instances, not templates.
Milvus search can filter by `field_campaign` to scope results per campaign.

---

## Module inventory

| Module | Status | Purpose |
| ------ | ------ | ------- |
| `drupal/gatsby` | Installed, not enabled | Webhook + fast builds for Gatsby source |
| `drupal/jsonapi_extras` | Installed, enabled | Required by gatsby; field visibility |
| `drupal/entity_clone` | Installed, enabled | Clone characters per campaign |
| `drupal/conditional_fields` | Installed, enabled | Form UX conditionals (patched) |
| `drupal/paragraphs` | Enabled | Complex field structures |
| `drupal/migrate_plus` / `migrate_tools` | Enabled | JSON → Drupal import |
| `drupal/search_api` | Installed, not enabled | Milvus index management |
| `drupal/ai` / `ai_search` / `ai_vdb_provider_milvus` | Installed, not enabled | Semantic search |
| `drupal/ai_provider_ollama` | Installed, not enabled | Ollama embedding provider |
| `basic_auth` | Disabled | Enable for Gatsby API auth (interim) |
| `serialization` | Disabled | Required by jsonapi/rest |
| `jsonapi` | Disabled | Enable for Gatsby source plugin |

---

## Implementation checklist

### Drupal side

- [ ] Enable `jsonapi`, `gatsby`, `basic_auth`, `serialization`
- [ ] Configure CORS in `services.yml`
- [ ] Create `gatsby_user` with read permissions
- [ ] Add `field_source_character` and `field_campaign` to character (UI)
- [ ] Enable Milvus modules when instance available
- [ ] Configure Gatsby webhook URL in Drupal admin

### Gatsby frontend

- [ ] Scaffold Gatsby project in `frontend/`
- [ ] Install and configure `gatsby-source-drupal`
- [ ] Build GraphQL queries for character, npc, story, item pages
- [ ] Build component library (CharacterSheet, NPCCard, StoryReader, ItemCard)
- [ ] Build campaign dashboard with character instance support
- [ ] Add search UI backed by Milvus (via Drupal Search API or direct)

### Python app

- [ ] Create `src/integration/drupal_sync.py` for delta updates
- [ ] Add `--sync-drupal` CLI flag to consultant
- [ ] Add post-session hook to push story + character updates
