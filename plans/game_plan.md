# Interactive Combat Emulator Plan

## Overview

2D top-down grid-based combat emulator for the D&D Character Consultant System.
Allows the DM to run tactical encounters between the current party and
monsters/NPCs on a map, with click-based movement and attacks, initiative
tracking, HP management, and action economy enforcement. Future phase adds an
AI DM agent that selects optimal monster/NPC actions each turn.

Modelled after Fantasy Grounds Ultimate (FGU) 2D top-down view.

---

## What Already Exists (Reusable)

| Component | Module | What You Get |
|---|---|---|
| Character combat stats | `src/characters/character_sheet.py` | HP, AC, speed, ability scores, proficiency, equipment, spells |
| Encounter difficulty | `src/encounters/encounter_scaler.py` | Party-vs-monster XP thresholds, `PartyMember` dataclass |
| D&D rules engine | `src/utils/dnd_rules.py` | Modifier calc, proficiency by level, DC scaling |
| NPC profiles | `src/npcs/npc_agents.py` | Simplified / full / major boss stat blocks incl. legendary actions |
| Party management | `src/stories/party_manager.py` | Party list, add/remove |
| Combat narration | `src/combat/combat_narrator.py` | AI narrative output per action (plug in after resolution) |
| AI client | `src/ai/ai_client.py` | OpenAI-compatible chat completion (future AI DM) |
| Class icons | `src/utils/ascii_art.py` | Token display fallback |

---

## What Is Missing (Gaps to Build)

### Data Layer

| Missing | Needed For |
|---|---|
| `current_hp` per combatant | HP bar, death saves, damage tracking |
| `position: (grid_x, grid_y)` per combatant | Map placement, movement, range |
| Initiative order + turn state | Turn sequencing |
| Action economy per turn | `action_used`, `bonus_action_used`, `reaction_used`, `movement_remaining` |
| Condition/status effects | Poisoned, prone, stunned, concentrating, etc. |
| Spell slot consumption | Slots available vs. used per combat |
| Temporary HP | Separate from current HP |
| Concentration tracking | One spell at a time |
| Death save state | Failures/successes when at 0 HP |
| Monster stat blocks | CR, XP value, attacks (name, to-hit bonus, damage dice), traits, multiattack |
| Map/terrain data | Grid dimensions, walls, obstacles, difficult terrain, doors |
| Combatant type flag | `player` / `npc` / `monster` for AI DM targeting logic |

### Logic Layer

| Missing | Needed For |
|---|---|
| Attack roll resolution | d20 + to-hit vs. AC -> hit/miss |
| Damage roll resolution | Dice expression parser (`2d6+4`) |
| Movement validation | Speed limit, difficult terrain cost, wall blocking |
| Range validation | Melee (5 ft), ranged (short/long), spell range |
| AoE calculation | Blast radius from origin cell |
| Line-of-sight check | Wall occlusion for ranged attacks |
| Saving throw resolution | d20 + modifier vs. DC |
| Condition application/removal | Duration-based, concentration break |
| Legendary action budget | Reset each turn for boss NPCs |

### Visual / UI Layer

| Missing | Needed For |
|---|---|
| Square grid renderer | 2D top-down map |
| Token system | Character icons on grid cells |
| Movement range highlight | Blue overlay for reachable cells |
| Attack range highlight | Red overlay for valid targets |
| Initiative tracker panel | Turn order sidebar |
| HP bar per token | Visual health state |
| Action economy panel | Action / Bonus / Move / Reaction indicators |
| Condition badge on token | Status indicators |
| Log panel | Per-action narrative + dice results |
| Map editor / loader | JSON map files or procedural generation |

---

## Language and Framework

### Option A - Python + Pygame (Recommended for MVP)

The entire `src/` stack imports directly with zero serialization overhead.
Every rule, stat, AI client, and narrator is already in Python. Pygame handles
a 2D square grid, token sprites, click events, and panel layouts without
leaving the ecosystem.

Stack additions: `pygame`, `pygame-gui` (panels/buttons), `pytmx` (optional
Tiled map loader).

Layout: left 70% = grid canvas, right 30% = Pygame surfaces for panels.

Constraints:
- No browser-based sharing without Pygbag (WASM wrapper).
- Complex HTML-style UI (tooltips, forms) requires manual surface management.
- HiDPI/resolution scaling requires manual handling.

### Option B - Python FastAPI + React/TypeScript + Phaser.js

More polished UI, runs in browser, leverages existing Gatsby/React knowledge.
Phaser 3 has built-in tilemap and pointer-click grid systems.

Constraints:
- Requires a running FastAPI server; Python logic becomes an HTTP API.
- HTTP round-trip latency per action.
- Two separate codebases to maintain.

### Option C - Godot 4

Purpose-built for 2D grid RPG. Excellent TileMap, AStarGrid2D pathfinding,
and token tools built in.

Constraints:
- Cannot import any existing Python modules - full rules rewrite in GDScript.
- Entirely new ecosystem.

### Decision

Phase 1 (MVP): Python + Pygame. Zero friction to integrate existing code.

Phase 2 (upgrade path): Wrap resolution engine in FastAPI, build a
React/Phaser frontend if browser access becomes a priority. The data layer
and rules engine built in Phase 1 transfer directly.

---

## Module Structure

```
src/
  combat_emulator/
    __init__.py
    state/
      combat_state.py        # CombatState dataclass - source of truth
      combatant.py           # Combatant wraps character/npc, adds current_hp, pos, conditions
      initiative_tracker.py  # InitiativeTracker - ordered list, whose turn, round counter
      action_economy.py      # ActionEconomy - action/bonus/move/reaction per turn
      condition_registry.py  # Condition enum + duration tracking
    map/
      grid.py                # Grid(width, height) - cell data, passability, terrain type
      map_loader.py          # Load JSON map files from game_data/maps/
      pathfinder.py          # BFS movement range + A* path calculation
      los.py                 # Line-of-sight via Bresenham ray cast
    resolution/
      dice.py                # parse_dice_expr("2d6+4") -> roll -> int
      attack_resolver.py     # roll_attack(attacker, target) -> AttackResult
      damage_resolver.py     # roll_damage(weapon/spell, crit) -> int
      saving_throw.py        # roll_save(combatant, ability, dc) -> bool
      spell_resolver.py      # Spell effect dispatcher
    ui/
      renderer.py            # Main Pygame loop, surface layout
      grid_view.py           # Draw grid, tokens, highlights
      initiative_panel.py    # Right-side turn order + HP bars
      action_panel.py        # Action economy indicators
      log_panel.py           # Scrollable action log
      token.py               # Token sprite, HP bar, condition badges
      highlight.py           # Movement / attack range overlays
    ai_dm/
      dm_agent.py            # AI selects optimal monster action
      target_selector.py     # Scoring function for AI target choice
    data/
      monster_registry.py    # Load monster stat blocks from game_data/monsters/
    emulator.py              # Entry point: CombatEmulator.run()

game_data/
  monsters/                  # NEW: monster stat blocks (JSON)
    goblin.json
    orc.json
    troll.json
    ...
  maps/                      # NEW: map definition files (JSON)
    dungeon_room_1.json
    tavern_brawl.json
    ...
```

---

## Monster Stat Block Schema

```json
{
  "name": "Goblin",
  "cr": 0.25,
  "xp": 50,
  "size": "Small",
  "type": "humanoid",
  "alignment": "neutral evil",
  "max_hit_points": 7,
  "hit_dice": "2d6",
  "armor_class": 15,
  "armor_type": "leather armor, shield",
  "movement_speed": 30,
  "ability_scores": {
    "strength": 8,
    "dexterity": 14,
    "constitution": 10,
    "intelligence": 10,
    "wisdom": 8,
    "charisma": 8
  },
  "saving_throws": {},
  "skills": {"stealth": 6},
  "damage_resistances": [],
  "damage_immunities": [],
  "condition_immunities": [],
  "senses": {"darkvision": 60, "passive_perception": 9},
  "languages": ["Common", "Goblin"],
  "attacks": [
    {
      "name": "Scimitar",
      "attack_type": "melee",
      "to_hit_bonus": 4,
      "reach": 5,
      "damage_dice": "1d6",
      "damage_bonus": 2,
      "damage_type": "slashing"
    },
    {
      "name": "Shortbow",
      "attack_type": "ranged",
      "to_hit_bonus": 4,
      "range_short": 80,
      "range_long": 320,
      "damage_dice": "1d6",
      "damage_bonus": 2,
      "damage_type": "piercing"
    }
  ],
  "multiattack": null,
  "traits": [
    {
      "name": "Nimble Escape",
      "description": "Can take the Disengage or Hide action as a bonus action."
    }
  ],
  "legendary_actions": null,
  "lair_actions": null
}
```

---

## Map Schema

```json
{
  "name": "Dungeon Room 1",
  "width": 20,
  "height": 15,
  "cell_size_ft": 5,
  "cells": [
    {"x": 0, "y": 0, "terrain": "wall"},
    {"x": 1, "y": 1, "terrain": "floor"},
    {"x": 3, "y": 4, "terrain": "difficult"},
    {"x": 5, "y": 5, "terrain": "door", "open": false}
  ],
  "spawn_points": {
    "players": [{"x": 2, "y": 2}, {"x": 3, "y": 2}],
    "monsters": [{"x": 18, "y": 12}, {"x": 17, "y": 13}]
  }
}
```

Terrain types: `floor`, `wall`, `difficult`, `door`, `water`, `pit`.

---

## Interaction Model (Click Flow)

1. Click own token -> select it; highlight movement range (blue) and attack
   range (red) on enemies in range with line of sight.
2. Click a blue cell -> move token, deduct movement feet from `action_economy`.
3. Click a red enemy token -> open action menu (Attack / Spell / Disengage /
   Dash / Help / End Turn).
4. Click Attack -> auto-roll attack + damage, update `current_hp`, push result
   to log panel, feed to `CombatNarrator` for one-sentence prose output.
5. End Turn -> advance initiative, reset action economy for next combatant.

---

## Condition Registry

Standard D&D 5e conditions to track:

- BLINDED, CHARMED, DEAFENED, EXHAUSTION (1-6), FRIGHTENED
- GRAPPLED, INCAPACITATED, INVISIBLE, PARALYZED, PETRIFIED
- POISONED, PRONE, RESTRAINED, STUNNED, UNCONSCIOUS
- CONCENTRATING (custom: breaks on damage if save fails)
- DEAD (at 0 HP after failed death saves)

Each condition stored as `Condition(type, duration_rounds, source_combatant)`.

---

## Action Economy Per Turn

```python
@dataclass
class ActionEconomy:
    action_used: bool = False
    bonus_action_used: bool = False
    reaction_used: bool = False
    movement_remaining: int = 0   # feet, populated from combatant speed on turn start

    def reset(self, movement_speed: int) -> None:
        self.action_used = False
        self.bonus_action_used = False
        self.reaction_used = False
        self.movement_remaining = movement_speed
```

---

## Phase 1 - Core Combat Engine (No UI)

Priority order:

1. `Combatant` dataclass wrapping existing character/NPC JSON; adds
   `current_hp`, `position`, `conditions`, `action_economy`, `combatant_type`.
2. `dice.py` - regex dice expression parser and roller (`d20`, `2d6+4`).
3. `attack_resolver.py` - uses `calculate_modifier()` from `dnd_rules.py`;
   compares roll vs. AC; detects crits (natural 20).
4. `damage_resolver.py` - rolls damage dice, doubles dice on crit, applies
   resistance/vulnerability.
5. `initiative_tracker.py` - `roll_initiative()` for all combatants, sort
   descending, expose `current_combatant()` / `advance_turn()`.
6. `action_economy.py` - resets each turn, tracks all four resources.
7. `condition_registry.py` - `Condition` enum, duration countdown per round.
8. `monster_registry.py` + `game_data/monsters/*.json` schema.
9. `CombatState` - single source of truth for the entire encounter.
10. Unit tests in `tests/combat_emulator/` mirroring module structure.

---

## Phase 2 - Grid and Pygame UI

1. `grid.py` - `Grid(width, height, cell_size_px)`; each cell stores terrain
   type and occupant reference.
2. `map_loader.py` - load `game_data/maps/*.json` into `Grid`.
3. `pathfinder.py` - BFS flood-fill for movement range (difficult terrain costs
   2 ft per cell), returns set of reachable cells.
4. `los.py` - Bresenham ray between two cells; returns `True` if no wall blocks.
5. `renderer.py` - Pygame 1280x800 window. Left 70% grid, right 30% panels.
6. Token system - class icon from `ascii_art.py` or portrait image; HP bar
   overlay; condition badge text (no emojis).
7. Highlight overlays - blue for movement range, red for valid attack targets.
8. Initiative panel - ordered turn list with HP bars on the right.
9. Log panel - last 12 lines of dice results + AI narrative sentences.
10. Full combat loop playtest with existing party vs. starter monsters.

---

## Phase 3 - AI DM Agent (Future)

The AI DM scores all possible monster actions each turn and picks the optimal
one. The DM can set an aggression dial (0.0 = random, 1.0 = optimal) so
monsters feel fair rather than perfectly tactical.

Implementation:

1. `target_selector.py` - score each enemy by: lowest HP, flanking available,
   prone status, concentration break value, caster priority.
2. `dm_agent.py` - enumerate valid actions for current monster (attacks,
   special traits, spells, movement), call `AIClient.chat_completion()` with
   serialized `CombatState` as JSON context and action list; receive chosen
   action as structured JSON (use function calling / structured output).
3. Legendary action hooks - after each player turn, call
   `dm_agent.use_legendary_action()` if the boss NPC has budget remaining.
4. Lair action hooks - at initiative count 20, trigger lair actions if enabled
   on the boss NPC profile.

---

## Constraints

| Constraint | Impact |
|---|---|
| Pylint 10.00/10 required | All new modules must pass; avoid complex lambdas in dice roller |
| No hardcoded config | Monster dir, maps dir, window size, cell size -> `CombatConfig` in `src/config/config_types.py` |
| mypy + Pylance clean | All dataclasses need full type annotations; `Optional` for nullable fields |
| No emojis | Condition badges must be ASCII text or image assets, never emoji characters |
| Character JSON has no `current_hp` | Derive from `max_hit_points` at combat start; never mutate source JSON |
| `movement_speed` is feet, not cells | Divide by 5 for cell count; store as `movement_speed_cells` on `Combatant` |
| Simplified NPC profiles have no attack data | Fall back to generic attack based on CR estimate, or prompt DM to promote to full profile |
| No existing monster stat blocks | `game_data/monsters/` directory and schema designed from scratch |

---

## New Files Required

| File | Purpose |
|---|---|
| `game_data/monsters/*.json` | Monster stat blocks |
| `game_data/maps/*.json` | Map and grid definitions |
| `src/combat_emulator/` | Full emulator module (see structure above) |
| `tests/combat_emulator/` | Mirrored test structure |
| `src/config/config_types.py` | Add `CombatConfig` (window size, cell size, dirs) |
| `docs/COMBAT_EMULATOR.md` | Architecture and usage documentation |

---

## Build Order

| Week | Work |
|---|---|
| 1 | Combatant + CombatState + dice.py + attack/damage/save resolvers |
| 2 | Monster JSON schema + 5-10 starter monsters + initiative tracker |
| 3 | Grid + pathfinder + LoS (headless, unit-tested) |
| 4 | Pygame renderer: grid view + tokens + click-to-move |
| 5 | Click-to-attack + action menu + log panel + HP bars |
| 6 | Conditions + action economy + death saves + concentration |
| 7 | Map loader + starter maps + full combat loop playtest |
| 8 | AI DM agent (Phase 3, optional) |

---

## Documentation to Update on Implementation

Per Rule 5, update these files when implementing:

| Change | Documentation |
|---|---|
| New `src/combat_emulator/` module | `src/README.md` |
| New `CombatConfig` key | `docs/AI_INTEGRATION.md` or `.env.example` |
| New `game_data/monsters/` and `maps/` directories | `docs/JSON_Validation.md` |
| New test category `combat_emulator` | `tests/README.md` |
| Full architecture | Create `docs/COMBAT_EMULATOR.md` |
