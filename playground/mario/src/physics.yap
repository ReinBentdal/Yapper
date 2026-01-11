# Physics and Collision System

Basic collision detection and movement physics for 2D platformer.

## What This Does

The Physics class provides static utility methods for:
- AABB (Axis-Aligned Bounding Box) collision detection
- Gravity application and velocity integration  
- Horizontal movement with deltaTime
- Screen boundary constraint enforcement
- Ground collision detection (Y-axis floor)

## Key Decisions

- Static utility class (decided: agent default)
  > why: physics functions don't need instance state, just pure calculations

- AABB collision only (decided: agent default)
  > why: simple rectangles sufficient for retro platformer, fast detection

- Immediate velocity changes on collision (decided: agent default)
  > why: no complex physics simulation needed, instant response feels better

- Screen boundary hard constraints (decided: agent default)
  > why: prevent entities from leaving visible area

## Contracts

- :contract: All collision rectangles have x, y, width, height properties
- :contract: Gravity always applied downward (positive Y direction)
- :contract: Screen boundaries at (0,0) to (screenWidth, screenHeight)
- :contract: Ground collision stops downward velocity and sets onGround=true

## Depends On

- Entity objects with position (x,y) and velocity (velocityX, velocityY) properties

## Used By

- player.js for movement, jumping, and collision
- enemies.js for basic collision detection
- Any entities needing physics simulation

<!-- code: none | yap: none | timestamp -->

<!-- code: 4ac8b4187e79854d | yap: 991769d235536401 | 2026-01-11 03:46 -->
