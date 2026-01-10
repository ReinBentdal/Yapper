# Agent Description Language (ADL) Specification

Version: 0.4

## Purpose

ADL is a **conversation artifact** - the record of how human intent becomes specific implementation, with all reasoning preserved.

It serves three roles:

1. **Conversation space** - where vague human intent gets refined into specific specs through dialogue
2. **Agreement record** - the specs that human and agent have aligned on
3. **Reasoning archive** - why decisions were made, so anyone (human, agent, future reader) can understand

Core principles:

- **Intent preserved** - every spec traces back to what the human actually wanted
- **Reasoning visible** - technical choices are justified, not just stated
- **Decision history** - how we got here (human, agent, conversation)
- **No hidden changes** - agent proposes through ADL, human reviews ADL diffs
- **Specificity required** - vague intent in, specific specs out

The goal: **codebases where humans stay in control** even when agents do most of the coding, because the ADL captures the conversation that produced the code.

## How It Works

```
Human has vague intent
        ↓
Human yaps in Notes section
        ↓
Agent asks clarifying questions (in Notes)
        ↓
Back-and-forth until intent is clear
        ↓
Agent proposes specific specs
        ↓
Human approves/edits
        ↓
Specs move to structured sections (with intent, why, decided)
        ↓
Agent implements code to match specs
        ↓
Agent verifies alignment
```

**The human reviews ADL changes, not code changes.** If the ADL is right, the code should follow.

## File Structure

### Location

ADL files are named `ADL.md` and scattered throughout a codebase:

```
project/
├── ADL.md                    # Root: project overview
├── src/
│   ├── ADL.md                # src-level concerns  
│   ├── auth/
│   │   ├── ADL.md            # Auth module documentation
│   │   └── *.ts
│   └── database/
│       ├── ADL.md            # Database module documentation
│       └── *.ts
```

**Scope Rule:** An `ADL.md` describes its directory and all subdirectories, unless a subdirectory has its own `ADL.md` (which takes over).

### Minimal Valid ADL.md

```markdown
# Module Name

One sentence describing what this module does.
```

This is the minimum. A heading and a description. Everything else is optional enhancement.

---

## Document Structure

### Required Sections

#### Title (H1)
The module or project name.

```markdown
# Auth Module
```

#### Description
Immediately after the title. One paragraph minimum explaining what this code does.

```markdown
# Auth Module

Handles user authentication via OAuth and email/password. Manages sessions in Redis.
```

### Optional Sections

All other sections are optional. Their presence indicates documentation maturity. Their absence indicates gaps.

---

## The Human Notes Section

Every ADL.md SHOULD have a "Notes" or "Human Notes" section at the top (after the title and description). This is a freeform space where humans dump thoughts, TODOs, half-formed ideas, and raw information.

```markdown
# Auth Module

Handles user authentication and sessions.

## Yap Here

<!-- 
Human-writable scratchpad. Agent should read this for context but 
restructure the information into proper sections below.
-->

- sarah said we might need to add SAML support Q2
- the refresh token logic is weird, look at oauth.ts line 47
- I think there's a bug when sessions expire during a request
- password hashing uses bcrypt, 12 rounds
- TODO: document the rate limiting stuff
```

**Agent Behavior:** 
- READ this section for context and intent
- DO NOT delete human notes without explicit permission
- Extract actionable information into structured sections below
- Can add to notes if uncertain where something belongs

---

## Standard Sections

These are the conventional sections. Use the ones that apply.

### What's Here

Describes files and their contents.

```markdown
## What's Here

### `oauth.ts`
OAuth flow implementation for Google and GitHub providers.

- `beginOAuth(provider)` → redirects to provider
- `completeOAuth(code)` → exchanges code for tokens, creates session
- `refreshTokens(userId)` → refreshes expired OAuth tokens

### `session.ts`
Session management via Redis.

- `createSession(userId)` → returns session token
- `validateSession(token)` → returns user or throws
- `destroySession(token)` → invalidates session
```

### Depends On

What this module needs to function.

```markdown
## Depends On

- `database/` - user lookups during OAuth
- `redis/` - session storage
- `config/` - OAuth client credentials
```

### Used By

What depends on this module. Critical for understanding blast radius.

```markdown
## Used By

- `api/middleware/auth.ts` - validates sessions on protected routes
- `api/routes/login.ts` - login/logout endpoints
- `jobs/cleanup.ts` - expired session cleanup
```

### Key Decisions

Architectural choices and their rationale.

```markdown
## Key Decisions

> :decision: Redis sessions over JWTs
> Needed instant revocation for enterprise security requirements. JWTs would require a blacklist anyway.

> :decision: 24h session TTL with sliding expiration
> Balance between security and UX. Discussed with security team 2024-01.
```

### Gaps

Explicit acknowledgment of what's missing or incomplete.

```markdown
## Gaps

- Password reset flow exists but isn't documented
- Rate limiting logic needs explanation
- No tests for the refresh token edge cases
```

---

## Convention Markers

Use blockquotes with markers for machine-parseable annotations:

| Marker | Purpose | Example |
|--------|---------|---------|
| `:warn:` | Gotchas, dangers, non-obvious behavior | `> :warn: Mutates input array` |
| `:contract:` | Preconditions, assumptions, requirements | `> :contract: Requires Redis connection` |
| `:todo:` | Known incomplete items | `> :todo: Add input validation` |
| `:decision:` | Design choices with rationale | `> :decision: Using polling for simplicity` |
| `:deprecated:` | Don't use, with alternative | `> :deprecated: Use newFunc() instead` |
| `:extends:` | Extension points for future work | `> :extends: Add new providers in providers/` |

### Be Specific, Not Vague

Markers must be actionable. Avoid ambiguous statements that don't help anyone.

**Bad - vague and useless:**
```markdown
> :contract: Requires modern browser
> :contract: Needs proper configuration
> :warn: May cause issues
> :contract: Must be initialized first
```

**Good - specific and actionable:**
```markdown
> :contract: Requires Canvas API (IE not supported)
> :contract: Requires REDIS_URL env var
> :warn: Throws NetworkError if offline, caller must handle
> :contract: Call init() before any other method
```

**Test for specificity:** Could someone read this and know exactly what to do or check? If not, be more specific.

**For browser/environment requirements**, list actual APIs or features:
```markdown
> :contract: Uses fetch, localStorage, Canvas 2D
> :contract: Node 18+ (uses native fetch)
> :contract: Requires WebGL 2.0 for 3D rendering
```

**For preconditions**, name the actual thing:
```markdown
> :contract: db.connect() must be called first
> :contract: User must be authenticated (req.user exists)
> :contract: Input array must be sorted ascending
```

**For warnings**, describe the actual behavior:
```markdown
> :warn: Returns null if not found (doesn't throw)
> :warn: Mutates input object, clone first if needed
> :warn: Rate limited to 100 req/min, throws RateLimitError
```

Example in context:

```markdown
### `query.ts`

Low-level database query execution.

- `query(sql, params)` → executes parameterized query

> :warn: Never interpolate user input into SQL strings. Always use params array.

> :contract: Assumes connection pool is initialized. Call `initDb()` first.

> :deprecated: `rawQuery()` is deprecated. Use `query()` with params instead.
```

---

## Initiative Tracking

Every significant item (features, decisions, extensions) must be marked with who initiated it:

| Marker | Meaning |
|--------|---------|
| `[H]` | Human initiative - human requested or decided this |
| `[A]` | Agent initiative - agent added this proactively |
| `[?]` | Unclear - needs confirmation |

### Where to Use

- Features
- Design decisions
- Extension points
- Any spec that required a choice

### Where NOT to Use

- Notes section (that's the conversation space)
- Pure facts (file exists, function takes X params)
- Convention markers themselves (`:warn:`, `:contract:`)

---

## Spec Format

Every significant spec should have context. The full format:

```markdown
- <specific spec>
  > intent: <what the human actually wanted, in plain language>
  > why: <technical reasoning for this approach>
  > decided: <how we got here>
```

### The `decided:` Field

This replaces simple markers with richer context:

| Value | Meaning |
|-------|---------|
| `human` | Human specified this directly |
| `agent, human approved` | Agent proposed, human said yes |
| `conversation` | Back-and-forth discussion to reach this |
| `agent (default)` | Technical default, human doesn't need to care |
| `unknown` | Legacy/existing code, origin unclear |

### Examples

**Human-specified feature:**
```markdown
- arrow keys and WASD to move
  > intent: standard game controls
  > decided: human
```

**Agent proposal, human approved:**
```markdown
- movement queue (max 3 inputs)
  > intent: controls should feel responsive, no lost keypresses
  > why: buffers rapid inputs, executes one per frame
  > decided: agent, human approved
```

**Reached through conversation:**
```markdown
- 150ms game tick
  > intent: responsive but playable
  > why: controls update speed and difficulty
  > decided: conversation - agent proposed 100ms, human felt too fast
```

**Technical default:**
```markdown
- uses requestAnimationFrame for render loop
  > why: smoother than setInterval, syncs with display refresh
  > decided: agent (default)
```

**Legacy code:**
```markdown
- retry logic with exponential backoff
  > why: handles transient failures
  > decided: unknown - existed before ADL
```

### Short Form

For simple items, you can use minimal format:

```markdown
- arrow keys to move (decided: human)
- 150ms tick rate (decided: conversation)
```

But prefer full format for anything non-trivial.

---

## The Conversation Flow

The Notes section is where intent gets refined:

### Step 1: Human yaps

```markdown
## Yap Here

- want the snake to feel snappy
- current movement feels weird
- sometimes my keypresses get lost
```

### Step 2: Agent asks clarifying questions

```markdown
## Yap Here

- want the snake to feel snappy
- current movement feels weird  
- sometimes my keypresses get lost

<!-- AGENT: To make sure I understand:
     
     "Snappy" - do you mean:
     a) Faster reaction to input?
     b) Smoother animation?
     c) Both?
     
     "Keypresses get lost" - this happens when:
     a) Pressing keys very quickly?
     b) Pressing during snake movement?
     
     This helps me propose the right fix. -->
```

### Step 3: Human clarifies

```markdown
## Yap Here

- want the snake to feel snappy
- current movement feels weird
- sometimes my keypresses get lost

snappy means faster reaction. keypresses lost when pressing quickly

<!-- AGENT: ... -->
```

### Step 4: Agent proposes specific specs

```markdown
<!-- AGENT: Got it. I propose adding:

- movement queue (max 3 inputs)
  > intent: no lost keypresses when pressing quickly
  > why: buffers rapid inputs, executes one per frame
  > decided: agent, human approved (pending)

- reduce tick to 100ms (from 150ms)
  > intent: snappier reaction
  > why: faster updates = less input delay
  > decided: agent, human approved (pending)

Ok with these? Can adjust if 100ms feels too fast. -->
```

### Step 5: Human approves or adjusts

Human says: "yes but try 120ms, 100 seems aggressive"

### Step 6: Agent finalizes in structured sections

```markdown
## Features

- movement queue (max 3 inputs)
  > intent: no lost keypresses when pressing quickly
  > why: buffers rapid inputs, executes one per frame
  > decided: agent, human approved

## Decisions

- 120ms game tick
  > intent: snappy but not too fast
  > why: balance between responsiveness and playability
  > decided: conversation - started at 100ms, human adjusted to 120ms
```

### Step 7: Agent implements code

Only after specs are in structured sections does the agent write code.

---

## Tone and Style

ADL should read like working notes, not polished documentation.

**Too formal:**
> Visual styling with modern gradient background and glassmorphism effects, providing a contemporary aesthetic

**Better:**
> gradient bg, glassmorphism look, mobile-friendly

**Principles:**
- Strip marketing adjectives (modern, smooth, clean, elegant)
- Keep it terse
- Match the informality of the Notes section
- Facts over flourish

---

## Abstract Sections

Not everything maps to a file. Use sub-sections for abstract concepts:

```markdown
## Style / Conventions

- minimal, no frameworks (decided: human)
- css custom properties for theming (decided: agent, human approved)

## Architecture

- single page app (decided: human)
- separated into html/css/js files (decided: agent, human approved)
```

These help document decisions that span multiple files or are conceptual.

---

## Root ADL.md (Project Level)

The root `ADL.md` has additional responsibilities:

```markdown
# Project Name

One paragraph describing the project's purpose.

## Yap Here

<!-- Yap yap, write down your thoughts here and the agent will take care of it.. for project-level thoughts -->

## Quick Map

Brief guide to the codebase structure:

- `src/api/` - HTTP layer
- `src/auth/` - Authentication  
- `src/database/` - Data persistence
- `src/jobs/` - Background processing

## Global Conventions

Project-wide rules that apply everywhere:

- All errors extend `AppError`
- Config via environment variables in `src/config.ts`
- Tests in `tests/` mirror source structure

## Architecture Decisions

Major technical choices:

> :decision: Monolith architecture
> Simpler deployment and debugging for current team size.

> :decision: PostgreSQL + Redis
> Postgres for persistence, Redis for sessions and caching.

## Extension Guidelines

How to add new functionality:

> :extends: New API routes go in `src/api/routes/`
> :extends: New background jobs go in `src/jobs/`

## Current State

Honest assessment of documentation coverage:

- `auth/` - Well documented
- `api/` - Partially documented  
- `database/` - Needs work
- `jobs/` - Undocumented, ask Sarah
```

---

## Agent Reading Protocol

When an agent needs to understand code:

1. **Start at root** - Read project-level `ADL.md` first
2. **Follow the path** - Read `ADL.md` files down to the relevant module
3. **Check dependencies** - Read `ADL.md` for modules listed in "Depends On"
4. **Then read code** - Only after understanding context from ADL

## Agent Writing Protocol

When an agent modifies code:

1. **Read ADL first** - Understand existing structure and conventions
2. **Check for conflicts** - Does the change violate any `:contract:` or `:decision:`?
3. **Make code changes** - Implement the modification
4. **Update ADL** - Add/modify entries for changed functionality
5. **Preserve human notes** - Don't delete or rewrite the Notes section
6. **Add markers** - Include `:warn:`, `:contract:` etc. where appropriate

## Completeness Indicators

ADL files reveal their own completeness:

| State | Indicators |
|-------|------------|
| **Undocumented** | No `ADL.md` exists |
| **Stub** | Only title and one-line description |
| **Partial** | Has "What's Here" but missing dependencies/decisions |
| **Complete** | Has all relevant sections filled out |
| **Stale** | Contains `:todo:` items or references to non-existent code |

---

## Examples

### Minimal (Valid)

```markdown
# Utils

Common utility functions used across the project.
```

### Partial

```markdown
# Utils

Common utility functions used across the project.

## What's Here

### `string.ts`
String manipulation helpers.

- `slugify(text)` → URL-safe string
- `truncate(text, length)` → truncated with ellipsis

### `date.ts`  
Date formatting and parsing.

- `formatDate(date, format)` → formatted string
- `parseDate(string)` → Date object
```

### Complete

```markdown
# Utils

Common utility functions used across the project. These are pure functions with no side effects or external dependencies.

## Yap Here

- might want to add a `money.ts` for currency formatting
- the date parsing is locale-dependent, need to document that

## What's Here

### `string.ts`
String manipulation helpers.

- `slugify(text)` → URL-safe string
- `truncate(text, length)` → truncated with ellipsis
- `capitalize(text)` → first letter uppercase

> :contract: All functions handle null/undefined by returning empty string.

### `date.ts`
Date formatting and parsing.

- `formatDate(date, format)` → formatted string
- `parseDate(string)` → Date object or null

> :warn: Uses system locale. Results vary by environment.

> :todo: Add timezone-aware versions.

## Depends On

None - this module has no dependencies.

## Used By

- `api/` - response formatting
- `database/` - date serialization
- `jobs/` - logging timestamps

## Key Decisions

> :decision: No external date library
> Moment.js is heavy, date-fns is fine but we don't need it yet. Native Date is sufficient.
```

---

## Versioning

ADL files can include a last-updated marker at the bottom:

```markdown
---
Last updated: 2024-01-15
```

This helps identify potentially stale documentation.