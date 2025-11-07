# Story Continuation Guide

This guide explains the AI-powered story continuation feature that allows users to generate and append AI-enhanced narrative content to existing story files.

## Overview

The story continuation system enables:
- **Combat Scene Generation** - AI-enhanced combat narratives with RAG spell/ability lookup
- **Exploration Scene Generation** - Social, roleplay, and discovery scenes without combat
- **Automatic NPC Detection** - Identifies NPCs in generated content and creates profiles
- **Character Context Integration** - Incorporates party member personalities automatically
- **Persistent Story Updates** - Appends new content while preserving existing story

## User Workflow

### 1. View Existing Story

Open a story file in the CLI and select "Generate AI continuation"

```
[Your_Campaign]
└── 001_The_Tavern.md
```

When viewing the story, the system offers:
```
Generate AI continuation for this story? (y/n): 
```

### 2. Select Scene Type

Choose the type of scene to continue:

```
What type of scene is this?
1. Combat/Action scene
2. Exploration/Social/Roleplay scene

Choice (1-2): 
```

- **Combat**: Generates tactical combat narratives with spell/ability context
- **Exploration**: Generates discovery, social, or roleplay scenes (no combat)

### 3. Provide Continuation Prompt

Describe what happens next in the story:

```
For Combat:
"Goblins ambush the party on the forest road"

For Exploration:
"A mysterious hooded figure enters the tavern and approaches the party"
```

### 4. Review Generated Content

The system generates narrative content and updates the story file with:
- New story section with appropriate title
- Appended to existing story content
- Supporting files: story_hooks, session_results

## Scene Types and Behavior

### Combat Scenes

**Characteristics:**
- Generates tactical combat descriptions
- Includes character abilities and spell effects
- RAG context provides accurate spell/ability descriptions
- Focuses on action, damage, positioning, and outcomes

**System Prompt Constraints:**
- Allows combat, fighting, weapon use
- Includes tactical details
- Integrates RAG spell descriptions
- Respects character classes and abilities

**Example:**
```
Prompt: "The party encounters a dragon in the mountain pass"

Generated narrative (excerpt):
"The dragon's scales gleamed in the sunlight as it roared, unleashing a blast
of flame toward the party. Kael raised his shield, taking the brunt of the heat
as Morgana began chanting an incantation for Fireball - a 3rd-level evocation
spell that would create an explosive burst of flame..."
```

### Exploration Scenes

**Characteristics:**
- Generates discovery, social, and roleplay narratives
- NO combat or hostile action
- Focuses on character interactions, atmosphere, plot development
- RAG context enhances NPC abilities and magical items

**System Prompt Constraints:**
- FORBIDS combat, fighting, hostile action
- Focuses on interaction and discovery
- Maintains narrative flow
- Includes RAG context for spells/abilities in roleplay context

**Example:**
```
Prompt: "A mysterious bard arrives at the tavern with news of the King's decree"

Generated narrative (excerpt):
"As the party sat by the fireplace, the tavern door swung open. A cloaked
figure entered, their lute catching the lamplight. They approached the bar
and spoke quietly to the innkeeper, occasionally glancing toward your group.
After exchanging a few words and coins, the bard turned and walked directly
toward your table..."
```

## Implementation Details

### Core Files

**Story Generation:**
- `src/stories/story_ai_generator.py` - Core story generation with RAG integration
- `src/utils/spell_lookup_helper.py` - Shared spell/ability lookup

**Combat Narration:**
- `src/combat/combat_narrator.py` - Combat narrator orchestration
- `src/combat/narrator_ai.py` - AI-enhanced combat narration with RAG
- `src/utils/spell_lookup_helper.py` - Shared spell/ability lookup

**CLI Integration:**
- `src/cli/cli_story_manager.py` - Story file operations and continuation handling
- `src/cli/dnd_cli_helpers.py` - Helper functions for scene selection and prompts
- `src/stories/story_updater.py` - Appends content and generates supporting files

**Party Configuration:**
- `src/cli/party_config_manager.py` - Loads party members and their profiles
- `game_data/campaigns/[Campaign]/current_party.json` - Party member list

### Function Signatures

#### Story Generation

```python
def generate_story_from_prompt(
    ai_client,
    story_prompt: str,
    story_config: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Generate story narrative with RAG spell/ability context.
    
    Args:
        ai_client: AIClient instance
        story_prompt: User's story continuation prompt
        story_config: Dict with keys:
            - party_characters: Character profiles
            - campaign_context: Campaign setting info
            - max_tokens: Max response length (default 2000)
            - is_exploration: If True, prevents combat (default False)
    
    Returns:
        Generated narrative string or None if AI unavailable
    """
```

#### Combat Narration

```python
def narrate_combat_from_prompt(
    self,
    combat_prompt: str,
    story_context: str = "",
    style: str = "cinematic"
) -> str:
    """
    Generate combat narrative with RAG spell/ability context.
    
    Args:
        combat_prompt: Tactical combat description
        story_context: Optional story background
        style: Narrative style (cinematic, gritty, heroic, tactical)
    
    Returns:
        Combat narrative prose
    """
```

#### Spell/Ability Lookup

```python
def lookup_spells_and_abilities(prompt: str) -> str:
    """
    Look up D&D spells/abilities mentioned in prompt via RAG.
    
    Args:
        prompt: Text containing potential spell/ability names
    
    Returns:
        Formatted D&D Rules Context or empty string
    """
```

## RAG Integration

### Automatic Spell/Ability Context

Both story and combat generation automatically:
1. Scan the prompt for spell/ability names (18+ supported)
2. Look up descriptions from dnd5e.wikidot.com via RAG
3. Include formatted context in AI prompt
4. Provide accurate mechanical descriptions

### Supported Abilities

Vicious Mockery, Eldritch Blast, Fireball, Healing Word, Cure Wounds, Sacred Flame, Thunderwave, Magic Missile, Shield, Mage Armor, Wild Shape, Sneak Attack, Divine Smite, Lay on Hands, Bardic Inspiration, Rage, Action Surge, Second Wind

### Graceful Fallback

If RAG is unavailable:
- Stories and combat still generate normally
- No spell/ability context is added
- No error or interruption to user experience

## Supporting File Generation

When story content is appended, the system generates/updates:

### Story Hooks File (`story_hooks_*.md`)
- Unresolved plot threads
- Auto-detected NPC profiles
- Suggested future story directions

### Session Results File (`session_results_*.md`)
- Character actions and outcomes
- NPCs encountered
- Mechanical game data
- Recruiting pool information

## Testing

The system is thoroughly tested with:

**Unit Tests:**
- Story generation with/without AI (`tests/stories/test_story_ai_generator.py`)
- Combat narration with/without AI (`tests/combat/test_narrator_ai.py`)
- RAG spell lookup integration and graceful fallback

**Integration Tests:**
- Complete CLI continuation workflow (`tests/cli/test_cli_story_continuation.py`)
- Scene type selection and routing
- AI prompt construction
- Party member context integration
- is_exploration flag enforcement

**Code Quality:**
- All source files: 10.00/10 pylint score
- All test files: 10.00/10 pylint score
- No duplicate code, no disabled warnings
- Shared helpers used for common patterns

## Examples

### Combat Continuation

```
Story File: 001_The_Bandits.md

Existing content:
"The party enters a mountain pass where they spot armed figures ahead..."

User selects: Combat scene
User prompt: "The bandits attack - a brutal ambush"

Generated continuation (appended):
## The Ambush

The bandits erupted from their positions, crossbow bolts streaking through
the air. Kael raised his shield, deflecting one bolt as another sank into his
shoulder. Morgana, their wizard, began weaving her fingers in complex patterns,
preparing to cast Fireball - a 3rd-level evocation spell that would create a
devastating explosion of flame and force...
```

### Exploration Continuation

```
Story File: 002_In_Bree.md

Existing content:
"The party arrives in the town of Bree seeking information..."

User selects: Exploration/Social scene
User prompt: "A mysterious hooded figure approaches with urgent news"

Generated continuation (appended):
## The Messenger

As the party settled around a table in the Prancing Pony, a figure in a
tattered cloak approached. When they spoke, their voice was hushed but urgent,
revealing knowledge of an ancient evil stirring in the Weathertop hills...
```

## Best Practices

1. **Start Small**: Use simple, descriptive prompts
2. **Match Scene Type**: Select combat for action, exploration for discovery/roleplay
3. **Review Generated Content**: Always read and edit before finalizing
4. **Build on Existing Story**: Reference previous scenes and NPCs
5. **Let Party Shine**: Generated content incorporates character personalities
6. **Use Supporting Files**: Review story_hooks and session_results for guidance

## Troubleshooting

### "AI features not available - cannot generate continuation"
- AI client not configured
- Environment variables missing
- Configure `.env` with API key or use Ollama for local inference

### Combat appears in exploration scene (or vice versa)
- Verify correct scene type was selected
- Check is_exploration flag in story_config
- System prompt should forbid/allow combat appropriately

### Generated content doesn't match party members
- Verify current_party.json exists in campaign directory
- Check character profile files exist in game_data/characters/
- Party members should be named exactly as their character files

### No spell/ability context in narrative
- RAG system may be unavailable (graceful fallback)
- Spell/ability name may not match known list
- System still generates narrative without RAG context

---

For more information, see:
- [AI_INTEGRATION.md](AI_INTEGRATION.md) - AI configuration and setup
- [.github/copilot-instructions.md](../.github/copilot-instructions.md) - Project architecture
