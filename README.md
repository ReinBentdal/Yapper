# Yapper

A conversation-based alignment layer between humans and AI coding agents. Yapper turns messy human intent ("yapping") into specific, trackable specs through dialogue.

## The Problem

When coding with AI agents:
- Codebases get messy fast
- Agents lack context and reinvent wheels
- Humans lose control of their own code
- No way to track who decided what

## The Solution

Yapper creates a conversation artifact - not documentation, but a record of how human intent becomes code:

1. **Human yaps** vague thoughts in the "Yap Here" section
2. **Agent asks** clarifying questions
3. **Together they refine** into specific specs
4. **Agent implements** only after approval
5. **Everything is tracked** with `decided:` attribution

## Quick Start

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your-key

# Interactive mode
python agent.py -i --project ./your-project

# Single request
python agent.py "add user login" --project ./your-project

# Initialize Yapper for a new project
python agent.py --init --project ./your-project
```

## How It Works

Every spec has context:

```markdown
- movement queue (max 3 inputs)
  > intent: no lost keypresses when pressing quickly
  > why: buffers rapid inputs, executes one per frame
  > decided: agent, human approved
```

The `decided:` field tracks attribution:
- `human` - human specified this
- `agent, human approved` - agent proposed, human agreed
- `conversation` - emerged from back-and-forth
- `agent (default)` - technical default
- `unknown` - legacy code

## Features

- **Change detection** - Shows which ADL files have pending changes on startup
- **Hash tracking** - Each ADL file has a hash to detect modifications
- **Rate limit handling** - Pauses and retries instead of crashing
- **Colored diffs** - Git-style +/- for all changes
- **Guided init** - Conversational setup for new projects

## File Structure

```
your-project/
├── ADL.md              # Root: project overview
├── src/
│   ├── ADL.md          # src-level specs
│   └── auth/
│       └── ADL.md      # Auth module specs
```

## Commands

In interactive mode:
- `quit` - exit
- `clear` - reset conversation
- `changes` - show pending ADL changes
- `mark <path>` - mark ADL as implemented

## The Name

"Yapper" - because humans yap their messy thoughts and the agent makes sense of them. The "Yap Here" section is where stream-of-consciousness goes, and the agent structures it into specs.

## Documentation

- `ADL.md` - This project's own spec (meta!)
- `ADL-SPEC.md` - The Yapper format specification
- `AGENT-SYSTEM-PROMPT.md` - Agent behavioral instructions

## License

MIT