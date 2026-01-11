# Retro Mario Web Game

A side-scrolling 8-bit style web platformer focused on exploration, built with pure HTML5 Canvas and JavaScript.

## Quick Map

- `index.html` - main entry point, canvas setup
- `src/game.js` - core game loop and state management  
- `src/player.js` - player character mechanics
- `src/enemies.js` - enemy AI and behavior
- `src/world.js` - level data and screen management
- `src/input.js` - keyboard input handling
- `src/renderer.js` - 8-bit graphics rendering
- `src/physics.js` - collision detection and movement
- `assets/` - sprites and audio files

## Conventions

- 16x16px grid for all positioning
- 60fps target with fixed timestep physics
- ES6 modules, no build tools
- Pixel-perfect rendering (no smoothing)
- All measurements in pixels
- Game coordinates: origin top-left

## Key Decisions

- Fixed timestep physics (decided: agent default)
  > why: consistent behavior across different framerates
  
- Component-based entities (decided: agent default)  
  > why: player, enemies, coins as separate classes with update/render methods

- Screen-based world (decided: conversation)
  > why: single screen areas connected left-to-right for exploration focus

- Pure Canvas rendering (decided: human)
  > why: no frameworks, direct pixel manipulation for authentic 8-bit look

- Game resolution: 800x600px (decided: agent, human approved)
  > why: classic 4:3 ratio, good for modern screens while maintaining retro feel

- Player movement: 120px/sec, jump 300px/sec (decided: agent, human approved)  
  > why: responsive controls that feel "snappy" for platforming

- Enemy AI: simple patrol (decided: agent, human approved)
  > why: predictable obstacles fitting exploration-focused gameplay

- Controls: arrows + X key (decided: agent, human approved)
  > why: standard platformer mapping, accessible and intuitive

## Contracts

- :contract: Game runs at 60fps with fixed timestep
- :contract: All positioning uses 16x16px grid alignment
- :contract: Canvas resolution exactly 800x600px
- :contract: No external dependencies (pure JS/HTML5)

<!-- code: none | yap: none | timestamp -->

<!-- code: 0529d882c88be277 | yap: 413fad19f12d0cde | 2026-01-11 03:46 -->
