# Player Character

Player character with classic platformer mechanics.

## What This Does

The Player class handles:
- Movement at 120px/sec horizontal speed
- Jumping with 300px/sec initial velocity and gravity
- Shooting dot projectiles at 400px/sec
- Collision detection with enemies, coins, and screen boundaries
- Health system with lives and invulnerability frames
- Screen transition when reaching edges

## Key Decisions

- Movement speed 120px/sec (decided: agent, human approved)
  > why: feels "snappy" for responsive platforming

- Jump velocity 300px/sec with 800px/sec² gravity (decided: agent default)  
  > why: gives good jump arc and control feel

- 16x16 pixel size (decided: agent default)
  > why: matches grid system and retro aesthetic

- Invulnerability frames after taking damage (decided: agent default)
  > why: prevents rapid damage from single enemy contact

## Contracts

- :contract: Player is exactly 16x16 pixels
- :contract: Movement speed exactly 120px/sec horizontal
- :contract: Jump speed exactly 300px/sec initial velocity
- :contract: Dots travel at 400px/sec, disappear at screen edge
- :contract: 1 second invulnerability after taking damage

## Depends On

- physics.js (Physics class for collision detection)

## Used By  

- game.js creates and updates Player instance
- enemies.js checks collision with player
- world.js handles screen transitions based on player position

<!-- code: none | yap: none | timestamp -->

<!-- code: 029c65e2055ff147 | yap: 3902896f1b33cef8 | 2026-01-11 03:44 -->
