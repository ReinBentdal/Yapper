# Yapper Specification (YAP)

Version: 0.7

## Purpose

YAP (Yapper files) is a **conversation artifact** - the record of how human intent becomes specific implementation, with all reasoning preserved.

It serves three roles:

1. **Conversation space** - where vague human intent gets refined into specific specs through dialogue
2. **Agreement record** - the specs that human and agent have aligned on
3. **Reasoning archive** - why decisions were made, so anyone (human, agent, future reader) can understand

Core principles:

- **Intent preserved** - every spec traces back to what the human actually wanted
- **Reasoning visible** - technical choices are justified, not just stated
- **Decision history** - how we got here (human, agent, conversation)
- **No hidden changes** - agent proposes through YAP, human reviews YAP diffs
- **Specificity required** - vague intent in, specific specs out
- **Stateless structure** - only "Yap Here" contains temporary state
- **Strict structure** - only specified sections allowed, enforced by agents
- **Forward-looking architecture** - YAP describes "what should be" not "what currently is"
- **Implementation-independent** - architectural decisions only, not codebase-specific details

The goal: **codebases where humans stay in control** even when agents do most of the coding, because the YAP captures the conversation that produced the code.

## How It Works

```
Human has vague intent
        ↓
Human yaps in Yap Here section
        ↓
Agent asks clarifying questions (in Yap Here)
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
        ↓
"Yap Here" cleared when marked implemented (architectural decisions preserved)
```

**The human reviews YAP changes, not code changes.** If the YAP is right, the code should follow.

## File Structure

### Location

YAP files are named `YAP.md` and scattered throughout a codebase:

```
project/
├── YAP.md                    # Root: project overview
├── src/
│   ├── YAP.md                # src-level concerns  
│   ├── auth/
│   │   ├── YAP.md            # Auth module documentation
│   │   └── *.ts
│   └── database/
│       ├── YAP.md            # Database module documentation
│       └── *.ts
```

**Scope Rule:** A `YAP.md` describes its directory and all subdirectories, unless a subdirectory has its own `YAP.md` (which takes over).

### Minimal Valid YAP.md

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

### Allowed Optional Sections

**Standard Module Sections:**
- `Yap Here` - Human scratchpad and temporary state (preferred name)
- `What's Here` - Architectural capabilities and responsibilities
- `Depends On` - Dependencies
- `Used By` - What uses this module
- `Key Decisions` - Architectural choices

**Root Project Additional Sections:**
- `Quick Map` - Codebase overview
- `Global Conventions` - Project-wide rules
- `Architecture Decisions` - Major technical choices
- `Extension Guidelines` - How to add new functionality

**Abstract Concept Sections:**
- `Style / Conventions` - Cross-cutting style rules
- `Architecture` - Architectural patterns

### Stateless Design

**YAP files are stateless except for "Yap Here":**

- **Permanent sections** contain stable architectural decisions and documentation
- **"Yap Here" section** is the ONLY place for temporary state, work-in-progress, and changing status
- **No implementation-dependent sections** - YAP describes architecture, not current code state

This ensures YAP files represent stable, forward-looking architecture while keeping working state clearly separated.

### Implementation Independence

**YAP must be implementation-independent:**

- Describe **what should exist** architecturally, not **what files currently contain**
- Focus on **capabilities and responsibilities**, not **code structure details**
- Avoid **file-specific details** unless they represent architectural decisions
- No **status tracking** of current implementation state outside "Yap Here"

**Examples:**

❌ **Implementation-dependent (avoid):**
```markdown
- `auth.py` has 200 lines with login/logout functions
- OAuth tokens stored in tokens table with expires_at column
- Session cleanup runs every 15 minutes via cron job
- Rate limiting uses Redis with 100/minute default
```

✅ **Architecture-focused (preferred):**
```markdown
- OAuth authentication with Google and GitHub providers
- Session management with configurable TTL
- Automatic cleanup of expired sessions
- Rate limiting per IP with configurable thresholds
```

### Section Enforcement

**Agents MUST:**
- Only create sections from the allowed list above
- Move temporary state content to "Yap Here" section
- Reject/remove any non-standard sections from existing YAP files
- Integrate content from non-standard sections into appropriate standard sections
- Ask humans where to place content that doesn't fit standard sections
- Focus on architectural decisions, not implementation details
- Clear "Yap Here" when marking YAP as implemented (via new tool)

**Non-standard sections found in existing files should be:**
- Integrated into `What's Here` if describing architectural capabilities
- Moved to `Key Decisions` if architectural choices
- Moved to `Yap Here` if temporary state, TODOs, or missing features
- Removed if redundant with other sections or implementation-specific

---

## The Yap Here Section

Every YAP.md SHOULD have a "Yap Here" section at the top (after the title and description). This is where ALL temporary state lives - both human thoughts and agent working state.

```markdown
# Auth Module

Handles user authentication and sessions.

## Yap Here

<!-- Human thoughts and stream-of-consciousness -->
- sarah said we might need to add SAML support Q2
- the refresh token logic feels brittle
- wondering if we need better error messages

### Agent Working State
<!-- Temporary implementation status, gaps, next steps -->
- **Active Work**: implementing OAuth providers
- **Next**: add session cleanup mechanism
- **Questions**: should rate limiting be per-user or per-IP?
```

**Structure within "Yap Here":**
- Human notes at the top (freeform)
- Optional `### Agent Working State` subsection for temporary agent state
- Agent can add conversation comments with `<!-- AGENT: ... -->`

**Agent Behavior:** 
- READ this section for context and intent
- DO NOT delete human notes without explicit permission
- Extract actionable information into structured sections below
- Use "Agent Working State" for temporary tracking only
- Can add to notes if uncertain where something belongs
- **CLEAR this section when marking YAP as implemented** (preserve human notes in permanent sections first if requested)

**Lifecycle:**
1. Human yaps, agent tracks work in "Agent Working State"
2. Conversation refines intent into architectural specs
3. Specs move to permanent sections with full context
4. Agent implements code to match architectural specs
5. When marked implemented, "Yap Here" is cleared for next cycle

---

## Standard Sections

These are the conventional sections. Use the ones that apply.

### What's Here

Describes architectural capabilities and responsibilities, **not file contents**.

Focus on **what this module provides** architecturally, not **how it's currently implemented**.

```markdown
## What's Here

### OAuth Authentication
Support for Google and GitHub OAuth flows with automatic token refresh.

- Provider registration and configuration
- Authorization flow initiation and completion  
- Token management and refresh handling

### Session Management
Secure session handling with configurable TTL and cleanup.

- Session creation and validation
- Automatic expiration and cleanup
- Cross-request state persistence

### Rate Limiting
Configurable rate limiting to prevent abuse.

- Per-IP request limiting
- Configurable thresholds and windows
- Graceful degradation when limits exceeded
```

**NOT this (implementation-focused):**
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

What this module needs to function (architectural dependencies).

```markdown
## Depends On

- User data persistence
- Configuration management  
- Caching layer for session storage
```

### Used By

What depends on this module. Critical for understanding blast radius.

```markdown
## Used By

- API layer - authenticates requests
- Admin interface - manages user sessions
- Background jobs - cleanup tasks
```

### Key Decisions

Architectural choices and their rationale.

```markdown
## Key Decisions

> :decision: OAuth over password-only authentication
> intent: reduce password fatigue, improve security
> why: users prefer social login, fewer passwords to manage
> decided: human

> :decision: Session-based auth over JWTs
> intent: instant revocation for enterprise security
> why: JWTs require blacklists anyway, sessions simpler
> decided: conversation

> :decision: Redis for session storage
> intent: fast session lookups, automatic expiration
> why: built-in TTL, shared across server instances
> decided: agent, human approved
```

---

## Convention Markers

Use blockquotes with markers for machine-parseable annotations:

| Marker | Purpose | Example |
|--------|---------|---------|
| `:warn:` | Gotchas, dangers, non-obvious behavior | `> :warn: Mutates input array` |
| `:contract:` | Preconditions, assumptions, requirements | `> :contract: Requires Redis connection` |
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
### Authentication System

OAuth and session-based authentication with configurable providers.

> :warn: Session validation throws AuthenticationError for invalid tokens.

> :contract: Requires OAuth provider credentials in environment.

> :deprecated: Password-only auth deprecated. Use OAuth providers instead.
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

- Yap Here section (that's the conversation space)
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
- OAuth authentication with Google and GitHub
  > intent: users want social login options
  > decided: human
```

**Agent proposal, human approved:**
```markdown
- Session cleanup every 24 hours
  > intent: prevent database bloat from expired sessions
  > why: automatic cleanup reduces maintenance, 24h balances cleanup with performance
  > decided: agent, human approved
```

**Reached through conversation:**
```markdown
- Rate limiting: 100 requests per minute per IP
  > intent: prevent abuse while allowing legitimate usage
  > why: 100 req/min supports normal user patterns, per-IP prevents single-user abuse
  > decided: conversation - agent proposed 60/min, human preferred 100/min
```

**Technical default:**
```markdown
- Redis for session storage
  > why: built-in TTL, shared across server instances
  > decided: agent (default)
```

**Legacy code:**
```markdown
- bcrypt password hashing (legacy)
  > why: secure password storage for existing password accounts
  > decided: unknown - existed before YAP
```

### Short Form

For simple items, you can use minimal format:

```markdown
- OAuth with Google and GitHub (decided: human)
- 100 req/min rate limit (decided: conversation)
```

But prefer full format for anything non-trivial.

---

## The Conversation Flow

The Yap Here section is where intent gets refined:

### Step 1: Human yaps

```markdown
## Yap Here

- users keep complaining about having to create accounts
- want to make signup easier somehow
- maybe social login?
```

### Step 2: Agent asks clarifying questions

```markdown
## Yap Here

- users keep complaining about having to create accounts
- want to make signup easier somehow
- maybe social login?

<!-- AGENT: For social login, which providers would you prefer?
     - Google (most common)
     - GitHub (developer-focused)
     - Facebook/Meta
     - Others?
     
     Also, do you want to:
     a) Replace password signup entirely?
     b) Offer both social + password options?
     
     This helps me propose the right architecture. -->
```

### Step 3: Human clarifies

```markdown
## Yap Here

- users keep complaining about having to create accounts
- want to make signup easier somehow
- maybe social login?

Google and GitHub for now. Keep password option for people who don't want social.

<!-- AGENT: ... -->
```

### Step 4: Agent proposes architectural specs

```markdown
<!-- AGENT: Got it. I propose these architectural capabilities:

### OAuth Authentication System
Support for Google and GitHub OAuth with fallback to password auth.

- OAuth provider registration and flow handling
- Automatic account linking for existing email matches
- Password authentication maintained as fallback option

> intent: easier signup while preserving existing user options
> why: OAuth reduces friction, keeping passwords supports user choice
> decided: agent, human approved (pending)

### Session Management
Unified session handling regardless of auth method.

- Same session format for OAuth and password users
- Configurable session TTL
- Automatic cleanup of expired sessions

> intent: consistent experience after authentication
> why: users shouldn't see difference once logged in
> decided: agent, human approved (pending)

Sound right? Any adjustments to the approach? -->
```

### Step 5: Human approves or adjusts

Human says: "yes, but make sure Google is the primary option - most users will want that"

### Step 6: Agent finalizes in structured sections

```markdown
## What's Here

### OAuth Authentication System
Multi-provider OAuth with Google as primary, GitHub as secondary, password fallback.

- Google OAuth (primary recommendation in UI)
- GitHub OAuth (secondary option)
- Password authentication (fallback for users who prefer it)
- Automatic account linking for matching email addresses

> intent: easier signup while preserving user choice
> why: OAuth reduces signup friction, Google is most familiar, passwords for privacy-conscious users
> decided: conversation - agent proposed equal weighting, human preferred Google prominence

### Session Management
Unified session handling regardless of authentication method.

- Consistent session format across auth types
- Configurable TTL with secure defaults
- Automatic cleanup of expired sessions

> intent: transparent user experience after authentication
> why: authentication method shouldn't affect session behavior
> decided: agent, human approved
```

### Step 7: Agent implements code

Only after architectural specs are in structured sections does the agent write code.

### Step 8: Mark as implemented and clear

When implementation is complete and YAP is marked as implemented, the "Yap Here" section is cleared, preserving only the architectural decisions in permanent sections.

---

## Implementation Lifecycle

### "Yap Here" Clearing

When a YAP is marked as implemented, the "Yap Here" section should be cleared to prepare for the next cycle of changes:

1. **Agent checks if human notes should be preserved** - asks human if any thoughts should move to permanent sections
2. **Preserves important human insights** in Key Decisions or appropriate sections if requested
3. **Clears the entire "Yap Here" section** including Agent Working State
4. **Leaves the section header** so it's ready for future thoughts
5. **Updates the implementation hash** to mark current architectural state as implemented

**Result after clearing:**
```markdown
## Yap Here

<!--
Yap yap, write down your thoughts here and the agent will take care of it..
-->
```

This creates a clean slate for the next round of architectural evolution while preserving the permanent architectural decisions that resulted from the previous conversation.

---

## Tone and Style

YAP should read like working notes, not polished documentation.

**Too formal:**
> Visual styling with modern gradient background and glassmorphism effects, providing a contemporary aesthetic

**Better:**
> gradient bg, glassmorphism look, mobile-friendly

**Principles:**
- Strip marketing adjectives (modern, smooth, clean, elegant)
- Keep it terse
- Match the informality of the Yap Here section
- Facts over flourish
- Architecture over implementation details

---

## Abstract Sections

Not everything maps to a file. Use sub-sections for abstract concepts:

```markdown
## Style / Conventions

- minimal design, no heavy frameworks (decided: human)
- CSS custom properties for consistent theming (decided: agent, human approved)

## Architecture

- single-page application architecture (decided: human)
- separation of concerns: presentation, business logic, data (decided: agent, human approved)
```

These help document decisions that span multiple files or are conceptual.

---

## Root YAP.md (Project Level)

The root `YAP.md` has additional responsibilities:

```markdown
# Project Name

One paragraph describing the project's purpose.

## Yap Here

<!-- Human thoughts and stream-of-consciousness for project-level concerns -->
- thinking about adding a web UI for YAP editing
- performance seems good but should profile the API layer

### Agent Working State
<!-- Temporary project-level state -->
- **Active Work**: refactoring authentication module
- **Next Milestone**: v1.0 release preparation
- **Open Questions**: deployment strategy for production

## Quick Map

Brief guide to the codebase architecture:

- `src/api/` - HTTP request handling layer
- `src/auth/` - Authentication and session management  
- `src/database/` - Data persistence layer
- `src/jobs/` - Background processing system

## Global Conventions

Project-wide architectural rules:

- All errors extend `AppError` base class
- Configuration via environment variables, validated on startup
- Database transactions for multi-step operations

## Architecture Decisions

Major technical choices:

> :decision: Monolith architecture over microservices
> intent: simpler deployment and debugging for current team size
> why: team of 3 developers, complexity not worth the overhead yet
> decided: human

> :decision: PostgreSQL primary database with Redis for caching
> intent: reliable persistence with fast session/cache layer
> why: PostgreSQL for ACID transactions, Redis for ephemeral data
> decided: conversation

## Extension Guidelines

How to add new functionality:

> :extends: New API routes follow REST conventions in `src/api/routes/`
> :extends: Background jobs implement `JobInterface` in `src/jobs/`
> :extends: Database migrations use semantic versioning in `migrations/`
```

---

## Agent Reading Protocol

When an agent needs to understand code:

1. **Start at root** - Read project-level `YAP.md` first
2. **Follow the path** - Read `YAP.md` files down to the relevant module
3. **Check dependencies** - Read `YAP.md` for modules listed in "Depends On"
4. **Then read code** - Only after understanding architectural context from YAP

## Agent Writing Protocol

When an agent modifies code:

1. **Read YAP first** - Understand existing architecture and conventions
2. **Check for conflicts** - Does the change violate any `:contract:` or `:decision:`?
3. **Propose architectural changes** - Update YAP with new capabilities/decisions before coding
4. **Get approval** - Wait for human approval of architectural changes
5. **Make code changes** - Implement to match approved architectural specs
6. **Update YAP** - Add/modify entries for changed architectural capabilities
7. **Preserve human notes** - Don't delete or rewrite human content in "Yap Here"
8. **Add markers** - Include `:warn:`, `:contract:` etc. where appropriate
9. **Enforce structure** - Only use allowed sections, integrate non-standard content
10. **Use "Yap Here" for temporary state** - active work, questions, next steps only
11. **Clear "Yap Here" when marking implemented** - preserve architecture, reset working state

## Agent Tools

The Yapper agent provides these tools for working with code and YAP files:

### File Operations

| Tool | Description | Limits |
|------|-------------|--------|
| `read_file` | Read file contents with line numbers | 100 lines max per call, **blocked for YAP files** |
| `file_info` | Get file metadata (size, line count) | Use before reading unknown files |
| `search_files` | Search for regex pattern in files | Returns file:line:content matches |
| `edit_file` | Replace old_string with new_string | **Blocked for YAP files** - use write_yap_section |
| `write_file` | Create new files | **Blocked for YAP files** - use write_yap_section |
| `list_directory` | List directory contents | Excludes hidden files |

### YAP Operations

| Tool | Description |
|------|-------------|
| `read_yap_chain` | Read all YAP.md files relevant to a path (full content) |
| `read_yap_section` | Read a specific section from a YAP file (efficient, low token cost) |
| `write_yap_section` | Write/update a specific section in a YAP file (enforces structure) |
| `update_yap` | Update entire YAP.md file content |
| `mark_yap_implemented` | Mark YAP as implemented (updates hash) |
| `clear_yap_here` | Clear "Yap Here" section after implementation |
| `task_complete` | Signal task completion with summary |

### Tool Usage Guidelines

- **Always use `file_info` before reading unknown files** to check size
- **Use `edit_file` over `write_file`** for existing files (more reliable, smaller changes)
- **Use `search_files` to find code** before reading entire files
- **Paginate large files** with `start_line` parameter (100 line limit per read)
- **Call `clear_yap_here` after `mark_yap_implemented`** to reset for next cycle
- **Use section-specific tools for YAP files** - `read_yap_section`/`write_yap_section` for efficiency
- **Never use `read_file`/`write_file`/`edit_file` on YAP files** - they are blocked, use YAP-specific tools

---

## Section Enforcement Protocol

When agents encounter non-standard sections in YAP files:

1. **Identify non-standard sections** - Compare against allowed section list
2. **Propose integration** - Suggest where permanent content should move
3. **Get approval** - Ask human before making structural changes
4. **Preserve content** - Don't delete information, just reorganize
5. **Focus on architecture** - Move implementation details to "Yap Here" or remove
6. **Clean structure** - Result should only have allowed sections

**Common integrations:**
- "Features" → `What's Here` (if architectural capabilities)
- "TODO" / "Future Work" → `Yap Here → Agent Working State`
- "Current State" / "Gaps" → `Yap Here → Agent Working State` or remove if stale
- "Design Notes" → `Key Decisions` (if architectural)
- Implementation-specific content → Remove or move to `Yap Here`
- Random notes → `Yap Here`

---

## Completeness Indicators

YAP files reveal their own completeness:

| State | Indicators |
|-------|------------|
| **Undocumented** | No `YAP.md` exists |
| **Stub** | Only title and one-line description |
| **Partial** | Has "What's Here" but missing key architectural decisions |
| **Complete** | Has all relevant architectural sections filled out |
| **Active Work** | "Yap Here" has active agent working state |
| **Implemented** | Hash marked as implemented, "Yap Here" cleared |

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

### String Operations
Text manipulation capabilities for URLs and user input.

- URL slug generation from arbitrary text
- Text truncation with smart word boundaries
- Case conversion and normalization

### Date Handling  
Date formatting and parsing with timezone awareness.

- Flexible date parsing from various formats
- Localized formatting for user display
- Timezone conversion utilities
```

### Complete with Active Work

```markdown
# Utils

Common utility functions used across the project. Pure functions with no side effects or external dependencies.

## Yap Here

- might want to add money formatting utilities
- date parsing should handle more edge cases

### Agent Working State
- **Active Work**: implementing timezone-aware date functions
- **Next**: add currency formatting capabilities
- **Questions**: should we support custom date formats or stick to ISO?

## What's Here

### String Operations
Text manipulation capabilities for URLs and user input.

- URL slug generation with Unicode support
- Smart text truncation preserving word boundaries
- Case conversion with locale awareness

> :contract: All functions handle null/undefined input gracefully.

### Date Handling
Date formatting and parsing with comprehensive timezone support.

- Multi-format date parsing with fallbacks
- Localized formatting respecting user preferences
- Timezone conversion with DST handling

> :warn: Uses system locale for formatting - results vary by environment.
> :contract: Requires valid Date objects or ISO strings as input.

## Depends On

None - this module has no external dependencies by design.

## Used By

- API layer - response formatting and validation
- Database layer - date serialization and parsing
- Background jobs - timestamp generation and logging

## Key Decisions

> :decision: No external date library dependency
> intent: keep bundle size minimal, reduce external dependencies
> why: native Date API sufficient for current needs, can add library later if needed
> decided: human

> :decision: Pure functions only, no state
> intent: predictable behavior, easy testing, no side effects
> why: utilities should be reliable and not affect other system parts
> decided: agent, human approved
```

### After Implementation (Cleared)

```markdown
# Utils

Common utility functions used across the project. Pure functions with no side effects or external dependencies.

## Yap Here

<!--
Yap yap, write down your thoughts here and the agent will take care of it..
-->

## What's Here

### String Operations
Text manipulation capabilities for URLs and user input.

- URL slug generation with Unicode support
- Smart text truncation preserving word boundaries
- Case conversion with locale awareness

> :contract: All functions handle null/undefined input gracefully.

### Date Handling
Date formatting and parsing with comprehensive timezone support.

- Multi-format date parsing with fallbacks
- Localized formatting respecting user preferences
- Timezone conversion with DST handling

> :warn: Uses system locale for formatting - results vary by environment.
> :contract: Requires valid Date objects or ISO strings as input.

### Currency Formatting
Money formatting with locale and currency support.

- Multi-currency formatting with proper symbols
- Locale-aware number formatting
- Precision handling for different currencies

> :contract: Requires valid currency codes (ISO 4217).
> :warn: Formatting accuracy depends on browser Intl support.

## Depends On

None - this module has no external dependencies by design.

## Used By

- API layer - response formatting and validation
- Database layer - date serialization and parsing
- Background jobs - timestamp generation and logging
- E-commerce - price display and calculations

## Key Decisions

> :decision: No external date library dependency
> intent: keep bundle size minimal, reduce external dependencies
> why: native Date API sufficient for current needs, can add library later if needed
> decided: human

> :decision: Pure functions only, no state
> intent: predictable behavior, easy testing, no side effects
> why: utilities should be reliable and not affect other system parts
> decided: agent, human approved

> :decision: Browser Intl API for currency formatting
> intent: native internationalization without external libraries
> why: Intl.NumberFormat handles currency and locale complexities
> decided: agent, human approved
```

---

## Versioning

YAP files can include a last-updated marker at the bottom:

```markdown
---
Last updated: 2024-01-15
```

This helps identify potentially stale documentation.