# 8-bit Graphics Renderer

Pixel-perfect rendering system for retro aesthetics.

## What This Does

The Renderer class provides:
- Canvas context setup with disabled smoothing for crisp pixels  
- Sky blue background clearing
- Simple colored rectangle drawing (sprite placeholders)
- Rectangle drawing with black borders
- Pixel-perfect positioning (Math.floor for coordinates)

## Key Decisions

- Disable all image smoothing (decided: agent default)
  > why: maintains crisp pixel art aesthetic across all browsers

- Sky blue (#87CEEB) background (decided: agent default)
  > why: classic platformer sky color, good contrast with game elements

- Math.floor all coordinates (decided: agent default)
  > why: ensures pixel-perfect alignment, no blurry sub-pixel rendering

- Simple colored rectangles as placeholders (decided: agent default)
  > why: allows development without sprite assets

## Contracts

- :contract: All coordinates floored to integers for pixel-perfect rendering
- :contract: Image smoothing disabled on canvas context
- :contract: Background cleared to sky blue (#87CEEB) each frame
- :contract: All drawing methods use consistent color format (hex strings)

:warn: Currently using colored rectangles - sprite system not yet implemented

## Depends On

- HTML5 Canvas 2D context
- Browser canvas smoothing properties (vendor prefixed)

## Used By

- game.js creates Renderer with main canvas
- All entities call renderer methods in their render() functions

<!-- code: none | yap: none | timestamp -->

<!-- code: 1f7d295cf5d75aef | yap: af948fd8933b6e62 | 2026-01-11 03:46 -->
