# TODO List - D&D Character Consultant System

## 🔥 High Priority
### Code Quality & Testing
- [-] **Pylint the codebase** - Systematic pylint cleanup to achieve 9.5+/10 scores across all files
  - [x] dnd_consultant.py (8.81 → 9.88/10, 1028 → 956 lines)
  - [x] enhanced_story_manager.py (8.71 → 10.00/10, 1064 → 433 lines)
  - [x] All 7 extracted modules (10.00/10): character_consistency, hooks_and_analysis, npc_auto_detection, party_config_manager, session_results_manager, story_file_manager, text_formatting_utils
  - [x] npc_auto_detection.py (9.66 → 10.00/10)
  - [x] dungeon_master.py (8.85 → 10.00/10)
  - [ ] character_consultants.py
  - [ ] story_manager.py
  - [ ] combat_narrator.py
  - [ ] ai_client.py
  - [ ] rag_system.py
  - [ ] All validator files
  - [ ] Setup and helper files

  - [ ] **Comprehensive system testing** - End-to-end testing of all workflows
  - [ ] Story creation flow (new series, in-series, standalone)
  - [ ] Character management (create, edit, party config)
  - [ ] Combat conversion (FGU logs and prompts)
  - [ ] Character consultations and DC suggestions
  - [ ] Story analysis and NPC detection
  - [ ] RAG integration with wiki lookups
  - [ ] AI integration with all features
  - [ ] Validator integration (all JSON operations)

### Story Management System
- [ ] **Test story creation flow** - Verify the enhanced story manager works with CLI interface end-to-end

### Character System Improvements  
- [ ] **Level progression tracking** - Add system to track character level changes over time

### User Experience
- [ ] **Error handling** - Improve error messages throughout the system for better user guidance
- [ ] **VSCode tasks update** - Ensure all VSCode tasks work with the new enhanced system

### Combat & Story Editing
- [ ] **Story amender functionality** - Add system to suggest character reassignments (e.g., "Character A did X but Character B is a better fit for this action")

### AI Integration
- [ ] **AI-powered story suggestions** - Use AI to suggest story developments and narrative improvements (future enhancement)
- [ ] **Intelligent character matching** - AI-assisted character selection for actions (future enhancement)

## 🚧 Medium Priority

### Character System Improvements
- [ ] **Character templates** - Create additional class-specific templates beyond the basic example
- [ ] **Multi-class support** - Enhance character profiles to support multiclassing

### Feature Enhancements
- [ ] **Campaign templates** - Create templates for common campaign types (mystery, dungeon crawl, etc.)
- [ ] **Character relationship mapping** - Visual or structured relationship tracking between characters
- [ ] **Session notes integration** - Better integration between session results and story narrative
- [ ] **DC difficulty scaling** - Add optional level-based DC scaling recommendations

### Story Tools
- [ ] **Story timeline tracking** - Track chronological order of events across campaigns
- [ ] **Combat narrative templates** - Pre-built templates for different combat scenarios

### Technical Improvements
- [ ] **Configuration system** - Centralized config file for system settings
- [ ] **Optional SQLite integration** - Add optional database support for:
  - Character knowledge tracking (History check results)
  - Session history and analytics
  - Campaign statistics and insights
  - Keep JSON as default for simplicity

## 🌟 Low Priority / Nice to Have

### Advanced Features
- [ ] **In-world calendar tracking** - Track campaign timeline, seasons, and story chronology within the game world

### Story Tools
- [ ] **Character arc analysis** - Tools to analyze character development over multiple stories
- [ ] **Custom spell highlighting** - Extend spell highlighting system to support homebrew/custom spells (currently only official D&D 5e spells via wikidot are highlighted)

### Technical Improvements
- [ ] **Plugin architecture** - Allow custom modules/plugins for specific campaign needs  
- [ ] **Export functionality** - Export stories to different formats (PDF, HTML, etc.)
- [ ] **Backup system** - Automated backup of character profiles and party configurations

### User Experience
- [ ] **Interactive setup** - Make setup.py more interactive for first-time users
- [ ] **Quick start guide** - Create a step-by-step tutorial for new users

## 🐛 Known Issues to Fix

### Bug Fixes
- [ ] **W0611: Unused AIClient imported from ai_client (unused-import)** In dungeon_master.py
- [ ] **R0904: Too many public methods (24/20) (too-many-public-methods)** In enhanced_story_manager.py
- [ ] **Unicode handling** - Fix emoji/Unicode issues in Windows console output (partially resolved)
- [ ] **File path handling** - Ensure cross-platform compatibility for file paths
- [ ] **Memory usage** - Optimize character loading for large numbers of characters
- [ ] **Git integration** - Test git functionality with different repository structures

### Quality of Life
- [ ] **Startup time** - Optimize initial loading of character consultants
- [ ] **Tab completion** - Add tab completion for character names in CLI
- [ ] **Command history** - Save and recall previous commands in interactive mode
- [ ] **Batch operations** - Support for bulk character or story operations

## 📝 Documentation TODOs

### README Updates
- [ ] **Remove outdated references** to Story_Series_Folders structure
- [ ] **Update workflow examples** with real use cases
- [ ] **Add troubleshooting section** for common issues

### New Documentation
- [ ] **API documentation** - For developers who want to extend the system
- [ ] **Character creation guide** - Detailed guide for creating rich character profiles
- [ ] **Campaign management best practices** - Tips for organizing complex campaigns
- [ ] **Integration guide** - How to integrate with external tools

## [x] Recently Completed

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
- [x] **Test suites (local only)** - Created comprehensive test files for all validators (tests/ folder, git-ignored, not yet in repository)
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
- [x]  **Folder restructure** - Created docs/ and templates/ folders for better organization
- [x]  **Documentation reorganization** - Moved 6 docs to docs/, moved story_template.md to templates/
- [x]  **Python code updates** - Updated enhanced_story_manager.py and story_manager.py template paths
- [x]  **README navigation** - Added Documentation section with links to all docs
- [x]  **Personal docs folder** - Created docs_personal/ (git-ignored) for internal documentation
- [x]  **Cross-reference updates** - Fixed all links between documentation files
- [x]  **Character name anonymization** - Replaced personal character names with generic examples throughout docs

### Documentation Improvements - October 5, 2025
- [x]  **Party configuration documentation** - Added comprehensive section to README explaining current_party.json
- [x]  **Party management guide** - Documented CLI and manual configuration methods
- [x]  **Party validation notes** - Explained character name matching and git ignore behavior
- [x]  **Party usage examples** - Showed how party config affects NPC detection and story analysis

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
- [x] **Folder naming validation** - Implemented validation for _Campaign, _Quest, _Story, _Adventure suffixes
- [x] **Simplified .gitignore patterns** - Reduced to 4 clear folder patterns

---

**Last Updated:** October 12, 2025
**Priority Legend:** 🔥 High | 🚧 Medium | 🌟 Low | 🐛 Bugs | 📝 Docs