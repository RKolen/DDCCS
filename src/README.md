# D&D Character Consultant System - Python Engine

This directory contains the **Python engine** — the backend that powers the
whole system. It handles AI, RAG/semantic search, JSON validation, the calendar
and timeline, spotlight scoring, and synchronisation into Drupal. It runs in two
ways:

- As an in-process library imported by the **FastAPI sidecar** (`src/sidecar/`),
  which the [Gatsby frontend](../frontend/README.md) calls for search and
  spotlight.
- As batch/utility commands (indexing, Drupal sync) via `src/cli/`.

For how the engine fits the three-tier architecture (engine, Drupal, frontend),
see [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

> The interactive consultant menu (`python -m src.cli.dnd_consultant`) is the
> **legacy `v1.0.0` path** and is deprecated. The engine has changed enough that
> it likely no longer runs end to end. Utility flags such as `--reindex` and
> `--milvus-status` are still used. New user-facing work lives in the frontend.

## Package Organization

```text
src/
|-- calendar/            # In-world calendar tracking
|   |-- calendar_engine.py   # CalendarEngine, InWorldDate, date arithmetic, season/holiday detection
|   `-- date_tracker.py      # DateTracker: per-campaign current date persisted in timeline.json
|
|-- characters/          # Character management
|   |-- consultants/     # Per-character consultant classes
|   |-- character_sheet.py           # Character and NPC data models
|   |-- character_consistency.py     # Character consistency checking
|   |-- class_plan.py                # Class build plan from the class taxonomy (grants -> choices), with template/RAG fallback
|   `-- npc_constants.py             # NPC ability score constants
|
|-- character_arc/       # AI-powered character arc analysis
|   |-- arc_analyzer.py      # Arc engine + analyze_character_arc (sidecar entry)
|   |-- arc_criteria.py      # Criteria and metrics
|   |-- arc_data.py          # Arc data structures
|   |-- arc_reports.py       # Report generation
|   `-- arc_storage.py       # Arc data persistence
|
|-- relations/          # Story-arc relationship suggestion
|   |-- relation_types.py     # CharacterDigest + RelationSuggestion
|   `-- relation_suggester.py # Per-subject prompting, parsing, and merge
|
|-- story_arcs/         # Story-arc drafting from played sessions
|   |-- arc_draft_types.py    # SessionRecap, ArcDraft/ArcRoster, DiscoveredNpc
|   |-- recap_prompt.py       # The prompt opening both recap passes share
|   |-- arc_drafter.py        # The arc a campaign's sessions add up to
|   `-- npc_extractor.py      # The NPC cast those sessions name
|
|-- story_images/       # Story-scene illustrations (queued, event-scoped)
|   |-- types.py              # StoryEvent, RosterEntry, ShotPerson, ShotAnalysis
|   |-- events.py             # Chunked event extraction (never the whole story)
|   |-- shot.py               # Who is in the picked excerpt
|   |-- scene_prompt.py       # Wide-shot SD prompt (not a portrait prompt)
|   `-- render.py             # 768x512 DreamShaper + 2 IPAdapters + staggered ReActor
|
|-- npcs/               # NPC management
|   |-- npc_agents.py           # NPC AI agents
|   `-- npc_auto_detection.py   # Automatic NPC detection from stories
|
|-- stories/            # Story management
|   |-- story_manager.py                 # Core story management
|   |-- enhanced_story_manager.py        # Advanced story features
|   |-- story_analyzer.py / story_analysis.py  # Story analysis
|   |-- story_file_manager.py            # Story file operations
|   |-- story_ai_generator.py            # AI story generation
|   |-- story_amender.py                 # Story amendment workflow
|   |-- story_updater.py                 # Story file updates
|   |-- story_workflow_orchestrator.py   # Orchestrates story workflows
|   |-- story_consistency_analyzer.py    # Consistency analysis
|   |-- session_results_manager.py       # Session results tracking
|   |-- hooks_and_analysis.py            # Story hooks generation
|   |-- party_manager.py                 # Party state management
|   |-- character_manager.py             # Character management in stories
|   |-- character_loader.py              # Character loading
|   |-- character_load_helper.py         # Character loading helpers
|   |-- character_loading_base.py        # Base character loading
|   |-- character_action_analyzer.py     # Character action analysis
|   |-- character_fit_analyzer.py        # Character fit analysis
|   |-- series_analyzer.py               # Story series analysis
|   |-- equipment_checker.py             # Equipment consistency checks
|   |-- spotlight_types.py               # Spotlight data types (SpotlightEntry, SpotlightReport)
|   |-- spotlight_signals.py             # Spotlight signal collectors (recency, threads, DC, tension)
|   `-- spotlight_engine.py              # Spotlight scoring engine and prompt injection
|
|-- combat/             # Combat system
|   |-- combat_narrator.py      # Combat narration
|   |-- narrator_ai.py          # AI-driven narration
|   |-- narrator_consistency.py # Narrator consistency checking
|   `-- narrator_descriptions.py # Narrator description helpers
|
|-- items/              # Items and inventory
|   `-- item_registry.py        # Custom items registry
|
|-- spells/             # Custom / homebrew spell system
|   |-- spell_registry.py            # Homebrew spell registry
|   |-- spell_import_export.py       # Import/export of custom spells
|   `-- spell_item_integration.py    # Spell <-> magic item integration
|
|-- encounters/         # Encounter scaling
|   `-- encounter_scaler.py     # Encounter difficulty scaling/calculation
|
|-- sessions/           # Session notes
|   |-- session_notes.py         # Session notes data structures
|   `-- session_notes_manager.py # Session notes manager
|
|-- timeline/           # Cross-campaign timeline tracking
|   |-- event_schema.py          # Timeline event schema
|   |-- event_extractor.py       # Extract events from story files
|   |-- timeline_store.py        # Event storage/retrieval
|   |-- timeline_display.py      # Timeline views/export
|   `-- cross_campaign.py        # Cross-campaign event linking
|
|-- dm/                 # Dungeon Master tools
|   |-- dungeon_master.py       # DM consultant
|   `-- history_check_helper.py # History check helper
|
|-- validation/         # Data validation
|   |-- character_validator.py  # Character JSON validation
|   |-- npc_validator.py        # NPC JSON validation
|   |-- items_validator.py      # Items JSON validation
|   |-- party_validator.py      # Party config validation
|   |-- example_world.py        # Keeps live-campaign names out of the codebase
|   |-- css_palette.py          # Keeps colours in tokens.css and nowhere else
|   `-- validate_all.py         # Unified validator
|
|-- ai/                 # AI integration
|   |-- ai_client.py           # AI client interface (includes embed() for vectors)
|   |-- rag_system.py          # RAG (Retrieval Augmented Generation)
|   |-- abilities_rag.py       # Reusable rules resolver: abilities/features, backgrounds, feats, class tools, subclass features (via RAG_RULES_BASE_URL wiki)
|   |-- spells_rag.py          # Spell stat-block resolver from spell:{slug} wiki pages
|   |-- equipment_rag.py       # Equipment + tool item catalogue: descriptions/types + tool proficiency categories (via RAG_RULES_BASE_URL wiki)
|   |-- catalog_rag.py         # Which backgrounds/species/classes exist, each tagged with its sourcebook; filtered by RAG_SOURCEBOOKS
|   |-- wiki_scraping.py       # Shared Wikidot primitives (page content, title, tolerant fetch, ready client) for the rules resolvers
|   |-- availability.py        # AI availability detection
|   |-- lazy_imports.py        # Lazy import helpers
|   |-- milvus_client.py       # Milvus vector DB wrapper (connect/insert/search)
|   |-- milvus_collections.py  # Collection schema definitions (characters/npcs/stories/wiki)
|   |-- embedding_pipeline.py  # Chunking + embedding for all D&D data types
|   |-- semantic_retriever.py  # Semantic RAG via Milvus with keyword fallback
|   |-- index_sync.py          # Incremental sync called after JSON file saves
|   |-- comfyui_client.py      # HTTP client for the local ComfyUI workflow API (portraits)
|   |-- comfyui_workflows.py   # ComfyUI API-JSON workflow builders (txt2img, IPAdapter, scene, ReActor)
|   |-- portrait_prompt.py     # Builds SD positive/negative prompts from a character profile
|   |-- ollama_admin.py        # Best-effort Ollama model unloading (free RAM before SD generation)
|   `-- image_describe.py      # Image->prompt via an Ollama vision model (IMAGE_TO_PROMPT_MODEL)
|
|-- config/             # Centralized configuration
|   |-- config_types.py        # AIConfig, RAGConfig, RulesetConfig, DisplayConfig, PathConfig, DrupalConfig, ComfyUIConfig
|   `-- config_loader.py       # Config loading from file/env
|
|-- integration/        # External service integration
|   |-- drupal_sync.py         # Drupal-backed wiki page cache (GraphQL; backs DrupalWikiCache)
|   `-- drupal_graphql.py      # Drupal GraphQL client: query_drupal (degrades to {}) + mutate_drupal (raises)
|
|-- sidecar/            # FastAPI microservice (search + spotlight) -- see sidecar/README.md
|   |-- app.py                 # FastAPI app (/health, /search/parse-query, /eval/spotlight)
|   |-- models.py              # Pydantic request/response models
|   `-- query_parser.py        # AI query normalisation
|
|-- utils/              # Shared utilities (check AGENTS.md catalog first)
|   |-- file_io.py                  # JSON and file I/O
|   |-- path_utils.py               # Game data path construction
|   |-- string_utils.py             # String processing
|   |-- validation_helpers.py       # Common validation patterns
|   |-- cli_utils.py                # CLI selection menus
|   |-- terminal_display.py         # Rich terminal output
|   |-- character_profile_utils.py  # Character loading helpers
|   |-- dnd_rules.py                # D&D 5e rules constants
|   |-- spell_highlighter.py        # Spell detection/highlighting
|   |-- npc_lookup_helper.py        # NPC lookup helpers
|   |-- story_file_helpers.py       # Story file utilities
|   |-- markdown_utils.py           # Markdown section updates
|   |-- tts_narrator.py             # TTS narration
|   |-- cache_utils.py              # In-memory cache management
|   |-- behaviour_generation.py     # Behavior from personality
|   |-- errors.py                   # Custom exceptions + error handling
|   |-- error_templates.py          # Standardized error messages
|   |-- ascii_art.py                # ASCII art character portraits
|   |-- audio_player.py             # Cross-platform audio playback
|   |-- piper_tts_client.py         # Piper neural TTS client
|   |-- dialogue_detector.py        # Dialogue segmentation for TTS
|   |-- text_formatting_utils.py    # Text wrapping utilities
|   |-- story_formatting_utils.py   # Story section formatting
|   |-- story_parsing_utils.py      # Story content parsing
|   |-- spell_lookup_helper.py      # Spell/ability RAG lookup
|   |-- npc_migration.py            # NPC profile migration
|   |-- optional_imports.py         # Optional dependency helpers
|   `-- display_file.py             # Standalone file viewer
|
`-- cli/                # Command-line interface (legacy menu + live utility flags)
    |-- dnd_consultant.py                  # Main interactive CLI (legacy) + --reindex / --milvus-status flags
    |-- dnd_cli_helpers.py                 # CLI helper functions
    |-- milvus_commands.py                 # --reindex and --milvus-status handlers
    |-- cli_story_manager.py               # Story management CLI
    |-- cli_character_manager.py           # Character management CLI
    |-- cli_character_development_manager.py  # Character development CLI
    |-- cli_consultations.py               # Consultation handlers
    |-- cli_session_manager.py             # Session management CLI
    |-- cli_story_analysis.py              # Story analysis CLI
    |-- cli_story_helpers.py               # Story CLI helpers
    |-- cli_story_config_helper.py         # Story config helpers
    |-- cli_story_reader.py                # Story reader CLI
    |-- cli_series_analysis.py             # Series analysis CLI
    |-- cli_config.py                      # CLI configuration
    |-- base_story_interaction_manager.py  # Base story interaction
    |-- story_amender_cli_handler.py       # Story amender CLI
    |-- party_config_manager.py            # Party configuration
    `-- setup.py                           # Workspace initialization
```

## Image->prompt (`src/ai/image_describe.py`)

Turns an existing portrait into a positive prompt via a local Ollama vision
model. Three constraints are load-bearing, all found the hard way:

**Do not extend `_INSTRUCTION` without testing it against a real image.**
Qwen2.5-VL under Ollama dies on certain prompt texts with
`GGML_ASSERT(a->ne[2] * 4 == b->ne[0]) failed` — a shape assert in the vision
patch merger, i.e. the model runner crashing, not a poor answer. It is
deterministic per phrasing and independent of the image: the current two
sentences succeed every time, while the same text plus one more sentence about
garments or colours fails every time, on images from 512x768 to 1024x1536.
Ollama returns this as HTTP 500 with an `error` key, which is why the body is
read before the status is checked — swallowing it surfaces in the console as
"the vision model returned no description" and sends you hunting through prompt
wording instead.

**Keep the prompt inside one encoder window.** Stable Diffusion reads 77 tokens
at a time and adherence decays across windows, so a 250-token prose description
does not fail loudly — the leading concepts dominate and the rest dilutes to
noise. A gold dragonborn described in 154 words of prose about faces, hair, and
elegant robes rendered as a human woman; the same checkpoint (DreamShaper 8)
renders a correct dragonborn from `Green dragonborn, stoic, armored,
protective`. Hence `_MAX_TAGS`, and the species from the character's own record
placed first, where it cannot be diluted or hallucinated away.

**Spend the tags on the character, not the room.** A faithful description of a
portrait includes its setting, and those tags compete: prompts carrying
`grand hall, chandeliers, audience watching` produced a picture of an archway
with a tiny figure in it. `_SCENE_WORDS` drops them, and `_NON_VISUAL_TAGS`
drops impressions (`majestic presence`) that cost tokens and change nothing.

## Likeness across regenerations (`src/ai/comfyui_workflows.py`)

Image->prompt is how a portrait is *described*; it is not how a character keeps
their face. Describing a picture and re-rendering the description is lossy in
both directions — the tags drop what they cannot name, and the checkpoint fills
the gaps from its own priors — so a chain of prompt-only regenerations drifts
into a different person. Chained img2img is no better: colour and contrast shift
on every pass.

`ipadapter_workflow()` is the answer to that. It conditions the model on the
reference portrait's own CLIP-vision embedding instead of on words about it, so
identity survives regeneration while the prompt still moves pose, clothing, and
mood. The graph is `txt2img_workflow()` with the identity chain
(`IPAdapterModelLoader` + `CLIPVisionLoader` + `LoadImage` ->
`IPAdapterAdvanced`) spliced between the checkpoint and the sampler; the
sampler's `model` input is rewired onto the patched model. **That rewire is the
whole thing** — leave it out and the chain is built, ignored, and the render
comes back as a plain txt2img with nothing to indicate anything went wrong.

Three requirements, all checked before this path is taken (see
`_identity_reference` in `sidecar/app.py`):

- the **ComfyUI-IPAdapter-plus** custom nodes are installed (a missing node type
  fails the whole queued prompt, not just the chain);
- `COMFYUI_IPADAPTER_MODEL` and `COMFYUI_CLIP_VISION` both name files present in
  ComfyUI's `models/ipadapter/` and `models/clip_vision/`. They are configured
  rather than derived because the pair must match the checkpoint family — an
  SD 1.5 IPAdapter on an SDXL checkpoint produces nothing useful;
- the reference image can be fetched and uploaded to ComfyUI.

Any of those missing degrades to text-to-image with a logged reason rather than
failing the render, and the response's `used_reference` says which one actually
ran. `weight` (default 0.8) trades prompt freedom against likeness: above ~0.9
the prompt stops mattering and every render is the reference again; below ~0.5
the likeness washes out.

**Configure a general IPAdapter, never a `-face` variant.** Face adapters encode
*human facial identity*; a non-human character's head is outside that
distribution, so the adapter maps it to the nearest human face and rebuilds
that. It fails in the most misleading way possible: costume, palette, and
setting transfer perfectly, so the render looks like it worked while the species
has been silently replaced. A gold dragonborn reference at `weight: 1` on
`ip-adapter-plus-face_sd15` produced a human woman *with `human` in the negative
prompt*; the same prompt, seed, and reference on `ip-adapter-plus_sd15` at
`weight: 0.7` produced the dragonborn. Raising the weight makes a face adapter
worse, not better - weight is how hard the human reconstruction is imposed. And
no negative prompt fixes it: a negative removes a concept, it cannot supply the
one the model is missing.

## Story scenes (`src/story_images/`)

Portraits are one face. A story illustration is a **shot**: whoever the picked
event puts in frame, not the whole campaign roster in one graph. `scene_workflow()`
renders 768x512 DreamShaper with at most two chained IPAdapters (the leads).
Remaining likenesses go through `reactor_swap_workflow()` one face at a time,
with ComfyUI `/free` between steps. ReActor is optional (`COMFYUI_REACTOR_*`);
without it the job still ships and reports `used_ipadapter` / `swapped_faces`
honestly. Do not load Flux, SDXL, or extra FaceID graphs on this CPU box.

Scene likeness uses `COMFYUI_SCENE_IPADAPTER_MODEL`, a **face** adapter, and
never the full-image `COMFYUI_IPADAPTER_MODEL` the portraits use: a full-image
adapter transfers the reference's framing, background and companions, so a
scene request comes back as a redrawn portrait. Unset means the scene renders
from its prompt alone.

`framing.py` carries the shot type and camera angle. Without them every
render came back a wide shot of backs walking away, and a face swap on a face
nobody can see costs CPU minutes and changes zero pixels - so `render.py` now
also drops a swap that returned its input untouched rather than reporting a
likeness that did not happen. Per-character direction is not a prompt change:
SD 1.5 will not bind an attribute to one named subject among six, so that
needs regional conditioning (ControlNet pose).

`appearance.py` captions a portrait into visual tags when the character record
carries no appearance text of its own. Lineage and class alone ("human wizard")
drop every detail nobody wrote down - spectacles, a scar, a particular hat -
and those are exactly the details that make a face recognisable. The stored
`field_image_prompt` always wins; captioning is only the fallback, and runs one
vision call per in-frame person who needs it.

## Running the System

### Search/spotlight sidecar (used by the frontend)

```bash
python3 run_sidecar.py
```

See [sidecar/README.md](sidecar/README.md).

### Index and Drupal utilities

```bash
python -m src.cli.dnd_consultant --reindex         # build/refresh the Milvus index
python -m src.cli.dnd_consultant --milvus-status   # report index status
```

### Legacy interactive CLI (deprecated)

```bash
python -m src.cli.dnd_consultant   # legacy menu; may not run end to end
```

### Validation

```bash
# Validate all game data
python -m src.validation.validate_all

# Validate specific types
python -m src.validation.character_validator
python -m src.validation.npc_validator
python -m src.validation.items_validator
python -m src.validation.party_validator
```

### Setup Workspace

```bash
python -m src.cli.setup
```

## Import Conventions

All imports use absolute paths from the `src` package:

```python
from src.characters.consultants.character_consultants import CharacterProfile
from src.stories.story_manager import StoryManager
from src.validation.validate_all import validate_all_game_data
from src.utils.text_formatting_utils import wrap_narrative_text
```
