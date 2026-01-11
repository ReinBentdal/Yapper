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

- conversation history persistence (decided: human - bug fix)
  > intent: maintain context across interactions
  > why: agent was losing context between messages
  > fix: maintain conversation_history across run() calls

- interactive command mode (decided: human)
  > intent: manage agent session with commands
  > why: need to clear history, check status, mark files
  > commands: `clear`, `changes`, `mark <path>`, `quit`

- always-interactive mode (decided: human)
  > intent: keep conversation going after initial request
  > why: tasks often lead to follow-ups
  > behavior: handle command-line args then enter interactive loop

- concise progress feedback (decided: human)
  > intent: know agent is working without verbose output
  > why: current tool dumps are noisy, hide real progress
  > behavior: show progress indicators, not implementation details

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
  > behavior: agent asks, human responds with thoughts/adjustments/approval

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

## What's Here

### `agent.py`

Main agent implementation.

- `YAPAgent` class - orchestrates everything (renamed from ADLAgent)
- `YAPManager` - finds, reads, writes YAP files (renamed from ADLManager)
- `YAPTracker` - hash computation and change detection (renamed from ADLTracker)
- `FileManager` - file operations with diff display
- `Colors` - terminal coloring
- `TOOLS` - tool definitions for Claude API

> :contract: requires `anthropic` package
> :contract: requires ANTHROPIC_API_KEY env var

### `YAP-SPEC.md`

The Yapper specification document.

- file structure and placement rules
- spec format with intent/why/decided
- conversation flow steps
- marker definitions (:warn:, :contract:, etc.)
- specificity requirements
- strict section enforcement rules

> intent: agents read this to understand how to work with Yapper
> why: self-documenting format

### `AGENT-SYSTEM-PROMPT.md`

Behavioral instructions for the agent.

- core principles (conversation-first, YAP-first)
- the conversation workflow
- how to adapt to human expertise level
- what agent can/cannot do
- example interactions
- strict section enforcement protocol

> intent: shape agent behavior
> why: raw Claude doesn't know Yapper conventions

### Interactive Commands

- `clear` - clear conversation history (decided: human)
  > intent: start fresh conversation
  > why: sometimes need to reset context

- `changes` - show YAP files with pending changes (decided: human)
  > intent: quick status check
  > why: see what needs implementation

- `mark <path>` - mark YAP file as implemented (decided: human)
  > intent: manually update hash without code changes
  > why: sometimes need to force-mark as done

- `quit`/`exit` - exit agent (decided: human)
  > intent: clean exit from interactive mode

### Progress Feedback System

- concise tool indicators with emojis (decided: agent, human approved pending)
  > intent: show what's happening without noise
  > why: current JSON dumps hide real progress
  > examples: "📖 Reading files...", "✏️ Writing code...", "🔍 Analyzing..."

- real-time thinking indicators (decided: agent, human approved pending)
  > intent: show when agent is processing vs waiting
  > why: long API calls look like hanging
  > behavior: "🤖 Thinking..." with optional spinner

- grouped operation display (decided: agent, human approved pending)
  > intent: related operations shown together
  > why: easier to follow multi-step tasks
  > format: operation group → individual steps → final result

- contextual result summaries (decided: agent, human approved pending)
  > intent: show what matters, not implementation details
  > why: users care about outcomes, not internal steps
  > behavior: file changes, YAP updates, discovered issues

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

> :decision: progress over verbosity (decided: agent, human approved pending)
> intent: show meaningful progress, not technical details
> why: verbose tool output clutters the conversation
> trade-off: lose debugging info but gain clarity
> escape: --verbose flag for when debugging needed

## Current State

- Core implementation: Complete
- YAP specification: Complete with strict sections
- Agent system prompt: Needs updating for YAP naming
- Code needs refactoring: ADL→YAP class names and hash format
- Playground examples: Skipped for now (per request)
- Progress feedback: Needs implementation

## Gaps

- no automated testing of YAP-code alignment
- no schema validation for YAP files
- no migration path when YAP format changes
- single-agent only, no multi-agent coordination
- no tab completion in interactive mode
- no session persistence across restarts
- agent code still uses ADL naming internally
- verbose tool output needs condensing
- no progress indicators during long operations
- no grouped operation display
- no --verbose flag for debugging

---
<!-- YAP-HASH: (not yet implemented) -->