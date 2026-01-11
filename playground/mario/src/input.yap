# Input Handling

Keyboard input system for retro platformer controls.

## What This Does

The Input class manages:
- Keyboard event listening (keydown/keyup)
- Key state tracking (currently held vs just pressed)
- Arrow key movement detection
- X key for shooting action
- Clean press detection to avoid repeated actions

## Key Decisions

- Use event.code instead of event.key (decided: agent default)
  > why: consistent across different keyboard layouts

- Track both current and previous key states (decided: agent default)
  > why: enables "just pressed" detection for single-shot actions like jumping

- Single Input instance for entire game (decided: agent default)
  > why: avoids multiple event listeners, centralized input state

## Contracts

- :contract: Arrow keys (ArrowLeft, ArrowRight, ArrowUp, ArrowDown) for movement
- :contract: X key (KeyX) for shooting
- :contract: isPressed() returns true only on frame when key first pressed
- :contract: isDown() returns true while key is held

## Depends On

- Browser KeyboardEvent API
- Document event listeners

## Used By

- game.js passes input to player for movement/shooting
- player.js checks input state each frame

<!-- code: none | yap: none | timestamp -->

<!-- code: a83c5ec28b69df12 | yap: a5d3b48e85ec85d1 | 2026-01-11 03:46 -->
