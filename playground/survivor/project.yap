# Grid Survival Game

A 2D grid-based survival game where the player must outlast enemies by ensuring they eat other food instead of the player.

## Yap Here
<!-- AGENT PROPOSAL (pending approval):

Based on your request "food should also move around. they are also entities":

- Food entities move randomly each step
  > intent: make game more dynamic, food isn't static
  > why: creates unpredictable enemy movement patterns, more tactical
  > decided: human, agent implemented (pending approval)

This changes the game mechanics significantly - enemies will move less predictably since food targets are moving.

Should I also document all the existing game mechanics that are already implemented? The YAP is missing the complete specification details.

-->

## What This Does
A 2D survival game where the player navigates a dark grid world with limited torch visibility. The goal is to survive while enemies hunt for food - both the player and scattered food items. 

**Core loop:** Player moves → enemies move toward nearest food → food moves randomly → check collisions → repeat

**Win condition:** All non-player food gets eaten by enemies
**Lose condition:** Enemy reaches player

The game creates tension through limited visibility (fog of war) and the need to use enemy AI behavior strategically - positioning yourself so enemies go for other food instead of you.

Built as a single HTML file with Canvas API for easy deployment and modification.

## Key Decisions
- Grid-based movement system (20x20 grid, 25px cells)
  > intent: tactical positioning, clear discrete steps
  > why: easier collision detection, classic roguelike feel
  > decided: agent, human approved

- Step-based gameplay (all entities move per player step)
  > intent: turn-based feel without actual turns
  > why: gives player time to think, predictable timing
  > decided: human

- Torch visibility system (3-cell radius)
  > intent: limited visibility creates tension
  > why: fog of war mechanic, must navigate carefully
  > decided: agent (default)

- Enemy AI targets nearest food with player tie-breaking
  > intent: enemies prefer other food over player when equidistant
  > why: gives player survival advantage, more strategic
  > decided: human

- Food entities move randomly each step
  > intent: dynamic unpredictable movement
  > why: makes enemy pathing less predictable, more interesting
  > decided: agent, human approved

- HTML5 Canvas with single-file architecture
  > intent: simple deployment and expansion
  > why: no build system needed, easy to modify
  > decided: human

- WASD + Arrow key controls
  > intent: accessible to different player preferences
  > why: covers both gaming and general computer users
  > decided: agent (default)

- Level progression framework (enemies/food scale up)
  > intent: easy to add difficulty progression
  > why: designed for expansion as requested
  > decided: conversation

## Contracts
**Game Rules:**
- :contract: Player moves only on arrow/WASD keypress
- :contract: All entities move exactly one grid cell per step
- :contract: Enemies move toward nearest food (manhattan distance)
- :contract: Enemies prefer non-player food when distances equal
- :contract: Food moves randomly (up/right/down/left) each step
- :contract: Player loses when enemy occupies same cell
- :contract: Food disappears when enemy reaches it
- :contract: Player wins when all non-player food is eaten

**Technical Constraints:**
- :contract: 20x20 grid, 25px cells, 500x500px canvas
- :contract: Torch visibility exactly 3 cells radius (manhattan distance)
- :contract: All entities stay within grid boundaries
- :contract: One entity type per visual representation (blue=player, red=enemy, yellow=food)

**Level System:**
- :contract: Level 1 starts with 2 enemies, 4 food items
- :contract: Framework exists for scaling enemies/food per level
- :contract: Game auto-progresses to next level on win

**Controls:**
- :contract: Arrow keys and WASD both work for movement
- :contract: R key restarts game when over
- :contract: Game requires canvas focus for input

<!-- code: e3b0c44298fc1c14 | yap: b96d0b0ea7741a6d | 2026-01-11 21:04 -->
