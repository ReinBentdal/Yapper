# Yapper

Conversation-based alignment layer for agent-assisted codebases. Makes code navigable and maintainable when agents do the coding.

## Yap Here
<!-- All implemented -->

## Quick Map

- `agent.py` - main implementation (YapAgent, YapManager, FileManager, tools)
- `project.yap` - project-level context (you are here)
- `agent.yap` - architectural context for agent.py
- `YAP-SPEC.md` - the yap format specification

## What This Does

Yapper provides a structured way to work with AI coding agents:

1. Human writes intent in `.yap` files
2. Agent reads yap, asks clarifying questions
3. Human and agent agree on specs
4. Agent implements code to match specs
5. System tracks when code drifts from yap

The core insight: agents lack institutional knowledge. YAP files provide that context so any agent can understand and modify code correctly.

## Conventions

- Single-file Python architecture (agent.py contains everything)
- `.yap` files for architectural context, one per relevant code file
- Hash tracking to detect code/yap drift
- Streaming API responses for real-time feedback
- Interactive CLI with conversation persistence

## Key Decisions
- .yap extension with per-file naming (decided: human)
  > why: cleaner, file association is obvious (agent.yap → agent.py)

- Per-file yap instead of per-directory (decided: human)
  > why: more precise mapping, easier to track drift

- Code hash tracking (decided: human)
  > why: detect when code changes without yap review

- Single agent.py file (decided: human)
  > why: simplicity, easy to understand entire system

- Streaming responses (decided: human)
  > why: immediate feedback during long operations

- Reference system with auto-clearing across turns (decided: human)
  > intent: prevent context bloat and agent slowdown
  > why: persistent references accumulate causing performance issues
  > decided: human

## Contracts

- Requires Python 3.10+
- Requires ANTHROPIC_API_KEY environment variable
- All paths relative to project root
- .yap files only modified via yap-specific tools
- .yapignore protects sensitive files from agent access

## Depends On

- anthropic (Claude API)
- python-dotenv (environment loading)

<!-- code: 19c928238624733c | yap: 9b1597980ca98d22 | 2026-01-11 05:03 -->
