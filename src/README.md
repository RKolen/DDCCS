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
|   |-- staging.py            # Named settings and moods an operator can pick
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
|   |-- dependency_declarations.py  # Every import must be in requirements.txt
|   |-- gate.py                # Shared scan/report/exit plumbing for gates
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
|   |-- comfyui_admin.py       # Restart a local ComfyUI, freeing RAM
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

### The scene prompt is budgeted, not truncated

`build_scene_prompt` composes the scene first - action, setting, mood,
framing, style - and gives the cast whatever characters are left, sharing them
out and dropping whoever no longer fits. It used to join everything and clip
the tail, which meant the cast silently ate the scene: six people at a hundred
characters each came to 604 against a 480 budget, so the setting, the mood,
the framing and the style were all cut off the end and the sixth person
stopped mid-word. That render came back as one character in a forest, with no
port, no night and no group.

Person tags are cut with `clip_tags`, which keeps whole tags. Cutting on a
word boundary left `"piercing green eyes,, teal"` in the prompt, and the model
put the tiefling's colour on the elf.

The budget is why a cast above two belongs in region mode: one 480-character
prompt cannot describe six people *and* the place they are in, whereas each
region gets its own `PROMPT_BUDGET_CHARS` to itself.

### The skeleton is what ControlNet obeys

Facing words in the prompt are not enough. An openpose figure drawn with both
ears, both eyes and full-width shoulders **is** a front view, and
`"side profile view, faces in profile"` lost to it in every render - the terms
reached the prompt correctly and the picture came back facing the camera
anyway. Measured before the fix: every pose drew shoulders at 46% of the box
with two ears and two eyes, whatever the caption said.

`turn_layout` rotates the skeleton instead. The body foreshortens
horizontally by `cos(turn)`, floored so a profile stays a drawable figure
rather than collapsing to a line, and the head keypoints are carried round the
skull on their own bearings - nose 0, eyes +/-30, ears +/-90 - so anything
that ends up on the far side is simply not drawn. A profile then has one eye
and one ear with the nose leading; from behind there is no face at all, and
the shoulders open back to full width **mirrored** - someone's right arm is on
the viewer's right once you are behind them, and openpose reads limb identity
from colour, so an unmirrored back view says "facing forward, arms crossed
over".

`_figure_pose` also honours the operator's chosen stance. `pose_for_index`
exists so a cast is not six identical statues; it was overriding the staging
rather than standing in for it.

### A stride is fore-aft, so a flat layout cannot hold one

`STANDING` and `POSE_VARIANTS` are `(dx, dy)`: what the camera sees head-on.
A step has no width to see from there, so `walking` faked one by splaying the
legs sideways. That reads from the front and nowhere else - the splay is
lateral, so turning the figure squeezed it away exactly when a real stride
would be widest, and a cast staged in profile came back standing to attention.

`POSE_DEPTH` gives the joints that move fore and aft a third coordinate,
positive toward the way the figure faces, and `turn_layout` trades one for the
other: `x = dx*cos(turn) + dz*sin(turn)`. At a front view nothing changes; at
a profile the lateral part is gone and the stride is all there is. A joint
carrying a `dz` skips the foreshortening floor, because it has real width when
turned and does not need the crutch - holding 45% of a splay against the
stride was what cancelled it out.

The magnitudes are deliberately larger than a real step, and the skeleton is
the wrong thing to judge them by. Half these values looked like a natural
walk drawn as a stick figure and rendered as a figure standing still: the
ControlNet was weighing a 14%-of-height stride against its own prior that a
lone character stands to attention, and the prior won at every strength up to
1.6. Doubled, the same prompt and seed walk at the configured 0.85.

Measured on a 480px figure: a walk strides 10% of its height at a front view,
26% at three-quarter and 29% in profile, against 6% for a standing figure in
profile. A control image is not a drawing; it is an instruction, and it has to
out-argue the checkpoint.

### Who is in front is not the same as who is nearest

`place` pastes cutouts in sequence, so the last one in wins every overlap.
That order was cast order, which meant whoever happened to be ticked last was
painted on top - a character staged at the back could be pasted over one at
the front, at a fraction of their height.

Depth is the obvious fix and is not enough on its own. Depth also sets
apparent size, and apparent size is not distance here: `SPECIES_HEIGHT` makes
a halfling 0.62 of a human, so a halfling at the front of the scene is still
smaller than an orc at the back. Pushing the small character forward until
they stop being swallowed therefore ruins everyone else's distance.
`Placement.order` is the separate control that problem needs - 1 is painted
last - and `paint_order` lets it outrank depth, falling back to depth for
anyone the operator did not number.

### Which way round is not the same as how far round

`Placement.facing` says how far a figure is turned. `Placement.toward` says
whether that is to the left or the right, and without it a cast all set to
side profile faced the same way - a group and the person walking up to meet
them included. `TOWARD_SIGN` flips the turn angle, so left is the mirror of
right; `front` and `behind` are unaffected, because a 180-degree turn has no
handedness and the console hides the control for them. Empty means
`DEFAULT_TOWARD`, so existing staging keeps the direction it already had.

### Facing is per character, not per scene

The Camera control says where the lens is. **Which way each person is turned
is a property of that person**, and it lives on their `Placement.facing`.

One angle for the whole cast cannot express "the group walks away while
someone follows them": every figure would be told to turn the same way, and
`ANGLE_NEGATIVES` would ban the backs of the ones who should be walking off.
Worse, the live composite path (`paint_figures`, `composite=True`) passed **no
angle at all** - the comment said the skeleton would set the orientation, but
a 2D openpose skeleton cannot say "facing away". So each figure was rendered
alone against grey with nothing telling it which way to stand, and a figure
alone on grey faces the camera. That is why a six-person scene came back as a
row of people looking at the lens.

`facing` is opt-in: empty adds nothing and keeps the old behaviour, so no
existing render is restaged. When set, that figure gets its own `ANGLES` terms
*and* its own `ANGLE_NEGATIVES`, because the ban on "back turned" that
protects a front view would otherwise forbid the figure asked to turn away.

### Restarting ComfyUI between renders (`src/ai/comfyui_admin.py`)

ComfyUI does not give system RAM back. `POST /free` unloads models from the
GPU, but the process keeps the arena it grew loading them, so on a small box
the second scene render of a session starts with no room and the kernel takes
the process out mid-render. Restarting is the only thing that returns it.

`COMFYUI_RESTART_AFTER_SCENE=true` makes `/story/scene` do that after each
render, synchronously, before the response returns - so the next queued job
finds a clean process rather than a full one. It runs before the
render-failed check on purpose: a render that died part-way through has still
grown the arena, and that is exactly when the next one gets killed.

Two safety properties. "Local" is not guessed from the address - a loopback
URL can still be somebody else's container - it means `COMFYUI_DIR` is set,
because knowing where the install is, is the same thing as being able to
relaunch it. And the process is found by its command line, never by what is
listening on a port; a port says nothing about what you are about to stop.

The mechanics live in `scripts/restart-comfyui.sh`, beside the `start.sh`
that launches ComfyUI in the first place, so the launch recipe has one home.

### Staging (`staging.py`)

The shot analysis writes a setting and a mood as free prose, which is right
until an operator wants the same duel in a castle. `staging.py` is the
vocabulary they pick from, and the console mirrors it in
`frontend/src/utils/storyImage.ts` - `tests/story_images/test_staging.py`
fails if the two lists drift apart.

A `Setting` is six fields rather than one sentence, because CLIP reads a
caption in sequence and the same words composed differently render a
different picture. `backdrop` is the field that earns its keep: something
standing far behind the figures is what gives the empty middle of the frame
somewhere to go, and without one a courtyard reads as a plain. `seat` and
`seat_noun` are the same object said twice - once for the scene, which
paints it, and once for whoever sits on it, whose own caption would
otherwise ask for a stone bench in a forest.

Anything not in the table is used as the place, keeping the default's time
and light and dropping `ground` and `backdrop` - the two clauses most likely
to contradict a location they were not written for.

`ShotPerson.appearance` and `ShotPerson.action` are separate for the same
reason: appearance is who someone is anywhere and comes from Drupal's
`field_image_prompt`; action is what they are doing in this one scene. The
same elf in a tavern should not be holding a drawn blade because their
portrait had one. `action` was called `role` and held exactly this - the
analysis has always been asked for "one line on what they are doing in this
shot" - so both keys are still accepted on the way in.

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
