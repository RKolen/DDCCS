# TODO List - D&D Character Consultant System

## 🔥 High Priority

### Story Management System
- [ ] **Update README references** - Remove outdated "Story_Series_Folders" references since we now use folder-based organization 
- [ ] **Test story creation flow** - Verify the new enhanced story manager works with the CLI interface
- [ ] **Document party configuration** - Add section about current_party.json management to README
- [ ] **Validate .gitignore patterns** - Ensure all story content patterns are properly ignored

### Character System Improvements  
- [ ] **Character validation** - Add validation for character JSON files during loading
- [ ] **Level progression tracking** - Add system to track character level changes over time

### User Experience
- [ ] **Error handling** - Improve error messages throughout the system for better user guidance
- [ ] **VSCode tasks update** - Ensure all VSCode tasks work with the new enhanced system

### Combat & Story Editing
- [ ] **Fix Combat Summary conversion** - Update combat narrator to accept prompts/summaries instead of raw logs, test combat narrator functionality
- [ ] **Story amender functionality** - Add system to suggest character reassignments (e.g., "Character A did X but Character B is a better fit for this action")

### AI Integration
- [ ] **Local LLM integration** - Integrate with local LLMs for enhanced creative suggestions and character consultation
- [ ] **AI-powered story suggestions** - Use AI to suggest story developments, character actions, and narrative improvements
- [ ] **Intelligent character matching** - AI-assisted character selection for actions based on abilities and personality

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
- [ ] **NPC integration** - Better integration of NPCs with the story management system
- [ ] **Combat narrative templates** - Pre-built templates for different combat scenarios

### Technical Improvements
- [ ] **Configuration system** - Centralized config file for system settings

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
- [ ] **Add party management section** explaining current_party.json
- [ ] **Update workflow examples** with real use cases
- [ ] **Add troubleshooting section** for common issues

### New Documentation
- [ ] **API documentation** - For developers who want to extend the system
- [ ] **Character creation guide** - Detailed guide for creating rich character profiles
- [ ] **Campaign management best practices** - Tips for organizing complex campaigns
- [ ] **Integration guide** - How to integrate with external tools

---

## ✅ Recently Completed

- [x] **Fixed character loading** - Exclude template/example files from loading
- [x] **Party configuration system** - Configurable current_party.json with templates
- [x] **Story/mechanics separation** - Pure narrative in stories, mechanics in session results
- [x] **Enhanced .gitignore** - Comprehensive protection of campaign content
- [x] **Git history cleanup** - Removed story references from version control
- [x] **Enhanced story manager** - Better organization and user choice system

---

**Last Updated:** September 28, 2025
**Priority Legend:** 🔥 High | 🚧 Medium | 🌟 Low | 🐛 Bugs | 📝 Docs