# Enemy AI System

Simple enemy entities with patrol behavior.

## What This Does

The Enemy class provides:
- Basic enemy entities with 16x16 size
- Simple patrol AI moving left/right within defined bounds
- Physics with gravity and ground collision
- Speed of 60px/sec (half of player speed)
- Collision detection with player dots (gets destroyed)

The EnemyManager class handles:
- Spawning enemies based on screen data
- Updating all enemies each frame
- Rendering all active enemies
- Managing enemy lifecycle (creation/destruction)

## Key Decisions

- Enemy speed 60px/sec (decided: agent, human approved)
  > why: slower than player (120px/sec) so player can outrun/outmaneuver

- Patrol AI with fixed bounds (decided: agent, human approved)
  > why: predictable behavior fitting exploration focus

- Enemies destroyed by player dots (decided: agent default)
  > why: simple combat mechanic, gives dots purpose

- 16x16 size matching player (decided: agent default)
  > why: consistent collision boxes, symmetric combat

## Contracts

- :contract: Enemies are exactly 16x16 pixels
- :contract: Move at exactly 60px/sec horizontal speed
- :contract: Turn around at patrol boundaries (startX to startX + patrolWidth)
- :contract: Destroyed when hit by player dot
- :contract: Apply gravity and ground collision like player

## Depends On

- physics.js for collision detection and movement

## Used By

- game.js creates EnemyManager and calls update/render
- player.js checks collision with enemies for damage
- world.js provides enemy spawn positions per screen

<!-- code: none | yap: none | timestamp -->

<!-- code: c09c1ecefd284d56 | yap: 7a708885bdd97cc9 | 2026-01-11 03:46 -->
