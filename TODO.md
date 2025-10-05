# TODO List - D&D Character Consultant System

## 🔥 High Priority

### Story Management System
- [ ] **Test story creation flow** - Verify the enhanced story manager works with CLI interface end-to-end

### Character System Improvements  
- [ ] **Character validation** - Add validation for character JSON files during loading
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

### Technical Improvements
- [ ] **Plugin architecture** - Allow custom modules/plugins for specific campaign needs  
- [ ] **Export functionality** - Export stories to different formats (PDF, HTML, etc.)
- [ ] **Backup system** - Automated backup of character profiles and party configurations

### User Experience
- [ ] **Interactive setup** - Make setup.py more interactive for first-time users
- [ ] **Quick start guide** - Create a step-by-step tutorial for new users

## 🐛 Known Issues to Fix

### Bug Fixes
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

## ✅ Recently Completed

### Repository Organization - October 5, 2025
- [x] ✅ **Folder restructure** - Created docs/ and templates/ folders for better organization
- [x] ✅ **Documentation reorganization** - Moved 6 docs to docs/, moved story_template.md to templates/
- [x] ✅ **Python code updates** - Updated enhanced_story_manager.py and story_manager.py template paths
- [x] ✅ **README navigation** - Added Documentation section with links to all docs
- [x] ✅ **Personal docs folder** - Created docs_personal/ (git-ignored) for internal documentation
- [x] ✅ **Cross-reference updates** - Fixed all links between documentation files
- [x] ✅ **Character name anonymization** - Replaced personal character names with generic examples throughout docs

### Documentation Improvements - October 5, 2025
- [x] ✅ **Party configuration documentation** - Added comprehensive section to README explaining current_party.json
- [x] ✅ **Party management guide** - Documented CLI and manual configuration methods
- [x] ✅ **Party validation notes** - Explained character name matching and git ignore behavior
- [x] ✅ **Party usage examples** - Showed how party config affects NPC detection and story analysis

### NPC Detection System - October 4, 2025
- [x] ✅ **Automatic NPC detection** - System scans story content for NPCs (innkeepers, merchants, guards, blacksmiths)
- [x] ✅ **Smart filtering** - Excludes party members (from current_party.json) and existing NPC profiles
- [x] ✅ **False positive filtering** - Filters out sentence starters (Suddenly, Meanwhile, However, etc.)
- [x] ✅ **Story hooks integration** - Automatically adds NPC profile suggestions to story hooks file
- [x] ✅ **Ready-to-run code examples** - Includes Python snippets in hooks file for easy profile generation
- [x] ✅ **NPC detection documentation** - Created docs/NPC_DETECTION.md with full usage guide
- [x] ✅ **Test validation** - Updated test_final_validation.py to validate automatic NPC detection
- [x] ✅ **Fixed literal \n bug** - Story hooks now have proper line breaks instead of literal backslash-n

### Combat Narrator Improvements - October 4, 2025
- [x] ✅ **Auto-generated combat titles** - AI generates contextual titles from story context (e.g., "Goblin Ambush at Darkwood")
- [x] ✅ **Combat prompt support** - Accepts simple combat descriptions, not just Fantasy Grounds logs
- [x] ✅ **RAG integration for combat** - Uses wiki lookup for spell/ability descriptions in combat narratives
- [x] ✅ **Test Combat Narrator** - Verified combat_narrator.py works with centralized AI configuration
- [x] ✅ **Combat Summary conversion** - Combat narrator accepts prompts/summaries instead of requiring raw logs

### RAG (Retrieval-Augmented Generation) System - October 2025
- [x] ✅ **RAG architecture designed** - WikiCache, WikiClient, RAGSystem classes for wiki integration
- [x] ✅ **Wiki scraping implementation** - Created rag_system.py with web scraping using requests + BeautifulSoup
- [x] ✅ **Cache system implemented** - TTL-based caching in .rag_cache/ directory (git-ignored)
- [x] ✅ **Story generation integration** - DungeonMaster extracts locations and injects wiki context into AI prompts
- [x] ✅ **History check integration** - Created history_check_helper.py for character History checks with wiki lore
- [x] ✅ **.env configuration** - Added RAG settings to .env.example (RAG_ENABLED, RAG_WIKI_BASE_URL, cache/search settings)
- [x] ✅ **.gitignore updated** - Added .rag_cache/, *.rag.json, rag_*.db patterns
- [x] ✅ **RAG documentation** - Created RAG_INTEGRATION.md (450+ lines) and RAG_QUICKSTART.md
- [x] ✅ **RAG testing** - Tested with wiki integration, verified location lookups

### AI Integration - September 2025
- [x] ✅ **AI Integration Complete** - Fully integrated with OpenAI SDK, supports OpenAI, Ollama, OpenRouter, and any OpenAI-compatible API
- [x] ✅ **Per-character AI configuration** - Each character can have unique AI settings (model, temperature, system prompts)
- [x] ✅ **AI-enhanced character reactions** - Characters respond using AI with rule-based fallback
- [x] ✅ **AI-enhanced DC suggestions** - Intelligent difficulty calculations with AI analysis
- [x] ✅ **Comprehensive documentation** - See docs/AI_INTEGRATION.md for complete guide
- [x] ✅ **NPC AI integration** - NPCs can also have AI-enhanced personalities and responses
- [x] ✅ **DM narrative generation** - AI-generated story narratives with character context
- [x] ✅ **Folder naming validation** - Implemented validation for _Campaign, _Quest, _Story, _Adventure suffixes
- [x] ✅ **Simplified .gitignore patterns** - Reduced to 4 clear folder patterns

---

**Last Updated:** October 4, 2025 (NPC Detection + Combat Narrator Updates)
**Priority Legend:** 🔥 High | 🚧 Medium | 🌟 Low | 🐛 Bugs | 📝 Docs