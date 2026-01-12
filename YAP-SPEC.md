# YAP Specification

Version: 1.0

## Purpose

YAP files make agent-assisted codebases **scalable and navigable**. Unlike human developers who accumulate institutional knowledge, agents start fresh. YAP files provide the context needed for any agent (or human) to understand and modify code correctly.

## Golden Rules

1. **YAP FIRST, THEN CODE** - Agent must agree on specs in .yap files with human BEFORE writing any code
2. **HUMAN APPROVAL REQUIRED** - Agent proposals are always pending until human explicitly approves
3. **CLEAR ATTRIBUTION** - Every decision marked as `human`, `agent, human approved`, or `conversation`

## Core Principles

- **Context for agents** - what this code does, why it works this way, what must stay true
- **Track decisions** - who decided what, so changes can be made intelligently
- **Detect drift** - know when code changes without architectural review
- **One-way flow** - yap first, then code (but agent can propose yap changes after reading code)

## File Structure

```
project/
├── project.yap          # Project-level context
├── agent.yap            # YAP for agent.py
├── src/
│   ├── auth.yap         # YAP for auth.py (or auth/ directory)
│   └── utils.yap        # YAP for utils.py
```

**Naming:** `<name>.yap` corresponds to `<name>.py` (or `<name>/` directory).

**Scope:** A `.yap` file describes its corresponding code file or directory.

## Hash Tracking

Every `.yap` file ends with:

```
<!-- code: abc123 | yap: def456 | 2024-01-15 14:30 -->
```

- `code`: SHA256 hash of the associated code file(s)
- `yap`: SHA256 hash of the yap content (excluding this line)
- Timestamp of last sync

**On startup, warn if:**
- Code hash changed but yap hash didn't → code modified without yap review
- Yap hash changed but not marked implemented → pending architectural changes

## Sections

### For all `.yap` files

#### Yap Here
Working space for human thoughts, agent conversation, and **implementation state**.

**Implementation state tracking:**
- If all specs are implemented: `<!-- All implemented -->`
- If nothing is implemented: `<!-- Not implemented -->`
- If partial: list specific pending items

```markdown
## Yap Here

<!-- Pending implementation:
- [ ] RateLimiter class
- [ ] Integration with login endpoint
-->

- thinking about splitting this into smaller functions
- the error handling feels inconsistent

<!-- AGENT: Should I propose restructuring the validation logic? -->
```

When agent marks yap as implemented, it clears pending items and updates to `<!-- All implemented -->`.

#### What This Does
Architectural purpose - what capability this provides, not implementation details.

```markdown
## What This Does

Orchestrates conversation between human and AI agent. Manages tool execution,
tracks YAP files, and maintains conversation context across turns.
```

#### Key Decisions
Important choices with attribution.

```markdown
## Key Decisions

- Streaming API responses (decided: human)
  > why: immediate feedback during long responses

- 100-line read limit (decided: conversation)
  > why: prevents token explosion, forces pagination

- Hash tracking in file footer (decided: agent, human approved)
  > why: simpler than external cache, self-contained
```

#### Contracts
What must be true. Specific and verifiable.

```markdown
## Contracts

- Requires ANTHROPIC_API_KEY env var
- All file paths resolved relative to project root
- YAP files only modified via yap-specific tools
```

#### Depends On / Used By
Relationships to other modules.

```markdown
## Depends On

- anthropic (Claude API client)
- python-dotenv (env loading)

## Used By

- CLI entry point (main)
```

### Additional sections for `project.yap`

#### Quick Map
Brief guide to codebase structure.

```markdown
## Quick Map

- agent.py - main agent implementation
- project.yap - you are here
```

#### Conventions
Project-wide rules.

```markdown
## Conventions

- All errors extend base AppError class
- Config via environment variables
- No external state beyond file system
```

## Markers

Use in Key Decisions or Contracts:

| Marker | Purpose |
|--------|---------|
| `:warn:` | Gotcha, non-obvious behavior |
| `:contract:` | Must be true, enforced |
| `:decision:` | Explicit choice made |

Example:
```markdown
- :warn: Rate limits pause execution with countdown
- :contract: Never write to files outside project root
- :decision: Single-file architecture over package structure
```

## Attribution

Every decision MUST note who made it. This is critical for understanding why code works the way it does.

**For approved decisions (in permanent sections):**

| Value | Meaning |
|-------|---------|
| `human` | Human specified directly |
| `agent, human approved` | Agent proposed, human explicitly agreed |
| `conversation` | Back-and-forth discussion led to this |
| `agent (default)` | Technical default, low importance |

**For pending proposals (in Yap Here):**

```markdown
<!-- AGENT PROPOSAL (pending approval):
- Use token bucket for rate limiting
  > why: allows burst while enforcing average
  > decided: agent, human approved (PENDING)
-->
```

Agent CANNOT move proposals to permanent sections or implement code until human says "approved", "yes", "looks good", or similar explicit confirmation.

## Workflow

The workflow is **conversational**, not linear. Agent and human go back and forth until there's clarity and agreement.

```
┌─────────────────────────────────────────────────────┐
│                  CONVERSATION LOOP                   │
│                                                     │
│  Human writes thoughts  ←→  Agent asks questions   │
│  Agent proposes specs   ←→  Human refines/approves │
│  Agent implements       ←→  Human reviews/adjusts  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Key principle:** The agent can implement code, then return to discussion. It's iterative, not one-way.

**What requires approval before doing:**
- Moving specs to permanent sections
- First implementation of a new feature

**What can happen during iteration:**
- Agent implements something → human reviews → discussion → agent adjusts
- Agent reads code → notices issue → proposes yap change → human approves → agent updates

**Marking completion:**
When specs are agreed and code matches: `<!-- All implemented -->`

**Agent can also propose yap changes after reading code:**
- Notices code has grown/changed significantly
- Suggests new `.yap` files for new modules
- Proposes restructuring existing yap

## Iteration Limits

The agent has a limited number of tool calls per conversation turn. When approaching the limit:

1. **Wrap up current work** - finish the immediate task cleanly
2. **Save state in Yap Here** - note what's done and what's pending
3. **Return to human** - summarize progress and ask how to proceed

Don't leave work half-done. If you can't finish, document where you stopped.

## Agent Protocol

**NEVER write code without yap approval:**
1. Read relevant `.yap` file(s)
2. If changes needed, propose in Yap Here with `<!-- AGENT PROPOSAL (pending): -->`
3. WAIT for human to approve
4. Only then implement

**All agent suggestions must be clearly marked:**
```markdown
<!-- AGENT PROPOSAL (pending approval):
- Feature X
  > why: reasoning
  > decided: agent, human approved (PENDING)
-->
```

**After reading code (can propose without approval):**
1. If code diverged from yap, flag it
2. If restructuring needed, propose yap changes
3. Can suggest creating new `.yap` files

**Tools:**

*YAP Operations:*
- `read_yap_chain` - read all relevant .yap files for a path
- `read_yap_section` / `write_yap_section` - targeted edits
- `update_yap` - full file update
- `mark_yap_implemented` - update hashes after sync
- `clear_yap_here` - clear working section after implementation

*Implementation Tracking:*
- `get_implementation_status` - see status of all .yap files
- `add_pending_task` - add task to .yap's Yap Here section
- `complete_pending_task` - mark a task done

*File Operations:*
- `read_file` / `edit_file` / `write_file` - code files only (blocked for .yap)
- `search_files` - search code content with regex
- `remove_file` - delete files (blocked for .yap)
- `list_functions` - list functions in Python/JS/TS files

*Shared Tools:*
- `list_directory` - see project structure

## Minimal Valid `.yap`

```markdown
# Module Name

One sentence describing what this does.
```

That's it. Everything else is optional enhancement.
