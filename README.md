# D&D Character Consultant System

An AI-assisted toolkit for running Dungeons & Dragons campaigns — characters,
NPCs, stories, items, monsters, sessions, and campaign tracking — with AI
consultation, story generation, RAG-backed lore, and semantic search.

The project is a **three-tier application**. A user does everything from the web
frontend; the Python engine does the heavy lifting; Drupal stores the truth.

```text
  Gatsby frontend  -->  Drupal CMS (source of truth)  <--  Python engine
  (what users use)      (content database, GraphQL)        (AI, RAG, sync)
                                   ^
                          DDEV hosts Drupal + Ollama + Milvus + Solr
```

> This project began as a Python CLI (tagged `v1.0.0`). It has since moved to the
> three-tier model above; **the interactive CLI is deprecated** and likely no
> longer runs end to end. New work targets the frontend. The full story is in
> [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Architecture at a glance

| Tier | Lives in | Role |
| ---- | -------- | ---- |
| **Frontend** | [`frontend/`](frontend/) | Gatsby + React UI; the primary interface. Reads Drupal over GraphQL, writes and calls AI via serverless functions. |
| **Drupal CMS** | [`drupal-cms/`](drupal-cms/) | Headless content store and single source of truth; exposes content over GraphQL. |
| **Python engine** | [`src/`](src/) | AI client, RAG + Milvus semantic search, validation, calendar/timeline, spotlight, and Drupal sync; also runs the search sidecar. |

Anything the old CLI did is now reachable from the frontend — see the capability
map in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#capability-map-cli-feature---where-it-lives-now).

---

## Documentation map

| Doc | What it covers |
| --- | -------------- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | The three tiers, data flow, runtime services, source-of-truth rules |
| [docs/FRONTEND_QUICKSTART.md](docs/FRONTEND_QUICKSTART.md) | **Start here** — get everything running and use it from the frontend |
| [frontend/README.md](frontend/README.md) | Frontend layout, pages, serverless functions, env vars |
| [src/README.md](src/README.md) | Python engine package structure and commands |
| [src/sidecar/README.md](src/sidecar/README.md) | The FastAPI search/spotlight sidecar |
| [docs/DRUPAL.md](docs/DRUPAL.md) | Drupal content types, GraphQL exposure, sync flow |
| [drupal-cms/AGENTS.md](drupal-cms/AGENTS.md) | Drupal/DDEV/PHP rules and the source-of-truth policy |
| [AGENTS.md](AGENTS.md) | Project-wide engineering standards (Python, tests, conventions) |
| [tests/README.md](tests/README.md) | Test suite |

---

## Quick start

The primary path is the frontend. Full instructions (prerequisites, env files,
indexing) are in [docs/FRONTEND_QUICKSTART.md](docs/FRONTEND_QUICKSTART.md).

```bash
# 1. Configure environment
cp .env.example .env                              # shared service credentials
cp frontend/.env.example frontend/.env.development # frontend site/browser settings

# 2. Start Drupal (+ Ollama, Milvus, Solr), the sidecar, and Gatsby
./start.sh --no-cli

# 3. Seed the semantic index, then open the app
python3 -m src.cli.dnd_consultant --reindex
#    Frontend: http://localhost:$GATSBY_PORT
```

### Legacy CLI (deprecated, `v1.0.0`)

```bash
python -m src.cli.dnd_consultant   # interactive menu; may not run end to end
```

The `--reindex`, `--milvus-status`, and `--sync-drupal` flags are still used as
engine utilities; the interactive menu is not maintained.

---

## What the system does

- **Characters & NPCs** — profiles with class, lineage, abilities, personality,
  AI and voice settings. NPCs are character records flagged by type.
- **Stories** — write or AI-generate session narratives; read them per campaign.
- **Items, monsters, spells** — registries including homebrew content.
- **Campaigns & party** — group characters, track session history.
- **Search** — natural-language search over all content via a Milvus vector
  index and a query-parsing sidecar.
- **AI consultation, RAG, spotlight, calendar/timeline** — provided by the
  Python engine.

It does **not** automate gameplay, roll dice, or run sessions for you — it
assists your storytelling and bookkeeping.

---

## Repository layout

```text
frontend/      # Gatsby + React frontend (primary UI)
drupal-cms/    # Headless Drupal CMS (source of truth)
src/           # Python engine (AI, RAG, validation, sync, sidecar, CLI)
game_data/     # Local JSON content (characters, campaigns, npcs, items)
docs/          # Project documentation (this map)
plans/         # Implemented feature design docs (historical)
tests/         # Engine test suite
start.sh       # Brings up Drupal + sidecar + Gatsby
```

---

## Prerequisites

- DDEV (Drupal + Ollama + Milvus + Solr), Node.js 18+, Python 3.8+, mkcert.
- `pip install -r requirements.txt` for the engine and sidecar.

See [docs/FRONTEND_QUICKSTART.md](docs/FRONTEND_QUICKSTART.md) for details.
