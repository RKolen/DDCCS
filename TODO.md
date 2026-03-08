# TODO List - D&D Character Consultant System

Last Updated: February 13, 2026

## Implementation Roadmap

### Phase 1: Foundation

- [ ] **Multi-voice TTS (Phase 1-2)** - Voice selection in character/NPC JSON schema, dialogue detection parser **Plan:** [plans/multi_voice_tts_design.md](plans/multi_voice_tts_design.md)

### Phase 2: Infrastructure

- [ ] **Drupal CMS Integration** - DDEV setup, JSON to Drupal migration, Python-to-Drupal API sync **Plan:** [plans/drupal_cms_integration.md](plans/drupal_cms_integration.md)
- [ ] **TTS Web Integration** - Pre-generated audio storage, audio sync to Drupal, React audio player components **Plan:** [plans/tts_web_integration.md](plans/tts_web_integration.md)
- [ ] **Multi-voice TTS (Phase 3-4)** - Voice switching implementation, Piper TTS integration

### Phase 3: Character System

- [ ] **Multi-class Support** - Enhance character profiles to support multiclassing **Plan:** [plans/multiclass_support_plan.md](plans/multiclass_support_plan.md)
- [ ] **Character Names Split** - Split names into first and last names for characters and NPCs **Plan:** [plans/character_names_plan.md](plans/character_names_plan.md)
- [ ] **Relationship Mapping** - Visual or structured relationship tracking between characters **Plan:** [plans/relationship_mapping_plan.md](plans/relationship_mapping_plan.md)

### Phase 4: Story Tools

- [ ] **AI Story Suggestions** - Use AI to suggest story developments and narrative improvements **Plan:** [plans/ai_story_suggestions_plan.md](plans/ai_story_suggestions_plan.md)
- [ ] **Session Notes Integration** - Better integration between session results and story narrative **Plan:** [plans/session_notes_plan.md](plans/session_notes_plan.md)
- [ ] **Timeline Tracking** - Track chronological order of events across campaigns **Plan:** [plans/timeline_tracking_plan.md](plans/timeline_tracking_plan.md)

### Phase 5: Quality of Life

- [ ] **CLI Enhancements** - Tab completion, command history, batch operations **Plan:** [plans/cli_enhancements_plan.md](plans/cli_enhancements_plan.md)
- [ ] **Export Functionality** - Export stories to different formats (PDF, HTML, etc.) **Plan:** [plans/export_functionality_plan.md](plans/export_functionality_plan.md)
- [ ] **Backup System** - Automated backup of character profiles and party configurations **Plan:** [plans/backup_system_plan.md](plans/backup_system_plan.md)

## Planned Features (Design Complete)

All features below have detailed implementation plans in the `plans/` directory.

### AI and Story Tools

- [AI Story Suggestions](plans/ai_story_suggestions_plan.md) - AI-powered story development suggestions
- [Session Notes Integration](plans/session_notes_plan.md) - Better session results and story narrative integration
- [Timeline Tracking](plans/timeline_tracking_plan.md) - Chronological event tracking across campaigns
- [Character Arc Analysis](plans/character_arc_analysis_plan.md) - Tools to analyze character development over multiple stories

### Character System

- [Multi-class Support](plans/multiclass_support_plan.md) - Character profiles with multiclassing support
- [Character Names Split](plans/character_names_plan.md) - First and last name separation
- [Relationship Mapping](plans/relationship_mapping_plan.md) - Character relationship tracking

### Infrastructure

- [Drupal CMS Integration](plans/drupal_cms_integration.md) - Full Drupal CMS integration
- [TTS Web Integration](plans/tts_web_integration.md) - Web-based TTS audio integration
- [Multi-voice TTS Design](plans/multi_voice_tts_design.md) - Multi-voice narration system
- [SQLite Integration](plans/sqlite_integration_plan.md) - Optional database support for tracking and analytics

### Quality of Life

- [CLI Enhancements](plans/cli_enhancements_plan.md) - Tab completion, command history, batch operations
- [Export Functionality](plans/export_functionality_plan.md) - Export to PDF, HTML, and other formats
- [Backup System](plans/backup_system_plan.md) - Automated backup system
- [Interactive Setup](plans/interactive_setup_plan.md) - More interactive setup for first-time users

### Technical Improvements

- [Error Handling Plan](plans/error_handling_plan.md) - Improved error messages and user guidance
- [Configuration System](plans/configuration_system_plan.md) - Centralized configuration management
- [DC Scaling](plans/dc_scaling_plan.md) - Optional level-based DC scaling recommendations
- [Custom Spell Highlighting](plans/custom_spell_highlighting_plan.md) - Support for homebrew/custom spells

### Campaign Management

- [Campaign Templates](plans/campaign_templates_plan.md) - Templates for common campaign types
- [Party Alterations](plans/party_alterations_plan.md) - Move current party to campaign files
- [Calendar Tracking](plans/calendar_tracking_plan.md) - In-world calendar and timeline tracking
- [Plugin Architecture](plans/plugin_architecture_plan.md) - Custom modules/plugins support

## High Priority (No Plan Yet)

### User Experience

- [ ] **Pronouns** - Add pronouns to character files - [Plan](plans/pronouns_field_plan.md)

## Medium Priority (No Plan Yet)

### Character System Improvements

- [ ] **Character templates** - Create additional class-specific templates beyond the basic example - [Plan](plans/character_templates_plan.md)
- [ ] **Profile Verification** - Check if JSON templates need to be updated for profile updates and consistency usage - [Plan](plans/profile_verification_plan.md)

### Story Tools

- [ ] **Language fixes** - Filter language to only include the prompts language - [Plan](plans/language_fixes_plan.md)
- [ ] **Story tools** - Additional story management tools - [Plan](plans/story_tools_plan.md)

### NPC System

- [ ] **Major NPC template (BBEG)** - Template for major NPCs and villains - [Plan](plans/major_npc_template_plan.md)

## Low Priority (No Plan Yet)

### Story Tools

- [ ] **Combat narrative templates** - Pre-built templates for different combat scenarios

### User Experience

- [ ] **Quick start guide** - Create a step-by-step tutorial for new users - [Plan](plans/quick_start_guide_plan.md)
- [Coqui TTS Integration](plans/multi_voice_tts_design.md#15-alternative-tts-engine-coqui-ai-tts) - Add Coqui AI as alternative TTS engine for higher voice quality (low priority - requires powerful CPU or NVIDIA GPU)

## Known Issues to Fix

### Bug Fixes

- [ ] **File path handling** - Ensure cross-platform compatibility for file paths
- [ ] **Git integration** - Test git functionality with different repository structures

### Quality of Life

- [ ] **Startup time optimization** - [Plan](plans/startup_optimization_plan.md)

## Documentation TODOs

### README Updates

- [ ] **Add troubleshooting section** for common issues

### New Documentation

- [ ] **API documentation** - For developers who want to extend the system
- [ ] **Character creation guide** - Detailed guide for creating rich character profiles
- [ ] **Campaign management best practices** - Tips for organizing complex campaigns
- [ ] **Integration guide** - How to integrate with external tools

## Recently Completed

### Error Handling Improvements - March 7, 2026

- [x] **Configuration System** - Centralized config file for system settings
- [x] **Error Handling Improvements** - Improve error messages throughout the system for better user guidance

### Narration and ASCII Art - December 30, 2025

- [x] **ASCII Character Art** - Create ASCII images for characters
- [x] **Voice Narration** - Make it possible to narrate the story files

### Story Amender Enhancement - December 18, 2025

- [x] **Story amender functionality** - Complete dynamic character reassignment system
  - [x] Refactored `character_fit_analyzer.py` to use dynamic ability extraction (class_abilities, specialized_abilities, known_spells, feats)
  - [x] Created `story_amender.py` orchestrator for amendment workflow (identify actions, analyze fits, generate amendments, apply to files)
  - [x] Extended `character_profile.py` with `get_all_abilities()` method for comprehensive ability listing
  - [x] Updated `character_manager.py` to extract and track all abilities (not just spells)
  - [x] Integrated CLI amendment workflow in `cli_story_manager.py` with `StoryAmenderCLIHandler`
  - [x] Added comprehensive unit tests for character fit analysis and story amendment

### Performance Optimization - December 6, 2025

- [x] **Lazy character loading** - Deferred character loading from startup to on-demand access. Implemented CharacterLoadingMixin base class for code reuse. Startup now instant (<0.1s vs 2-5s before). Characters load only when: (1) user selects story/campaign option, (2) user accesses character management, or (3) explicit ensure_characters_loaded() call. Party-based loading available for selective character access. Further optimization opportunities: [Plan](plans/startup_optimization_plan.md)

### Readability December 6, 2025

- [x] **Story Readability** - Make story readable from terminal
- [x] **Update Readmes** - Update Readmes with new structure and use the example characters in examples.
- [x] **Remove outdated references** to Story_Series_Folders structure
- [x] **Update workflow examples** with real use cases

### Manual Testing November 8, 2025

- [x] - The code recently undergone many code refactors and while tests are added for everything we need to check if the consultant still does what we want.

### Comprehensive Testing October 26, 2025

- [x] **Step 8: Validators Tests** - COMPLETE
  - [x] test_character_validator.py
  - [x] test_npc_validator.py
  - [x] test_party_validator.py
  - [x] test_items_validator.py
  - [x] test_all_validators.py
  - [x] tests/validation/README.md

**Next Steps (Priority Order):**

- [x] **Step 1: AI Integration Tests** COMPLETE
  - [x] Fix test_ai_env_config.py
  - [x] Create test_ai_client.py
  - [x] Create test_rag_system.py
  - [x] Create test_all_ai.py
  - [x] Create test_behavior_generation_ai_mock.py
  - [x] Create test_availability.py
  - [x] Create tests/ai/README.md

- [x] **Step 2: Character System Tests** COMPLETE
  - [x] test_character_profile.py
  - [x] test_consultant_core.py
  - [x] test_consultant_dc.py
  - [x] test_consultant_story.py
  - [x] test_consultant_ai.py
  - [x] test_class_knowledge.py
  - [x] test_character_sheet.py
  - [x] test_character_consistency.py
  - [x] test_all_characters.py
  - [x] tests/characters/README.md

- [x] **Step 3: NPC System Tests** COMPLETE
  - [x] test_npc_agents.py
  - [x] test_npc_auto_detection.py
  - [x] test_all_npcs.py
  - [x] tests/npcs/README.md

- [x] **Step 4: Story System Tests** COMPLETE
  - [x] test_story_manager.py
  - [x] test_enhanced_story_manager.py
  - [x] test_story_analyzer.py
  - [x] test_story_file_manager.py
  - [x] test_session_results_manager.py
  - [x] test_hooks_and_analysis.py
  - [x] test_party_manager.py
  - [x] test_story_updater.py
  - [x] test_character_manager.py
  - [x] test_character_loader.py
  - [x] test_character_consistency.py
  - [x] test_character_consistency_integration.py
  - [x] test_all_stories.py
  - [x] tests/stories/README.md

- [x] **Step 5: Combat System Tests** COMPLETE
  - [x] test_combat_narrator.py
  - [x] test_narrator_ai.py
  - [x] test_narrator_descriptions.py
  - [x] test_narrator_consistency.py
  - [x] test_all_combat.py
  - [x] tests/combat/README.md

- [x] **Step 6: Items System Tests** COMPLETE
  - [x] test_item_registry.py
  - [x] test_all_items.py
  - [x] test_load_precedence_registry_over_fallback
  - [x] test_load_fallback_only_items_present
  - [x] test_get_item_and_is_custom_api
  - [x] tests/items/README.md

- [x] **Step 7: DM Tools Tests** COMPLETE
  - [x] test_dungeon_master.py
  - [x] test_history_check_helper.py
  - [x] test_suggest_narrative_with_character_insights
  - [x] test_generate_narrative_with_ai_client_and_rag
  - [x] test_check_consistency_relationships
  - [x] test_all_dm.py
  - [x] tests/dm/README.md

- [x] **Step 9: CLI Tests** COMPLETE
  - [x] test_dnd_consultant.py
  - [x] test_setup.py
  - [x] test_cli_character_manager.py
  - [x] test_cli_story_manager.py
  - [x] test_cli_consultations.py
  - [x] test_cli_story_analysis.py
  - [x] test_all_cli.py
  - [x] tests/cli/README.md

- [x] **Step 10: Utils Tests** COMPLETE
  - [x] test_path_utils.py
  - [x] test_behaviour_generation.py
  - [x] test_cli_utils.py
  - [x] test_dnd_rules.py
  - [x] tests_file_io.py
  - [x] test_markdown_utils.py
  - [x] test_spell_highlighter.py
  - [x] test_story_formatting_utils.py
  - [x] test_story_parsing_utils.py
  - [x] test_string_utils.py
  - [x] test_text_formatting_utils.py
  - [x] test_validation_helpers.py
  - [x] test_story_file_helpers.py
  - [x] test_all_utils.py
  - [x] tests/utils/README.md

**Testing Standards:**

- [COMPLETE] Every test must achieve 10.00/10 pylint (NO disable comments no pragma no noqa)
- [COMPLETE] Every test must work with `run_all_tests.py`
- [COMPLETE] Common code goes in `test_helpers.py` (DRY principle)
- [COMPLETE] Every test folder has README.md (what/why/tests list)
- [COMPLETE] Every subsystem has `test_all_<subsystem>.py` runner

### Refactor & test-harness cleanup - October 26, 2025

- [x] Centralized duplicated test helpers into `tests/test_helpers.py`
  - Replaced per-file fixtures and import-try scaffolds with canonical
    helpers to reduce duplication and increase clarity.
- [x] Added `tests/test_runner_common.py` and updated per-subsystem
  aggregators to use a shared subprocess runner and summary helpers.
- [x] Fixed subprocess import / module-resolution issues by setting
  `PYTHONPATH` for child processes and invoking modules with `-m
  tests.<module>` to ensure reliable imports.
- [x] Resolved Pylint duplicate-code (R0801) across `tests/` by
  centralizing shared logic and removing local duplicates.
- [x] Fixed a complexity warning (R0914) in `tests/test_helpers.py`
  by extracting nested logic into module-level functions.
- [x] Updated many tests (combat, cli, characters, validators, utils)
  to use the canonical helpers; replaced inline fixtures and fake
  input helpers with `tests.test_helpers` utilities.
- [x] Repaired failing combat-suite tests found during refactors
  (import/unpacking fixes) and re-ran the suite to green.
- [x] Completed repository reorganization into `src/`, added
  `game_data/` fixtures, and updated tests to the new package layout.
- [x] Achieved Pylint 10.00/10 for tests and removed emojis that
  caused Windows console encoding issues.

### Code Quality & Pylint

- [x] **Pylint cleanup complete** - All core files 10.00/10
  - [x] dnd_consultant.py (8.81 -> 9.88/10, 1028 -> 956 lines)
  - [x] enhanced_story_manager.py (8.71 -> 10.00/10, 1064 -> 433 lines)
  - [x] All 7 extracted modules (10.00/10)
  - [x] npc_auto_detection.py (9.66 -> 10.00/10)
  - [x] dungeon_master.py (8.85 -> 10.00/10)
  - [x] All validators (10.00/10 with shared helpers)
  - [x] combat_narrator.py (10.00/10)
  - [x] story_manager.py (10.00/10)
  - [x] **Emoji removal complete** - All emojis removed (29 files, no UTF-8 workarounds)

### JSON Validation System & Nickname Support - October 12, 2025

- [x] **Character validator** - Created character_validator.py with comprehensive schema validation for character JSON files
- [x] **NPC validator** - Created npc_validator.py with schema validation for NPC profiles
- [x] **Items validator** - Created items_validator.py with schema validation for custom items registry
- [x] **Party validator** - Created party_validator.py with party config validation and character cross-reference checking
- [x] **Unified validator** - Created validate_all.py to validate all game data types at once with comprehensive reporting
- [x] **Validator integration** - All JSON save operations now validate data before writing (fail-soft with warnings)
- [x] **Nickname field support** - Added nullable nickname field to all characters and NPCs for better name handling
- [x] **Name constraints** - Validators now enforce character name constraints (no apostrophes, quotes, or shell-unsafe characters)
- [x] **Clear error messages** - All validators provide specific, actionable error messages with field names and expected types
- [x] **Test suites** - Created comprehensive test files for all validators (tests/ folder, now committed to repository)
- [x] **Test infrastructure** - Created test_helpers.py for UTF-8 encoding and path setup (10.00/10 pylint)
- [x] **Test runner** - Created run_all_tests.py unified test runner with category support (10.00/10 pylint)
- [x] **Test configuration** - Created tests/.pylintrc for test-specific lint rules (proper configuration, not inline disables)
- [x] **Documentation** - Created docs/JSON_Validation.md and docs/Validator_Integration.md with usage guides
- [x] **Validator exception handling** - Party validator throws clear exceptions when party member names don't match character files

### Project Reorganization & Spell Highlighting - October 10, 2025

- [x] **game_data/ folder structure created** - Centralized all user data into game_data/ directory
- [x] **Characters migration** - Moved characters/ to game_data/characters/, updated 4 Python files
- [x] **NPCs migration** - Moved npcs/ to game_data/npcs/, updated 3 Python files, fixed example file skip bug
- [x] **Custom items migration** - Moved registry to game_data/items/, updated item_registry.py
- [x] **Party config migration** - Moved party JSON to game_data/current_party/, updated 3 references
- [x] **Campaigns folder setup** - Created game_data/campaigns/ for all campaign content
- [x] **.gitignore cleanup** - Removed 40+ old patterns, added comprehensive game_data/ patterns
- [x] **Documentation updates** - Updated README.md, copilot-instructions.md, Test_Example.md
- [x] **Spell highlighting system** - Created spell_highlighter.py with pattern-based spell detection
- [x] **Spell highlighting integration** - Integrated into enhanced_story_manager.py, extracts 57 known spells
- [x] **Integration testing** - All 10/10 tests passed (characters, NPCs, items, party, campaigns, spells)

### Repository Organization - October 5, 2025

- [x] **Folder restructure** - Created docs/ and templates/ folders for better organization
- [x] **Documentation reorganization** - Moved 6 docs to docs/, moved story_template.md to templates/
- [x] **Python code updates** - Updated enhanced_story_manager.py and story_manager.py template paths
- [x] **README navigation** - Added Documentation section with links to all docs
- [x] **Personal docs folder** - Created docs_personal/ (git-ignored) for internal documentation
- [x] **Cross-reference updates** - Fixed all links between documentation files
- [x] **Character name anonymization** - Replaced personal character names with generic examples throughout docs

### Documentation Improvements - October 5, 2025

- [x] **Party configuration documentation** - Added comprehensive section to README explaining current_party.json
- [x] **Party management guide** - Documented CLI and manual configuration methods
- [x] **Party validation notes** - Explained character name matching and git ignore behavior
- [x] **Party usage examples** - Showed how party config affects NPC detection and story analysis

### Character System & RAG Enhancements - October 5, 2025

- [x] **NPC species/lineage fields** - Added species and lineage fields to NPCProfile dataclass
- [x] **Character equipment tracking** - CharacterProfile now includes equipment dict and magic_items list as dataclass fields
- [x] **Item extraction methods** - Added get_all_character_items() and get_item_details() to CharacterConsultant
- [x] **Dual wiki support** - Separate lore wiki (RAG_WIKI_BASE_URL) and rules wiki (RAG_RULES_BASE_URL)
- [x] **Custom items registry** - Created item_registry.py and custom_items_registry.json for homebrew item tracking
- [x] **Homebrew filtering** - WikiClient blocks custom items from wiki lookups, returns local data instead
- [x] **Item integration** - CharacterProfile stores equipment, CharacterConsultant can extract and lookup items

### NPC Detection & Combat Narrator - October 4, 2025

- [x] **Automatic NPC detection** - System scans story content for NPCs (innkeepers, merchants, guards, blacksmiths)
- [x] **Smart filtering** - Excludes party members (from current_party.json) and existing NPC profiles
- [x] **False positive filtering** - Filters out sentence starters (Suddenly, Meanwhile, However, etc.)
- [x] **Story hooks integration** - Automatically adds NPC profile suggestions to story hooks file
- [x] **Ready-to-run code examples** - Includes Python snippets in hooks file for easy profile generation
- [x] **NPC detection documentation** - Created docs/NPC_DETECTION.md with full usage guide
- [x] **Auto-generated combat titles** - AI generates contextual titles from story context (e.g., "Goblin Ambush at Darkwood")
- [x] **Combat prompt support** - Accepts simple combat descriptions, not just Fantasy Grounds logs
- [x] **RAG integration for combat** - Uses wiki lookup for spell/ability descriptions in combat narratives
- [x] **Fixed literal \n bug** - Story hooks now have proper line breaks instead of literal backslash-n

### RAG (Retrieval-Augmented Generation) System - October 2025

- [x] **RAG architecture designed** - WikiCache, WikiClient, RAGSystem classes for wiki integration
- [x] **Wiki scraping implementation** - Created rag_system.py with web scraping using requests + BeautifulSoup
- [x] **Cache system implemented** - TTL-based caching in .rag_cache/ directory (git-ignored)
- [x] **Story generation integration** - DungeonMaster extracts locations and injects wiki context into AI prompts
- [x] **History check integration** - Created history_check_helper.py for character History checks with wiki lore
- [x] **.env configuration** - Added RAG settings to .env.example (RAG_ENABLED, RAG_WIKI_BASE_URL, RAG_RULES_BASE_URL, cache/search settings)
- [x] **.gitignore updated** - Added .rag_cache/, *.rag.json, rag_*.db patterns
- [x] **RAG documentation** - Created RAG_INTEGRATION.md (450+ lines) and RAG_QUICKSTART.md
- [x] **RAG testing** - Tested with wiki integration, verified location lookups

### AI Integration - September 2025

- [x] **AI Integration Complete** - Fully integrated with OpenAI SDK, supports OpenAI, Ollama, OpenRouter, and any OpenAI-compatible API
- [x] **Per-character AI configuration** - Each character can have unique AI settings (model, temperature, system prompts)
- [x] **AI-enhanced character reactions** - Characters respond using AI with rule-based fallback
- [x] **AI-enhanced DC suggestions** - Intelligent difficulty calculations with AI analysis
- [x] **Comprehensive documentation** - See docs/AI_INTEGRATION.md for complete guide
- [x] **NPC AI integration** - NPCs can also have AI-enhanced personalities and responses
- [x] **DM narrative generation** - AI-generated story narratives with character context
- [x] **Folder naming validation** - Implemented validation for _Campaign,_Quest, _Story,_Adventure suffixes
- [x] **Simplified .gitignore patterns** - Reduced to 4 clear folder patterns
