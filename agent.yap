# Agent

Main Yapper implementation. Orchestrates conversation between human and AI agent, manages yap files, executes tools, and enforces the yap-first workflow.

## Yap Here
<!-- All implemented -->

## What This Does

Single-file agent that implements the YAP workflow: specs first, then code.

### Core Components

**YapAgent** - Main orchestrator
- Manages conversation with Claude API (streaming)
- Executes tools and tracks token usage
- Builds system prompt with YAP spec

**YapManager** - Yap file operations
- Finds and reads .yap files in project
- Section-level read/write operations
- Maps code files to their .yap counterparts
- Tracks pending implementation tasks

**YapTracker** - Change detection
- Computes hashes for yap content and associated code
- Detects drift between code and yap specs
- Stores hash footer in each .yap file

**FileManager** - Code file operations
- Read/write/edit code files
- Search with regex
- List functions in Python/JS/TS files
- Respects .yapignore protection

**YapIgnore** - File protection
- Parses .yapignore (gitignore syntax)
- Blocks agent access to sensitive files
- Protects directories and their contents

### Tool Categories

*YAP Tools* - read_yap_chain, read_yap_section, write_yap_section, update_yap, mark_yap_implemented, clear_yap_here, get_implementation_status, add_pending_task, complete_pending_task

*Code Tools* - read_file, file_info, search_files, edit_file, write_file, remove_file, list_functions

*Shared Tools* - list_directory, task_complete

### CLI

Interactive REPL with commands: clear, changes, mark, quit

## Key Decisions

- Single-file architecture (decided: human)
  > why: simplicity, entire system in one place

- Per-file yap mapping (decided: human)
  > why: clear 1:1 relationship between specs and code

- Streaming API responses (decided: human)
  > why: real-time feedback during agent work

## Contracts

- :contract: ANTHROPIC_API_KEY must be set
- :contract: All paths resolved relative to project root
- :contract: .yap files only modified via yap tools (read_file/edit_file blocked)
- :contract: .yapignore blocks ALL file operations on matched paths

- :warn: Rate limits pause execution with countdown
- :warn: File edits require exact string match
- :warn: list_functions works for Python and JS/TS only

## Depends On

- anthropic - Claude API client
- python-dotenv - env file loading
- hashlib, difflib, ast, re, fnmatch - stdlib

## Used By

- CLI entry point (main function)
- Can be imported as library

<!-- code: 3f4bef60fbfb4956 | yap: ecd98c978b7c750d | 2026-01-11 20:04 -->
