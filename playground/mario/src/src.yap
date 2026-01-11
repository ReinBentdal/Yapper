# Game Source Code

Core game modules implementing the retro platformer mechanics.

## What This Does

Implements the core game systems:
- Main game loop with fixed timestep physics
- Player character with movement, jumping, shooting
- Enemy AI with simple patrol patterns  
- Input handling for keyboard controls
- 8-bit style rendering with pixel-perfect graphics
- Level/world management with screen transitions
- Collision detection and physics

## Key Decisions

- ES6 modules with direct imports (decided: agent default)
  > why: no build step, simple development setup

- Fixed 16.67ms timestep (decided: agent default)
  > why: consistent physics regardless of framerate

- Entity-component pattern (decided: agent default)
  > why: each game object has update() and render() methods

- Immediate collision response (decided: agent default)
  > why: no collision queuing, resolve instantly for simple gameplay

## Contracts

- :contract: All entities have `update(deltaTime)` and `render(renderer)` methods
- :contract: Positions use pixel coordinates, origin at top-left
- :contract: Collision boxes are axis-aligned rectangles
- :contract: Screen boundaries: 0,0 to 800,600
- :contract: Grid alignment: positions divisible by 16

:warn: No sprite assets yet - using colored rectangles as placeholders

## Depends On

- HTML5 Canvas API
- ES6 module system
- RequestAnimationFrame API

## Used By

- index.html imports game.js to start the game loop

<!-- code: none | yap: none | timestamp -->

<!-- code: none | yap: 10d56544d356d8ac | 2026-01-11 03:46 -->
