# ADL Agent

A simple agentic coding tool that uses **Agent Description Language (ADL)** to maintain shared understanding between humans and AI coding agents.

## What is ADL?

ADL is a markdown-based documentation format where:

- **Humans can "yap"** - write messy notes, half-thoughts, TODOs
- **Agents structure it** - but only after asking permission
- **Initiative is tracked** - clear who decided what (`[H]` human, `[A]` agent)
- **Files are scattered** - each `ADL.md` lives alongside the code it describes
- **Gaps are obvious** - missing docs are structurally evident

See `ADL-SPEC.md` for the full specification.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY=your-key-here
```

### 3. Run the agent

Single request:
```bash
python agent.py "Add input validation to the login endpoint" --project ./my-project
```

Interactive mode:
```bash
python agent.py --interactive --project ./my-project
```

## How It Works

1. **Agent reads ADL first** - Before touching code, the agent reads relevant `ADL.md` files to understand context, conventions, and constraints.

2. **Agent respects decisions** - Documented `[H]` decisions are human choices the agent won't override. `[A]` decisions are agent choices that can be discussed.

3. **Agent asks before formalizing** - When extracting decisions from human notes, the agent asks for confirmation on wording before moving to structured sections.

4. **Agent logs its own decisions** - Implementation choices the agent makes are marked with `[A]` for transparency.

5. **Agent updates ADL** - After making code changes, the agent updates the relevant `ADL.md` files with proper initiative markers.

## Initiative Tracking

Every decision is marked with who made it:

| Marker | Meaning |
|--------|---------|
| `[H]` | Human initiative - human decided this |
| `[A]` | Agent initiative - agent decided this |
| `[?]` | Unclear - needs confirmation |

Example:
```markdown
## Decisions

> [H] :decision: use canvas not dom
> human wanted smooth graphics

> [A] :decision: 150ms tick rate
> agent chose reasonable default
```

## The Confirmation Workflow

When agent extracts from human notes:

1. Human yaps in Notes section
2. Agent identifies potential decisions
3. Agent asks: "ok to word these as [H] ...?"
4. Human confirms or edits
5. Agent formalizes with `[H]` marker

Agent's own decisions go directly with `[A]`, no confirmation needed.

## Project Structure

```
adl-agent/
├── ADL-SPEC.md              # The ADL language specification
├── AGENT-SYSTEM-PROMPT.md   # System prompt for the coding agent
├── agent.py                 # The Python agent implementation
├── requirements.txt         # Dependencies
├── README.md                # This file
└── sample-project/          # Example project with ADL files
    ├── ADL.md
    └── src/
        └── auth/
            ├── ADL.md
            └── password.py
```

## ADL File Structure

Minimal valid ADL:

```markdown
# Module Name

One sentence describing what this does.
```

Full structure:

```markdown
# Module Name

Description paragraph.

## Notes

<!-- Human scratchpad - agent reads, doesn't modify -->
- random thoughts
- TODOs
- half-baked ideas

## What's Here

### `file.py`
What this file does.

- `function_name()` → what it returns

> :warn: Gotchas and warnings
> :contract: Preconditions and assumptions
> :decision: Design choices with rationale

## Depends On

- `other-module/` - why we need it

## Used By

- `consumer/` - what uses this

## Gaps

- Known missing documentation
```

## Convention Markers

| Marker | Meaning |
|--------|---------|
| `:warn:` | gotcha or danger |
| `:contract:` | precondition or assumption |
| `:todo:` | known incomplete item |
| `:decision:` | design choice with rationale |
| `:deprecated:` | don't use, with alternative |
| `:extends:` | extension point |

## Agent Behavior

The agent follows these rules:

1. **Always read ADL before code** - Uses `read_adl_chain` tool first
2. **Respect `[H]` decisions** - Won't override human choices
3. **Ask before formalizing** - Confirms wording before extracting from notes
4. **Log own decisions as `[A]`** - Transparent about what agent chose
5. **Keep it informal** - Matches human's tone, no marketing speak
6. **Use `[?]` when unsure** - Never guesses about initiative

## Extending

The agent is designed to be extended. Key files:

- `AGENT-SYSTEM-PROMPT.md` - Modify agent behavior and rules
- `ADL-SPEC.md` - Extend the ADL format
- `agent.py` - Add new tools or change the agentic loop

## License

MIT
