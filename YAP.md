# Yapper

A conversation-based alignment layer between humans and AI coding agents. Yapper turns messy human intent into specific, trackable specs through dialogue - then ensures code matches those specs.

## Yap Here

<!--
Yap yap, write down your thoughts here and the agent will take care of it..
-->

- this started because AI coding makes codebases messy fast
- agents don't have context, they reinvent wheels, they don't explain themselves
- wanted something where I stay in control but agent does the heavy lifting
- the key insight: make the spec the conversation, not just the output

make the command updates more useful. More concise and with real-time updates such to know that the agent is working etc

### Agent Working State
<!-- Temporary implementation status, gaps, next steps -->
- **Implementation Status**: Core implementation complete and fully functional, hash-based change tracking implemented, streaming API calls working, interactive command mode complete, guided initialization complete, progress feedback implemented, comprehensive error handling, CLI interface complete, section-specific YAP tools (`read_yap_section`/`write_yap_section`) implemented, file operations blocked for YAP files to enforce structure, prompt caching enabled, real-time token streaming, 100-line read limit with pagination, `edit_file` tool for search/replace editing, compact diff summaries
- **Active Gaps**: no automated testing of YAP-code alignment, no schema validation for YAP files, no migration path when YAP format changes, single-agent only (no multi-agent coordination), no tab completion in interactive mode, no session persistence across restarts, no --verbose flag for debugging tool execution, no progress spinners during long API calls, no configuration file support (only CLI args), no plugin system for custom tools, no integration with version control systems, no metrics/analytics on YAP usage patterns
- **Next Steps**: focus on user experience improvements (tab completion, session persistence, --verbose flag), then consider testing infrastructure and validation tools

## Quick Map

- `agent.py` - Main agent implementation
- `YAP-SPEC.md` - The Yapper specification document  
- `AGENT-SYSTEM-PROMPT.md` - Behavioral instructions for the agent
- `playground/` - Example projects demonstrating Yapper in practice

## Global Conventions

- YAP files named `YAP.md` throughout codebase (decided: human)
  > intent: clear naming, avoid confusion with other markdown files
  > why: YAP is the format name, should be in filename

- strict section enforcement (decided: human)
  > intent: consistent structure across all YAP files
  > why: agents can parse reliably, humans know what to expect
  > rule: only sections defined in YAP-SPEC.md are allowed

- stateless YAP structure except "Yap Here" (decided: human)
  > intent: separate permanent architecture from temporary working state
  > why: keeps YAP files stable while allowing dynamic work tracking
  > rule: only "Yap Here" section contains temporary state, implementation status, gaps

- conversation history persistence (decided: human - bug fix)
  > intent: maintain context across interactions
  > why: agent was losing context between messages
  > fix: maintain conversation_history across run() calls

- interactive command mode (decided: human)
  > intent: manage agent session with commands
  > why: need to clear history, check status, mark files
  > commands: `clear`, `changes`, `mark <path>`, `quit`/`exit`

- always-interactive mode (decided: human)
  > intent: keep conversation going after initial request
  > why: tasks often lead to follow-ups
  > behavior: handle command-line args then enter interactive loop

- real-time streaming output (decided: human)
  > intent: see agent responses as they're generated
  > why: long responses felt unresponsive
  > behavior: stream text to terminal during API calls

- concise tool feedback (decided: human)
  > intent: show tool usage without noise
  > why: verbose JSON dumps cluttered conversation
  > behavior: compact summaries with status indicators

- automatic .env API key setup (decided: human)
  > intent: smooth onboarding experience
  > why: reduces friction for new users
  > behavior: prompt for key and save to .env if missing

## Architecture Decisions

- markdown format (decided: conversation)
  > intent: easy for humans, parseable for agents
  > why: renders everywhere, no syntax errors, feels like notes
  > alternatives: started with YAML, too rigid and form-like

- scattered files not monolith (decided: human)
  > intent: each YAP.md lives with its code
  > why: locality matters, don't want one giant file
  > rule: YAP.md describes its directory and subdirs unless child has own YAP

- "Yap Here" section for human stream-of-consciousness (decided: conversation)
  > intent: low-friction place to dump thoughts
  > why: agent reads for context, structures into specs below
  > constraint: agent NEVER deletes or modifies human yaps without permission

- agent must ask before adding `decided: human` (decided: human - critical rule)
  > intent: never put words in human's mouth
  > why: agent was assuming human intent, caused misattribution
  > history: agent kept marking things [H] without asking, broke trust

- specs need intent/why/decided (decided: conversation)
  > intent: reasoning is as important as the spec itself
  > why: future readers (human or agent) need to understand the "why"
  > benefit: enables informed changes, prevents blind modifications

- no vague specs (decided: conversation)
  > intent: ":contract: requires modern browser" is useless
  > why: can't verify, can't act on it
  > rule: must be specific enough that someone knows exactly what to check

- conversational approval process (decided: human)
  > intent: humans respond naturally instead of Y/n
  > why: more natural than binary choices, allows for nuanced feedback
  > behavior: agent asks questions, human responds conversationally

- hash-based change tracking (decided: conversation)
  > intent: know which YAP files have pending changes
  > why: on startup, show what needs implementation
  > format: `<!-- YAP-HASH: abc123 | implemented: 2024-01-15 14:30 -->`
  > history: originally considered separate cache folder, hash in file is simpler

- rate limit handling with pause/retry (decided: human)
  > intent: don't crash on rate limits
  > why: agent was dying mid-task, losing all progress
  > behavior: pause with countdown, Ctrl+C to cancel gracefully

- git-style diffs for changes (decided: human)
  > intent: make changes obvious and reviewable
  > why: colored +/- lines familiar from git, easy to scan

- guided initialization for new projects (decided: conversation)
  > intent: help onboard projects without YAP
  > why: cold start problem - how do you document undocumented code?
  > flow: discover code dirs, go one by one, conversational

- streaming API calls (decided: human)
  > intent: show progress during long responses
  > why: agent felt unresponsive during API calls
  > behavior: real-time text streaming to terminal

## Extension Guidelines

> :extends: add new tools in TOOLS list
> :extends: add new markers beyond :warn:/:contract:/:decision:
> :extends: support other LLM providers beyond Claude
> :extends: add web UI for YAP editing
> :extends: add YAP linting/validation tool
> :extends: add tab completion for interactive commands
> :extends: add session save/restore
> :extends: add --verbose flag for detailed tool output
> :extends: add progress spinners for long operations

## What'S Here
### `agent.py`

Main agent implementation with full YAP workflow support.

#### Core Classes

- `YapAgent` - orchestrates entire conversation and tool execution
- `YapManager` - finds, reads, writes, and tracks YAP files
- `YapTracker` - hash computation and change detection for implementation status
- `FileManager` - file operations with diff display and caching
- `YapIgnore` - yapignore file parsing and protection checking
- `Colors` - terminal coloring with TTY detection
- `AgentConfig` - configuration dataclass

> :contract: requires `anthropic` and `python-dotenv` packages
> :contract: requires ANTHROPIC_API_KEY env var or creates .env interactively

#### File Protection System

Yapignore mechanism to protect sensitive files from all agent operations:

- `.yapignore` file uses gitignore syntax and patterns
- blocks all file operations (`read_file`, `edit_file`, `write_file`) on protected files
- project-wide protection with clear error messages
- integrates with existing YAP.md blocking system

> :contract: uses same pattern syntax as gitignore (glob patterns, negation, comments)
> :warn: blocks ALL file operations on protected files, including reads
> :contract: `.yapignore` applies to entire project from root directory

**Default protection patterns:**
- `.env*` - environment files with secrets
- `*.key`, `*.pem` - cryptographic keys
- `__pycache__/` - Python cache directories
- `node_modules/` - dependency directories
- `*.log` - log files
- `.git/` - version control metadata

> :decision: use gitignore syntax
> intent: familiar pattern matching that developers already know
> why: gitignore patterns are well-documented, handles complex cases like negation
> decided: conversation

> :decision: block ALL file operations, not just writes
> intent: complete protection of sensitive files
> why: even reading protected files could leak sensitive info or violate security
> decided: conversation

> :decision: yapignore applies project-wide, not per-directory
> intent: single source of truth for protected files
> why: simpler to manage, clearer security boundary
> decided: conversation

#### Tool System

Complete set of tools for YAP-based development:

**File Operations:**
- `read_file` - reads files with optional line ranges (100 line max, **blocked for YAP files and yapignore protected**)
- `file_info` - metadata without reading content (**respects yapignore protection**)
- `search_files` - regex search across codebase (**respects yapignore protection**)
- `edit_file` - search/replace editing (**blocked for YAP files and yapignore protected**)
- `write_file` - creates new files (**blocked for YAP files and yapignore protected**)
- `list_directory` - lists directory contents

**YAP Operations:**
- `read_yap_chain` - reads full YAP hierarchy for any path
- `read_yap_section` - reads specific section from YAP file (efficient, low token cost)
- `write_yap_section` - writes/updates specific section in YAP file (enforces structure)
- `update_yap` - updates entire YAP file content
- `mark_yap_implemented` - marks YAP as implemented (hash update)
- `clear_yap_here` - clears "Yap Here" section after implementation
- `task_complete` - signals completion with summary

> :contract: all tools work relative to project root
> :contract: file operations show diffs automatically
> :contract: `read_file`/`write_file`/`edit_file` blocked for YAP files - use section-specific tools
> :contract: all file operations respect yapignore protection
> :warn: tools can fail with exceptions, agent handles gracefully

#### API Integration

- streaming responses with real-time display
- rate limit handling with countdown and graceful cancellation
- ephemeral caching for system prompt efficiency
- tool use validation and error handling

> :contract: uses Claude Sonnet 4 by default
> :warn: rate limits pause execution with visible countdown
> :contract: max 30 tool iterations per conversation turn

#### Interactive Mode

Command-line interface with session management:

- `clear` - clears conversation history
- `changes` - shows YAP files with pending changes  
- `mark <path>` - manually marks YAP as implemented
- `quit`/`exit` - exits cleanly

> :contract: always enters interactive mode after initial request
> :contract: Ctrl+C during rate limit gracefully cancels

#### Initialization System

Guided YAP creation for existing codebases:

- automatically discovers code directories
- recommends YAP.md locations based on file patterns
- conversational YAP creation with human approval
- skippable per-location with "skip all" option

> :contract: scans for common code extensions (.py, .js, .ts, etc.)
> :contract: suggests YAP.md in directories with multiple code files

#### Progress Feedback

Concise tool execution feedback:

- compact tool summaries instead of verbose JSON
- status indicators (✓, ✗, →)
- grouped operations display
- real-time streaming text

> intent: show progress without clutter
> why: verbose tool dumps obscured actual progress
> behavior: "→ read file.py (123 lines)" instead of full JSON

#### Hash-Based Change Tracking  

YAP implementation status via content hashing:

- computes SHA256 hash of YAP content (excluding hash footer)
- stores hash and timestamp in file footer
- detects changes by comparing stored vs current hash
- startup shows pending changes across all YAP files

> format: `<!-- YAP-HASH: abc123 | implemented: 2024-01-15 14:30 -->`
> :contract: hash excludes the hash comment itself
> :contract: shows "never implemented" for YAPs without hash

### CLI Arguments

- `request` - initial task (optional, enters interactive mode after)
- `--project` / `-p` - project root directory (default: current)
- `--model` / `-m` - Claude model (default: claude-sonnet-4-20250514)
- `--init` - guided YAP initialization mode
- `--no-color` - disables terminal colors

> :contract: always enters interactive mode even with initial request
> :contract: auto-detects TTY for color support

### Error Handling

Comprehensive error handling throughout:

- missing dependencies prompt installation
- API key setup if missing
- file not found errors
- rate limit recovery
- KeyboardInterrupt handling
- tool execution errors
- yapignore protection violations

> :warn: exits cleanly on missing anthropic/dotenv packages
> :contract: creates .env file if ANTHROPIC_API_KEY missing
> :contract: graceful cancellation during rate limit waits
> :contract: clear error messages when yapignore blocks file access

### YAP-SPEC.md

The Yapper specification document defining the format and workflow.

- file structure and placement rules
- spec format with intent/why/decided  
- conversation flow steps
- marker definitions (:warn:, :contract:, etc.)
- specificity requirements
- strict section enforcement rules
- stateless design with "Yap Here" for temporary state

> intent: agents read this to understand how to work with Yapper
> why: self-documenting format ensures consistency

### AGENT-SYSTEM-PROMPT.md

Behavioral instructions for the agent defining conversation patterns.

- core principles (conversation-first, YAP-first)
- the conversation workflow from vague to specific
- how to adapt to human expertise level
- what agent can/cannot do autonomously  
- example interactions and edge cases
- strict section enforcement protocol
- stateless YAP management

> intent: shape agent behavior beyond technical YAP format
> why: raw Claude doesn't know Yapper conversation patterns

## Key Decisions

> :decision: YAP is a conversation artifact, not documentation (decided: conversation)
> intent: capture the dialogue that produces aligned code
> why: the conversation IS the spec - human intent refined through Q&A
> history: started as "documentation format", evolved to "alignment layer"

> :decision: vague in, specific out (decided: conversation)
> intent: humans can yap loosely, agent structures it
> why: reduces friction for humans while maintaining precision
> history: early versions required too much structure upfront

> :decision: all changes flow through YAP (decided: conversation)
> intent: human reviews YAP changes, not code changes
> why: if YAP is right, code follows - easier to verify intent than implementation

> :decision: free-form human responses (decided: human)
> intent: humans respond naturally, not just Y/n
> why: humans think in sentences, not binary choices
> behavior: agent asks questions, human responds conversationally

> :decision: bidirectional insight (decided: conversation)
> intent: agent reads both YAP and code to reason
> why: code reveals reality, YAP reveals intent - both needed
> constraint: but all CHANGES commit through YAP first

> :decision: real-time progress over perfect logs (decided: human)
> intent: show meaningful progress during execution
> why: verbose tool output cluttered the conversation
> trade-off: lose debugging detail but gain clarity and responsiveness

> :decision: streaming API responses (decided: human)  
> intent: immediate feedback during long responses
> why: waiting for complete response felt unresponsive
> behavior: text appears as generated, tools summarized after

> :decision: automatic environment setup (decided: human)
> intent: reduce friction for new users
> why: manual API key setup was a common failure point
> behavior: prompt for key and create .env if missing

> :decision: stateless YAP files except "Yap Here" (decided: human)
> intent: separate permanent architecture from temporary working state
> why: keeps YAP files stable while allowing agent to track active work
> rule: "Current State" and "Gaps" sections removed, content moves to "Yap Here → Agent Working State"

> :decision: section-specific YAP tools over full file operations (decided: human)
> intent: efficient, structure-enforcing YAP file editing
> why: reading/writing entire YAP files wastes tokens and risks structure violations
> behavior: `read_yap_section`/`write_yap_section` for targeted operations, `read_file`/`write_file`/`edit_file` blocked for YAP files

---
<!-- YAP-HASH: edf48fe11bdfb020 | implemented: 2026-01-11 02:00 -->
