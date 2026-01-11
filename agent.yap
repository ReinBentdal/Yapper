# Agent

Main Yapper implementation. Orchestrates conversation between human and AI, manages yap files, executes tools, tracks changes.

## Yap Here
<!-- All implemented -->

## What This Does

### Core Classes

**YapAgent** - Main orchestrator
- Builds system prompt with yap spec
- Manages conversation history
- Calls Claude API with streaming
- Executes tools and handles responses
- Tracks token usage
- Mode system (YAP_MODE/CODE_MODE) with user-approval for switching

**YapManager** - Yap file operations
- Finds all .yap files in project
- Reads/writes yap content
- Section-level read/write for efficiency
- Hash computation and change detection
- Determines which yap applies to which code

**YapTracker** - Hash-based change tracking
- Computes SHA256 of yap content
- Computes SHA256 of associated code files
- Detects drift between code and yap
- Stores hashes in yap file footer

**FileManager** - Code file operations
- Read with line limits (100 max)
- Search with regex
- Edit via search/replace
- Write new files
- List functions in Python and JS/TS files
- Respects .yapignore protection

**YapIgnore** - File protection
- Parses .yapignore (gitignore syntax)
- Blocks all operations on protected files
- Default patterns for secrets, caches, etc.

**ReferenceStore** - Token efficiency
- Stores tool outputs as numbered refs
- Select refs to include in context
- Keeps conversation lean

### Tool System

File tools: read_file, file_info, search_files, edit_file, write_file, remove_file, list_directory, list_functions

Yap tools: read_yap_chain, read_yap_section, write_yap_section, update_yap, mark_yap_implemented, clear_yap_here

Implementation tracking: get_implementation_status, add_pending_task, complete_pending_task

Reference tools: list_refs, select_refs, deselect_refs, get_ref

Mode tools: switch_mode

### CLI

Interactive mode with commands: clear, changes, refs, mark, quit

## Key Decisions

- Mode system with YAP_MODE and CODE_MODE (decided: human)
  > intent: enforce yap-first workflow through tool restrictions
  > why: agent was jumping straight to code without proper spec conversation

- Mode switching requires user approval (decided: human)
  > intent: human gates all mode transitions
  > why: prevents agent from self-approving implementation starts
  > how: switch_mode creates pending request, user must say yes/no

- YAP_MODE restricts code access (decided: human)
  > intent: agent must work from yap documentation, not dig through code
  > why: forces proper yap-first workflow, only list_directory available for structure

- Single-file architecture (decided: human)
  > why: simplicity, easy to understand entire system

- Per-file YAP mapping (decided: human)
  > why: clear 1:1 relationship, easier drift tracking

- Streaming responses (decided: human)
  > why: real-time feedback during agent work

- Reference system for token efficiency (decided: human)
  > why: store tool outputs as refs, select into context as needed

- Tool iteration limit ~30 calls per turn (decided: human)
  > why: prevent runaway execution, force clean breaks

- YapIgnore for sensitive file protection (decided: human)
  > why: agents shouldn't read .env files, API keys, etc.

## Contracts

- :contract: ANTHROPIC_API_KEY must be set
- :contract: All paths resolved relative to project root
- :contract: .yap files only modified via yap tools (read_file/write_file blocked)
- :contract: .yapignore blocks ALL file operations on matched files
- :contract: Max 30 tool iterations per conversation turn
- :contract: Max 100 lines per read_file call
- :contract: Mode switches require user approval (pending until confirmed)

- :warn: Rate limits pause execution (not fail)
- :warn: File edits require exact string match (no fuzzy)
- :warn: list_functions works for Python and JS/TS files only

## Depends On

- anthropic - Claude API client
- python-dotenv - env file loading
- hashlib, difflib, ast - stdlib

## Used By

- CLI entry point (main function)
- Could be imported as library

<!-- code: 4b37efdc3546a07b | yap: 24e355c6f3005d4c | 2026-01-11 05:16 -->
