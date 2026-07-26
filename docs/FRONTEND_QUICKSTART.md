# Frontend Quick Start

Get the full system running and drive it from the Gatsby frontend. By the end
you will have Drupal, the search sidecar, and the Gatsby dev server up, and you
will create a character and an AI-generated story without ever logging into
Drupal.

For how the pieces fit together, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 1. Prerequisites

| Tool | Why |
| ---- | --- |
| [DDEV](https://ddev.readthedocs.io/) | Runs Drupal + Milvus + Solr in containers |
| Node.js 18+ and npm | Gatsby frontend |
| Python 3.8+ | Sidecar (search, spotlight, TTS, portraits) |
| [mkcert](https://github.com/FiloSottile/mkcert) | Local TLS cert DDEV uses for `*.ddev.site` |
| An OpenAI-compatible LLM endpoint | Chat, story generation, arc analysis (`AI_CREATIVE_BASE_URL` + key). A hosted service works; the default is [Ollama](https://ollama.com/) **on the host** — never inside DDEV, where heavy models double-load and crash the box. Image-to-prompt vision and pre-ComfyUI model unloading additionally use Ollama's native API |

Install Python deps once:

```bash
pip install -r requirements.txt
```

### Optional, per feature

| Tool | Enables | Without it |
| ---- | ------- | ---------- |
| Piper voices (`.onnx` files in `game_data/piper/voices/`) | Multi-voice story narration and character consultation audio. The `piper-tts` package itself comes from `requirements.txt` | `/tts/speak` returns 503 and the Narrate control reports it |
| `sox` (system package) | Pitch offsets per character voice — Piper has no pitch control of its own | Voices still play, at their natural pitch |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) at `COMFYUI_DIR`, own venv, plus a Stable Diffusion checkpoint (SD 1.5-class on CPU) | Portrait generation. `start.sh` launches it when `COMFYUI_ENABLED=true` | Portrait jobs fail with the reason; nothing else is affected |

Both host AI services sit behind sidecar endpoints (`/tts/speak`,
`/character/portrait`), so swapping engines is a new client behind the same
endpoint — the frontend, Drupal, and the job queue never name the engine. The
clients themselves are engine-specific (`PiperTTSClient` shells out to the
`piper` binary; `ComfyUIClient` speaks ComfyUI's workflow API), so there is no
drop-in provider switch today.

---

## 2. Configure environment

Two env files, root first.

```bash
# Project root — shared service credentials
cp .env.example .env
```

Fill in at least:

- `DRUPAL_BASE_URL` and
  `DRUPAL_GRAPHQL_TOKEN` if your endpoint needs auth.
- `AI_CREATIVE_BASE_URL` and `AI_CREATIVE_MODEL` — the Ollama-compatible
  endpoint and model used for story generation.
- `OLLAMA_API_KEY` (Ollama accepts any non-empty value).
- `RAG_WIKI_BASE_URL` / `RAG_RULES_BASE_URL` if you use RAG.

```bash
# Frontend — browser/site settings
cp frontend/.env.example frontend/.env.development
```

Fill in `SITE_URL`, `SITE_TITLE`, and `GATSBY_DRUPAL_BASE_URL`. Use the **HTTP**
Drupal URL here if Node rejects DDEV's self-signed cert. The AI and RAG display
values are bridged automatically from the root `.env`.

> Only `GATSBY_`-prefixed variables reach browser code. See
> [frontend/README.md](../frontend/README.md#environment-variables).

---

## 3. Start everything

The one-command path (brings up Drupal + sidecar + Gatsby, skips the legacy
CLI):

```bash
./start.sh --no-cli
```

This runs `ddev start` (Drupal, Milvus, Solr), launches the sidecar and the AI
job-queue processor in the background, starts the Gatsby dev server, and — when
`COMFYUI_ENABLED=true` — ComfyUI too. Logs go to `.sidecar.log`, `.gatsby.log`,
`.jobqueue.log`, and `.comfyui.log`. Ollama is expected to be already running on
the host.

Or do it manually:

```bash
cd drupal-cms && ddev start && cd ..
python3 run_sidecar.py &
cd drupal-cms && ddev drush advancedqueue:queue:process dnd_ai --timeout=0 &
cd ../frontend && npm run develop
```

---

## 4. First-run index

Seed the Milvus vector index so search and semantic retrieval work:

```bash
python3 -m src.cli.dnd_consultant --reindex
# check status:
python3 -m src.cli.dnd_consultant --milvus-status
```

(These flags run engine utilities only — they do not open the deprecated
interactive CLI menu.)

Then open the app:

- Frontend: <http://localhost:`GATSBY_PORT`>
- GraphQL explorer (stitched schema): <http://localhost:`GATSBY_PORT`/___graphql>
- Sidecar health: <http://localhost:`SIDECAR_PORT/health`>

---

## 5. Do everything from the frontend

Each task maps to a page and the serverless function or service behind it.

| Task | Where in the UI | Backed by |
| ---- | --------------- | --------- |
| Browse characters / NPCs | Characters, NPCs pages | Drupal GraphQL |
| View a character sheet | character detail | Drupal GraphQL |
| Edit a character's optional fields | character edit screen | `api/update-character.ts` |
| Create a campaign | Party page | `api/campaigns.ts` |
| Add a character to a campaign | Party page | `api/campaign-party.ts` |
| AI-generate a story | story forge | `api/generate-story.ts` (streams) |
| Save a finished story | story forge | `api/create-story.ts` |
| Read stories | Stories, Campaign Reader | Drupal GraphQL |
| Items / monsters / spells | Items, Monsters pages | Drupal GraphQL |
| Search | Search page | sidecar `/search/parse-query` + Milvus |
| Audit NPC profile completeness | NPC validator screen | Drupal GraphQL + engine |

**Try it:** open the story forge, pick a campaign and party, enter beats, and
generate — text streams in live from the LLM. Save it, and it is written to
Drupal via `createStory`; the new story appears on the Stories page after
Gatsby's 30-second refetch (or restart the dev server).

---

## 6. Troubleshooting

| Symptom | Fix |
| ------- | --- |
| Gatsby cannot reach Drupal / TLS error | Use the HTTP `GATSBY_DRUPAL_BASE_URL`, or trust DDEV's mkcert CA (`NODE_EXTRA_CA_CERTS=$HOME/.local/share/mkcert/rootCA.pem`). `start.sh` does this for you. |
| Stale schema / weird build errors | `cd frontend && npm run clean`, then `npm run develop`. |
| Schema missing a new field/type | Re-run `ddev drush config:import -y && ddev drush cache:rebuild`, then `npm run clean`. |
| Story generation returns no content | Confirm `AI_CREATIVE_MODEL` is pulled into the host Ollama and that `AI_CREATIVE_BASE_URL` points at it. |
| A queued job never leaves `queued` | The processor is not running: check `.jobqueue.log`, or start it with `ddev drush advancedqueue:queue:process dnd_ai --timeout=0`. |
| Portrait job fails immediately | ComfyUI is not up, or `COMFYUI_ENABLED` is unset; the job message says which. |
| Search returns nothing | Re-run `--reindex`; confirm the sidecar is up at `:$SIDECAR_PORT/health`. |
| Inspect background services | `tail -f .gatsby.log` / `tail -f .sidecar.log`. |

---

## See also

- [frontend/README.md](../frontend/README.md) — frontend layout and functions.
- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — the three tiers and data flow.
- [docs/DRUPAL.md](DRUPAL.md) — content model and GraphQL exposure.
