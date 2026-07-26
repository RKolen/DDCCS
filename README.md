# D&D Character Consultant System

An AI-assisted toolkit for running Dungeons & Dragons campaigns — characters,
NPCs, stories, items, monsters, sessions, and campaign tracking — with AI
consultation, story generation, character portraits, multi-voice narration,
RAG-backed lore, and semantic search. It runs entirely on local models by
default, and points at a hosted LLM endpoint if you would rather.

The project is a **three-tier application**. A user does everything from the web
frontend; the Python engine does the heavy lifting; Drupal stores the truth.

```text
  Gatsby frontend  -->  Drupal CMS (source of truth)  <--  Python engine
  (what users use)      (content database, GraphQL)        (AI, RAG, sync)
                                   ^
                DDEV hosts Drupal + Milvus + Solr; the host runs
                Ollama, ComfyUI, Piper, the sidecar, and the job queue
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

# 2. Start Drupal (+ Milvus, Solr), the sidecar, the AI job queue, and Gatsby
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

### Content and campaign management

- **Characters & NPCs** — profiles with class, lineage, abilities, personality,
  AI and voice settings. NPCs are character records flagged by type.
- **Stories** — write or AI-generate session narratives; read them per campaign,
  with AI session recaps and a synthesized campaign overview.
- **Items, monsters, spells** — registries including homebrew content.
- **Campaigns & party** — group characters, track session history.
- **Search** — natural-language search over all content via a Milvus vector
  index and a query-parsing sidecar.

### AI features

No cloud service is required: the default setup runs every model on this
machine, and nothing heavy runs inside DDEV. The chat/story endpoint is
OpenAI-compatible, so a hosted service can stand in for the local one; portraits
and narration are local services either way.

- **Consultation & story generation** — talk to a character in voice, or
  generate a session narrative from your beats (any OpenAI-compatible model;
  local Ollama by default).
- **Character arc analysis** — read a character's whole story history into an
  arc: direction, stage, metric trend lines, relationships, and goals.
- **Portrait generation (ComfyUI)** — generate a character portrait from the
  profile, edit the prompt that drives it, enhance that prompt with a model, or
  run **image -> prompt** to describe an existing portrait back into words. The
  result is stored as a real media entity on the character, and any portrait in
  the library can be reassigned instead of regenerating.
- **Voice narration (Piper TTS)** — read a story aloud with **multiple voices**:
  dialogue is segmented by speaker and each character narrates in their own
  configured voice, pitch, and speed.
- **RAG, spotlight, calendar/timeline** — rules- and lore-aware retrieval,
  spotlight scoring, and in-world date tracking from the Python engine.

Because a CPU model run takes minutes, the long jobs (portraits, arc analysis,
story generation, session summaries) are **queued and run one at a time** on the
host, tracked in the console's activity rail — start several and walk away.

### What it looks like

Characters in the console, with portraits generated locally through ComfyUI:

![The console's character list showing three characters with locally generated
portraits](docs/images/console-character-portraits.png)

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
start.sh       # Brings up Drupal + sidecar + Gatsby + AI job queue (+ ComfyUI when enabled)
```

---

## Prerequisites

- DDEV (Drupal + Milvus + Solr), Node.js 18+, Python 3.8+, mkcert.
- `pip install -r requirements.txt` for the engine and sidecar. This also
  installs **Piper TTS**, whose `.onnx` voices live in `game_data/piper/voices/`.
- **An OpenAI-compatible LLM endpoint** (`AI_CREATIVE_BASE_URL` + a key) for
  chat, story generation, and arc analysis — a cloud service works. The default
  is **Ollama on the host**, which is what keeps everything local and free; run
  it on the host, never in DDEV, where heavy models double-load and crash the
  box.

Optional, per feature:

- **`sox`** — pitch control for narration; Piper itself has none, so without it
  voices still play, just without a pitch offset.
- **ComfyUI** — portrait generation, installed at `COMFYUI_DIR` in its own venv
  with a Stable Diffusion checkpoint. Off unless `COMFYUI_ENABLED=true`; the
  console shows the reason rather than breaking when it is missing.

Two features do assume **Ollama's native API** rather than the OpenAI-compatible
one: image-to-prompt vision (`/api/generate` with a `num_ctx` cap) and unloading
a resident model before ComfyUI loads its checkpoint. Both are optional — the
rest of the system runs against any compatible endpoint.

Piper and ComfyUI are reached over HTTP through the sidecar (`/tts/speak`,
`/character/portrait`), so a different voice or image engine means a new client
behind those endpoints — the frontend, Drupal, and the job queue never name the
engine. The clients themselves are engine-specific, so it is a seam, not a
drop-in switch.

See [docs/FRONTEND_QUICKSTART.md](docs/FRONTEND_QUICKSTART.md) for details.
