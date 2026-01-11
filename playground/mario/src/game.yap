# Game Controller

Main game orchestration and loop management.

## What This Does

The Game class is the central coordinator that:
- Sets up canvas and all game systems (input, renderer, player, enemies, world)
- Runs the main game loop with fixed timestep physics
- Manages UI updates (lives, coins, screen counter)
- Handles game state transitions (playing, paused, game over, complete)
- Coordinates screen loading and entity spawning

## Key Decisions

- Fixed timestep at 60fps (16.67ms) (decided: agent default)
  > why: consistent physics across different hardware/browsers

- Accumulator pattern for frame timing (decided: agent default)
  > why: handles variable framerate while keeping physics stable

- Single Game instance orchestrates all systems (decided: agent default)
  > why: clear ownership and coordination point

## Contracts

- :contract: Runs at exactly 60fps fixed timestep regardless of display framerate
- :contract: Updates all systems in order: input → player → enemies → world
- :contract: UI elements (lives, coins, screen) updated every frame
- :contract: Canvas must have ID 'gameCanvas' in HTML

## Depends On

- input.js (Input class)
- renderer.js (Renderer class)  
- player.js (Player class)
- enemies.js (EnemyManager class)
- world.js (World class)
- HTML elements: gameCanvas, lives, coins, screen

## Used By

- index.html imports and creates Game instance

<!-- code: none | yap: none | timestamp -->

<!-- code: 471f5c049e2c8ff7 | yap: b9a0b0b9e1997902 | 2026-01-11 03:44 -->
