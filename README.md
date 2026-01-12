# Yapper

A conversation-based alignment layer for agent-assisted codebases. Yapper enforces **specs first, then code** - turning messy human intent into specific, trackable specs through dialogue.

## The Problem

When coding with AI agents:
- Agents jump straight to code without understanding context
- Codebases get messy fast with no architectural record
- Humans lose track of who decided what and why
- No way to detect when code drifts from agreed specs

## The Solution

Yapper uses `.yap` files as the single source of truth for architectural context:

1. **Human writes intent** in the "Yap Here" section
2. **Agent clarifies** through questions
3. **Together they agree** on specific specs
4. **Human approves** before implementation
5. **Agent implements** to match specs
6. **Hash tracking** detects when code drifts from specs

## Quick Start

```bash
pip install anthropic python-dotenv
export ANTHROPIC_API_KEY=your-key

# Interactive mode
python agent.py --project ./your-project

# Single request
python agent.py "add user login" --project ./your-project

# Initialize YAP for a new project
python agent.py --init --project ./your-project
```

## How It Works

Every spec has context and attribution:

```markdown
- Rate limiting via token bucket (decided: agent, human approved)
  > intent: prevent abuse without blocking legitimate users
  > why: allows burst traffic while enforcing average rate
```

Attribution values:
- `human` - human specified directly
- `agent, human approved` - agent proposed, human agreed
- `conversation` - emerged from back-and-forth discussion
- `agent (default)` - technical default, low importance

## File Structure

```
your-project/
├── project.yap         # Project-level context
├── agent.yap           # Specs for agent.py
├── .yapignore          # Protect sensitive files
├── src/
│   ├── auth.yap        # Specs for auth.py or auth/
│   └── utils.yap       # Specs for utils.py
```

Each `.yap` file maps to a code file or directory with the same name.

## Features

- **Change detection** - Shows which .yap files have pending changes on startup
- **Hash tracking** - Detects when code changes without yap review
- **Rate limit handling** - Pauses with countdown instead of crashing
- **Colored output** - Git-style diffs for all changes
- **Yapignore** - Protect sensitive files from agent access

## CLI Commands

In interactive mode:
- `quit` - exit
- `clear` - reset conversation
- `changes` - show pending yap/code changes
- `mark <path>` - mark .yap as implemented

## .yapignore

Protect sensitive files from agent access:

```gitignore
# Environment files
.env*

# Cryptographic keys
*.key
*.pem

# Cache directories
__pycache__/
node_modules/
```

## YAP File Structure

```markdown
# Module Name

Brief description of what this does.

## Yap Here
<!-- Working space for conversation and implementation state -->

## What This Does
Architectural purpose - what capability this provides.

## Key Decisions
Important choices with attribution.

## Contracts
What must be true. Specific and verifiable.

## Depends On / Used By
Relationships to other modules.
```

## Documentation

- `project.yap` - Project-level architectural context
- `agent.yap` - Architectural context for the agent implementation
- `YAP-SPEC.md` - The YAP format specification
- `AGENT-SYSTEM-PROMPT.md` - Agent behavioral instructions

## License

MIT
