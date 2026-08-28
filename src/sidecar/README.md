# Sidecar — Search & Spotlight Service

A small FastAPI microservice that imports the Python engine in-process and
exposes a couple of HTTP endpoints the
[Gatsby frontend](../../frontend/README.md) calls. It exists so the frontend can
use engine logic (query normalisation, spotlight scoring) without bundling
Python into the browser.

See [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) for where the sidecar
sits in the three-tier system.

---

## Run it

```bash
python3 run_sidecar.py        # from the project root
```

Host, port, log level, and reload come from config (`src/config/`) /
environment — `SIDECAR_HOST` and `SIDECAR_PORT`. `start.sh` launches it in the
background (logs to `.sidecar.log`).

`SIDECAR_BIND_HOST` (a launch knob read in `run_sidecar.py`, like
`SIDECAR_WORKERS`) overrides the interface uvicorn listens on without changing
the address clients dial. Bind every interface so the DDEV web container can
reach the sidecar over its host gateway for queued AI jobs; set
`SIDECAR_SECRET` alongside it, since the service is then reachable beyond
loopback (every route except `/health` then requires `X-Sidecar-Secret`).

---

## Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/health` | Readiness probe (no auth) |
| POST | `/search/parse-query` | Normalise a natural-language search query for the Milvus index |
| POST | `/eval/spotlight` | Compute spotlight scores for a campaign's characters |
| POST | `/character/build-from-template` | Derive a full character sheet (HP, proficiency, saves, class features, spell slots) from class + level + ability scores |
| POST | `/character/resolve-background` | Resolve a background's granted data (ability options, origin feat, skills, fixed tools, gold, equipment) from the rules wiki (`RAG_RULES_BASE_URL`). A "choose one kind of Musical Instrument / Gaming Set / Artisan's Tools" proficiency is returned as a `tool_choices` group (category sublist), not a literal tool |
| POST | `/character/skill-plan` | Derive the class + species/subspecies plan for the skills step: granted skills/tools + skill/tool choice groups, **granted languages** (Common, plus any class feature named after a language such as Druidic / Thieves' Cant) + a language choice (2), the class **equipment** A/B choices (items vs gold), and the **subclass** choice (level + options). The class portion comes from the `class` taxonomy (`class_grant` paragraphs) and falls back to the JSON template + rules wiki; `source` reports which was used |
| POST | `/character/equipment/describe` | Resolve prose descriptions and item types (weapon/armor/item) for equipment names from the rules-wiki (`RAG_RULES_BASE_URL`) equipment catalogue, so created item nodes get an accurate description and type |
| POST | `/character/arc/story` | Analyse a single story into one arc data point (one model call). The frontend loops this once per story so no request runs long enough to trip the fetch timeout |
| POST | `/character/arc/aggregate` | Aggregate the per-story data points into the full arc (direction, stage, summary, metric series, relationships, goals) via `aggregate_arc` over the distilled per-story summaries |
| POST | `/character/arc/synthesize` | Synthesize an arc summary, relationships, and goals from the per-story analysis **texts already stored** on the `character_analysis` node (not raw stories), on the creative model profile. This backs crash-safe resume: a re-run skips stories already persisted and this reads their stored prose instead of holding every story in memory |
| POST | `/character/arc` | Single-shot arc analysis (all stories then aggregate) via `analyze_character_arc` on the `fast` model profile; `disable_thinking` keeps qwen3 from leaving the JSON content empty. Prefer the two-step `/story` + `/aggregate` path for many stories |
| POST | `/relations/suggest` | Suggest one subject's story-arc relationships (one model call). Needs an **instruct** model (`RELATIONS_PROFILE`, default `creative`): a local "thinking" model spends its whole budget reasoning and returns empty content |
| POST | `/relations/merge` | Merge the per-subject batches into one set, collapsing reciprocal pairs (A->B and B->A are one bond); stronger tier wins, then the longer note |
| POST | `/character/portrait` | Generate a character portrait with local **ComfyUI** (Stable Diffusion) from the character profile, returning a base64 PNG plus the seed, prompt, and `alt` text. Disabled unless `COMFYUI_ENABLED=true`; returns 503 when disabled, unconfigured (`COMFYUI_CHECKPOINT`), or unreachable, and 500 when generation fails. Optional `seed` reproduces a render; optional `width`/`height` suit an SD 1.5-class checkpoint (the defaults are SDXL-sized). Optional `reference_image_url` (+ `identity_weight`, 0-1.5, default 0.8) conditions the render on an existing portrait via IPAdapter so it stays recognisably the same character - requires the ComfyUI-IPAdapter-plus nodes plus `COMFYUI_IPADAPTER_MODEL` and `COMFYUI_CLIP_VISION`, and degrades to text-to-image (never an error) when any of that is missing or the reference cannot be fetched; the response's `used_reference` reports which path ran. ComfyUI models are unloaded (`/free`) after every run because this box is CPU-only and a resident checkpoint is the top OOM risk |
| POST | `/tts/speak` | Synthesise text to speech with a Piper voice + speed, returning `audio/wav` (used by the character consultation's speak button and story narration clips; requires the `piper-tts` package). An optional `pitch` (semitones) is applied as a post-process with `sox` (Piper has no pitch control); pitch is skipped when `sox` is not on `PATH` |
| POST | `/tts/segment` | Split story text into multi-voice TTS segments (dialogue detector + character voice map). Returns ordered `{ text, speaker, voice_id, speed, pitch }` clips for the frontend to synthesise sequentially via `/tts/speak`. Narrator clips use British `en_GB-alan-medium` at speed `0.88` / pitch `0` (see `get_narrator_*` in `src/utils/piper_tts_client.py`). Does not run Piper itself |

Request/response shapes are defined as Pydantic models in
[models.py](models.py). Query normalisation logic is in
[query_parser.py](query_parser.py); spotlight scoring delegates to
`src.stories.spotlight_engine.SpotlightEngine`. The character build endpoint
reuses `src.characters.character_template.build_character_data_from_template`
and resolves class, species, and subspecies abilities (name, rules text, level,
source type) via the reusable `src.ai.abilities_rag` service, which scrapes the
rules wiki at `RAG_RULES_BASE_URL`.

### Authentication

If `SIDECAR_SECRET` is set, every request except `/health` must send a matching
`X-Sidecar-Secret` header. When `SIDECAR_SECRET` is unset, all requests are
allowed (local dev default).

---

## Consumers

- `frontend/src/pages/search.tsx` — search, via `/search/parse-query`.
- `frontend/src/api/spotlight.ts` — spotlight scoring, via the sidecar.
- `frontend/src/api/create-character.ts` — character creation wizard, via
  `/character/build-from-template`.
- `frontend/src/api/tts.ts` — single-clip Piper synthesis, via `/tts/speak`.
- `frontend/src/api/tts-segment.ts` — multi-voice story segmentation, via
  `/tts/segment` (used by `templates/story.tsx` Narrate).

---

## Files

| File | Purpose |
| ---- | ------- |
| `app.py` | FastAPI app, middleware, routers |
| `tts_routes.py` | Piper `/tts/speak` and `/tts/segment` routes |
| `models.py` | Pydantic request/response models |
| `query_parser.py` | AI query normalisation |

The runner lives at the project root: `run_sidecar.py`.
