# World and Level Management

Screen-based world system with level data and transitions.

## What This Does

The World class manages:
- Screen-based level progression (not continuous scrolling)
- Level data structure defining enemies and coins per screen
- Screen transition logic when player reaches edges
- Coin collection and scoring system
- Current screen tracking and data retrieval

The Coin class handles:
- Individual coin collectibles with 8x8 size
- Simple spinning animation with color brightness changes
- Collision detection with player for collection

## Key Decisions

- Screen-based world instead of scrolling (decided: conversation)
  > why: focuses on exploration, simpler than continuous scrolling

- Level data as nested arrays (decided: agent default)
  > why: simple structure: screens[screenIndex] = { enemies: [], coins: [] }

- Coins are 8x8 pixels (decided: agent default)
  > why: smaller than entities (16x16), easy to collect

- Screen transitions at exact edges (decided: agent default)
  > why: clear boundaries, no partial screen overlap

## Contracts

- :contract: Each screen exactly 800x600 pixels
- :contract: Player transitions at x < 0 (left) or x >= 800 (right)
- :contract: Coins are 8x8 pixels and centered when collected
- :contract: Screen data format: { enemies: [positions], coins: [positions] }
- :contract: Screen indices start at 0, increment going right

## Depends On

- physics.js for collision detection with coins

## Used By

- game.js calls loadCurrentScreen() and getScore()
- player.js triggers screen transitions
- enemies.js gets enemy spawn data from current screen

<!-- code: none | yap: none | timestamp -->

<!-- code: 34d6a852f75bf530 | yap: fb656be9f1723dce | 2026-01-11 03:46 -->
