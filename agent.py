#!/usr/bin/env python3
"""
Yapper - A conversation-based agentic coding tool.

Features:
- YAP.md change detection on startup
- Hash-based tracking of implementation status
- Colored output with git-style diffs
- Guided YAP initialization for new repos
"""

import os
import sys
import json
import re
import hashlib
import difflib
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv package not installed. Run: pip install python-dotenv")
    sys.exit(1)


def ensure_api_key() -> bool:
    """Load API key from .env file, prompting user to create one if missing."""
    env_path = Path.cwd() / ".env"

    # Try to load existing .env
    load_dotenv(env_path)

    if os.environ.get("ANTHROPIC_API_KEY"):
        return True

    # No API key found, prompt user
    print(f"{Colors.YELLOW}No ANTHROPIC_API_KEY found.{Colors.RESET}")
    print(f"Get your API key from: {Colors.CYAN}https://console.anthropic.com/settings/keys{Colors.RESET}\n")

    api_key = input("Enter your Anthropic API key: ").strip()

    if not api_key:
        print(f"{Colors.RED}No API key provided. Exiting.{Colors.RESET}")
        return False

    # Save to .env file
    env_path.write_text(f"ANTHROPIC_API_KEY={api_key}\n")
    print(f"{Colors.GREEN}API key saved to .env{Colors.RESET}\n")

    # Reload environment
    load_dotenv(env_path)
    return True


# =============================================================================
# Terminal Colors
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    
    @classmethod
    def disable(cls):
        """Disable colors for non-tty output."""
        for attr in dir(cls):
            if not attr.startswith('_') and isinstance(getattr(cls, attr), str):
                setattr(cls, attr, '')


if not sys.stdout.isatty():
    Colors.disable()


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")


def print_subheader(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}--- {text} ---{Colors.RESET}")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")


def print_agent(text: str):
    print(f"{Colors.MAGENTA}🤖 {text}{Colors.RESET}")


def print_diff(old_content: str, new_content: str, filename: str = ""):
    """Print a git-style diff."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"a/{filename}" if filename else "before",
        tofile=f"b/{filename}" if filename else "after",
        lineterm=""
    )
    
    for line in diff:
        line = line.rstrip('\n')
        if line.startswith('+++') or line.startswith('---'):
            print(f"{Colors.BOLD}{line}{Colors.RESET}")
        elif line.startswith('@@'):
            print(f"{Colors.CYAN}{line}{Colors.RESET}")
        elif line.startswith('+'):
            print(f"{Colors.GREEN}{line}{Colors.RESET}")
        elif line.startswith('-'):
            print(f"{Colors.RED}{line}{Colors.RESET}")
        else:
            print(line)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AgentConfig:
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    project_root: str = "."
    yap_filename: str = "YAP.md"


# =============================================================================
# YAP Hash and Tracking
# =============================================================================

class YapTracker:
    """Tracks YAP.md file changes via hash at end of file."""

    HASH_PATTERN = re.compile(
        r'\n---\n<!-- YAP-HASH: ([a-f0-9]+) \| implemented: (.+?) -->\s*$'
    )

    @staticmethod
    def compute_hash(content: str) -> str:
        content = YapTracker.HASH_PATTERN.sub('', content)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def get_hash_info(content: str) -> tuple[Optional[str], Optional[str]]:
        match = YapTracker.HASH_PATTERN.search(content)
        if match:
            return match.group(1), match.group(2)
        return None, None

    @staticmethod
    def add_hash(content: str) -> str:
        content = YapTracker.HASH_PATTERN.sub('', content)
        content = content.rstrip() + '\n'
        file_hash = YapTracker.compute_hash(content)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"{content}\n---\n<!-- YAP-HASH: {file_hash} | implemented: {timestamp} -->\n"

    @staticmethod
    def has_changes(content: str) -> bool:
        stored_hash, _ = YapTracker.get_hash_info(content)
        if stored_hash is None:
            return True
        current_hash = YapTracker.compute_hash(content)
        return current_hash != stored_hash


# =============================================================================
# YAP File Management
# =============================================================================

class YapManager:
    def __init__(self, project_root: str, yap_filename: str = "YAP.md"):
        self.project_root = Path(project_root).resolve()
        self.yap_filename = yap_filename
        self.tracker = YapTracker()
    
    def find_all_yap_files(self) -> list[Path]:
        yap_files = []
        for path in self.project_root.rglob(self.yap_filename):
            yap_files.append(path)
        return sorted(yap_files, key=lambda p: len(p.parts))

    def get_yap_for_path(self, target_path: str) -> list[Path]:
        target = Path(target_path)
        if not target.is_absolute():
            target = self.project_root / target
        target = target.resolve()

        current = target if target.is_dir() else target.parent
        paths_to_check = []

        while True:
            paths_to_check.append(current)
            if current == self.project_root or current == current.parent:
                break
            try:
                current.relative_to(self.project_root)
            except ValueError:
                break
            current = current.parent

        yap_chain = []
        for path in reversed(paths_to_check):
            yap_file = path / self.yap_filename
            if yap_file.exists():
                yap_chain.append(yap_file)

        return yap_chain

    def read_yap(self, yap_path: Path) -> str:
        return yap_path.read_text()

    def write_yap(self, yap_path: Path, content: str):
        yap_path.write_text(content)

    def mark_implemented(self, yap_path: Path):
        content = self.read_yap(yap_path)
        updated = self.tracker.add_hash(content)
        self.write_yap(yap_path, updated)

    def get_changed_yap_files(self) -> list[tuple[Path, str, str, str]]:
        changed = []
        for yap_file in self.find_all_yap_files():
            content = self.read_yap(yap_file)
            if self.tracker.has_changes(content):
                stored_hash, timestamp = self.tracker.get_hash_info(content)
                current_hash = self.tracker.compute_hash(content)
                changed.append((yap_file, stored_hash, current_hash, timestamp))
        return changed

    def get_project_context(self) -> str:
        yap_files = self.find_all_yap_files()
        if not yap_files:
            return "No YAP.md files found in project."

        context_parts = []
        for yap_file in yap_files:
            rel_path = yap_file.relative_to(self.project_root)
            content = self.read_yap(yap_file)
            context_parts.append(f"=== {rel_path} ===\n{content}")

        return "\n\n".join(context_parts)

    def get_recommended_yap_locations(self) -> list[Path]:
        locations = [self.project_root]
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c', '.h'}

        for item in self.project_root.rglob('*'):
            if item.is_file() and item.suffix in code_extensions:
                parent = item.parent
                if parent not in locations and parent != self.project_root:
                    code_files = [f for f in parent.iterdir() if f.suffix in code_extensions]
                    if len(code_files) >= 1:
                        locations.append(parent)

        return sorted(set(locations), key=lambda p: len(p.parts))


# =============================================================================
# File Operations
# =============================================================================

class FileManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self._file_cache = {}
    
    def read_file(self, path: str) -> str:
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        content = full_path.read_text()
        self._file_cache[str(full_path)] = content
        return content
    
    def write_file(self, path: str, content: str) -> str:
        full_path = self._resolve_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        old_content = self._file_cache.get(str(full_path), "")
        if not old_content and full_path.exists():
            old_content = full_path.read_text()
        
        full_path.write_text(content)
        self._file_cache[str(full_path)] = content
        
        if old_content and old_content != content:
            print_subheader(f"Changes to {path}")
            print_diff(old_content, content, path)
        elif not old_content:
            print_success(f"Created new file: {path}")
        
        return f"Successfully wrote to {path}"
    
    def list_directory(self, path: str = ".") -> list[str]:
        full_path = self._resolve_path(path)
        if not full_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        
        items = []
        for item in sorted(full_path.iterdir()):
            if item.name.startswith('.'):
                continue
            rel_path = item.relative_to(self.project_root)
            suffix = "/" if item.is_dir() else ""
            items.append(f"{rel_path}{suffix}")
        return items
    
    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return (self.project_root / p).resolve()


# =============================================================================
# Tools
# =============================================================================

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file relative to project root"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file. Creates directories if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_directory",
        "description": "List contents of a directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to directory, '.' for root"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "read_yap_chain",
        "description": "Read YAP.md files relevant to a path. ALWAYS use before working on code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file/directory to work on"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "update_yap",
        "description": "Update a YAP.md file after agreeing on specs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to YAP.md file"},
                "content": {"type": "string", "description": "New content (preserve Notes section)"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "mark_yap_implemented",
        "description": "Mark YAP as implemented (updates hash). Use when done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to YAP.md file"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "task_complete",
        "description": "Signal task completion with summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "What was accomplished"},
                "files_modified": {"type": "array", "items": {"type": "string"}},
                "yap_updates": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["summary"]
        }
    }
]


# =============================================================================
# Agent
# =============================================================================

class YapAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = anthropic.Anthropic()
        self.yap_manager = YapManager(config.project_root, config.yap_filename)
        self.file_manager = FileManager(config.project_root)
        self.conversation_history = []
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        system_prompt_path = Path(__file__).parent / "AGENT-SYSTEM-PROMPT.md"
        agent_instructions = system_prompt_path.read_text() if system_prompt_path.exists() else ""

        yap_spec_path = Path(__file__).parent / "YAP-SPEC.md"
        yap_spec = yap_spec_path.read_text() if yap_spec_path.exists() else ""

        project_context = self.yap_manager.get_project_context()

        return f"""You are a Yapper coding agent. Turn human intent into specific specs through conversation, then implement.

## YAP Specification
{yap_spec}

## Agent Instructions
{agent_instructions}

## Current Project YAP
{project_context}

## Rules
1. CLARIFY vague intent before proposing specs
2. PROPOSE specs with intent/why/decided before implementing
3. WAIT for approval before coding
4. Use mark_yap_implemented when done
5. Use task_complete to summarize"""
    
    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        try:
            if tool_name == "read_file":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                content = self.file_manager.read_file(tool_input["path"])
                return f"Contents of {tool_input['path']}:\n\n{content}"

            elif tool_name == "write_file":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                if "content" not in tool_input:
                    return "Error: Missing required parameter 'content'"
                return self.file_manager.write_file(tool_input["path"], tool_input["content"])

            elif tool_name == "list_directory":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                items = self.file_manager.list_directory(tool_input["path"])
                return f"Contents of {tool_input['path']}:\n" + "\n".join(items)
            
            elif tool_name == "read_yap_chain":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                yap_files = self.yap_manager.get_yap_for_path(tool_input["path"])
                if not yap_files:
                    return f"No YAP.md files found for: {tool_input['path']}"

                result_parts = []
                for yap_file in yap_files:
                    rel_path = yap_file.relative_to(self.yap_manager.project_root)
                    content = self.yap_manager.read_yap(yap_file)
                    has_changes = self.yap_manager.tracker.has_changes(content)
                    status = " (pending changes)" if has_changes else " (implemented)"
                    result_parts.append(f"=== {rel_path}{status} ===\n{content}")
                return "\n\n".join(result_parts)

            elif tool_name == "update_yap":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                if "content" not in tool_input:
                    return "Error: Missing required parameter 'content'"
                yap_path = Path(tool_input["path"])
                if not yap_path.is_absolute():
                    yap_path = self.yap_manager.project_root / yap_path

                old_content = ""
                if yap_path.exists():
                    old_content = self.yap_manager.read_yap(yap_path)

                self.yap_manager.write_yap(yap_path, tool_input["content"])

                if old_content:
                    print_subheader(f"YAP Changes: {tool_input['path']}")
                    print_diff(old_content, tool_input["content"], tool_input["path"])
                else:
                    print_success(f"Created: {tool_input['path']}")

                return f"Updated {tool_input['path']}"

            elif tool_name == "mark_yap_implemented":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                yap_path = Path(tool_input["path"])
                if not yap_path.is_absolute():
                    yap_path = self.yap_manager.project_root / yap_path
                self.yap_manager.mark_implemented(yap_path)
                print_success(f"Marked {tool_input['path']} as implemented")
                return f"Marked {tool_input['path']} as implemented"

            elif tool_name == "task_complete":
                summary = tool_input.get("summary", "Done")
                files = tool_input.get("files_modified", [])
                yap_updates = tool_input.get("yap_updates", [])

                print_header("Task Complete")
                print(f"{summary}\n")
                if files:
                    print(f"{Colors.BOLD}Files:{Colors.RESET}")
                    for f in files:
                        print(f"  {Colors.GREEN}• {f}{Colors.RESET}")
                if yap_updates:
                    print(f"\n{Colors.BOLD}YAP:{Colors.RESET}")
                    for f in yap_updates:
                        print(f"  {Colors.BLUE}• {f}{Colors.RESET}")
                return "TASK_COMPLETE"

            return f"Unknown tool: {tool_name}"
        except Exception as e:
            print_error(str(e))
            return f"Error: {e}"

    def _call_api(self, messages: list):
        return self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self.system_prompt,
            tools=TOOLS,
            messages=messages
        )
    
    def run(self, user_request: str, continue_conversation: bool = True) -> str:
        self.conversation_history.append({"role": "user", "content": user_request})
        messages = self.conversation_history.copy()
        
        max_iterations = 30
        for iteration in range(1, max_iterations + 1):
            try:
                response = self._call_api(messages)
            except KeyboardInterrupt:
                print_warning("Cancelled")
                return "Cancelled"

            if response.stop_reason == "end_turn":
                final_text = "".join(b.text for b in response.content if hasattr(b, "text"))
                if continue_conversation:
                    self.conversation_history.append({"role": "assistant", "content": response.content})
                print_agent("Response:")
                print(f"{final_text}\n")
                return final_text

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                final_text = "".join(b.text for b in response.content if hasattr(b, "text"))
                if continue_conversation:
                    self.conversation_history.append({"role": "assistant", "content": response.content})
                return final_text

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_use in tool_uses:
                result = self._execute_tool(tool_use.name, tool_use.input)

                # Compact tool output
                if result.startswith("Error:"):
                    print(f"  {Colors.RED}✗ {tool_use.name}: {result}{Colors.RESET}")
                else:
                    # Show tool name with brief summary
                    summary = self._get_tool_summary(tool_use.name, tool_use.input, result)
                    print(f"  {Colors.DIM}→ {summary}{Colors.RESET}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result
                })

                if result == "TASK_COMPLETE":
                    if continue_conversation:
                        self.conversation_history.append({"role": "assistant", "content": response.content})
                        self.conversation_history.append({"role": "user", "content": tool_results})
                    return "Task completed"

            messages.append({"role": "user", "content": tool_results})

        print_warning("Max iterations reached")
        return "Max iterations reached"

    def _get_tool_summary(self, tool_name: str, tool_input: dict, result: str) -> str:
        """Generate a concise summary of tool execution."""
        path = tool_input.get("path", "")
        if tool_name == "read_file":
            lines = result.count('\n')
            return f"read {path} ({lines} lines)"
        elif tool_name == "write_file":
            return f"wrote {path}"
        elif tool_name == "list_directory":
            items = result.count('\n')
            return f"listed {path} ({items} items)"
        elif tool_name == "read_yap_chain":
            return f"read YAP for {path}"
        elif tool_name == "update_yap":
            return f"updated {path}"
        elif tool_name == "mark_yap_implemented":
            return f"marked {path} implemented"
        elif tool_name == "task_complete":
            return "task complete"
        return f"{tool_name}"
    
    def clear_history(self):
        self.conversation_history = []
        print_success("History cleared")
    
    def check_for_changes(self) -> list:
        return self.yap_manager.get_changed_yap_files()

    def initialize_yap_guided(self):
        locations = self.yap_manager.get_recommended_yap_locations()
        if not locations:
            print_warning("No code files found")
            return

        print_info(f"Found {len(locations)} recommended YAP locations:")
        for i, loc in enumerate(locations):
            rel = loc.relative_to(self.yap_manager.project_root) if loc != self.yap_manager.project_root else Path(".")
            exists = (loc / self.yap_manager.yap_filename).exists()
            status = f"{Colors.GREEN}(exists){Colors.RESET}" if exists else f"{Colors.YELLOW}(missing){Colors.RESET}"
            print(f"  {i+1}. {rel}/ {status}")
        print()

        for loc in locations:
            rel = loc.relative_to(self.yap_manager.project_root) if loc != self.yap_manager.project_root else Path(".")
            yap_path = loc / self.yap_manager.yap_filename

            if yap_path.exists():
                continue

            print_subheader(f"Create YAP for: {rel}/")
            code_files = [f.name for f in loc.iterdir() if f.is_file() and not f.name.startswith('.')]
            if code_files:
                print(f"Files: {', '.join(code_files[:10])}")

            response = input(f"\nCreate YAP.md? [Y/n/skip all]: ").strip().lower()
            if response == 'skip all':
                break
            elif response in ('n', 'no'):
                continue

            self.run(f"""Create YAP.md for: {rel}/
Files: {', '.join(code_files)}

1. Read the files
2. Ask me about intent/decisions
3. Propose YAP structure
4. Wait for approval""")

            print()
            if input("Next location? [Y/n]: ").strip().lower() in ('n', 'no'):
                break
            self.clear_history()


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Yapper - Conversation-based coding")
    parser.add_argument("request", nargs="?", help="Task to perform")
    parser.add_argument("--project", "-p", default=".", help="Project root")
    parser.add_argument("--model", "-m", default="claude-sonnet-4-20250514")
    parser.add_argument("--init", action="store_true", help="Initialize YAP")
    parser.add_argument("--no-color", action="store_true")

    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    if not ensure_api_key():
        sys.exit(1)

    config = AgentConfig(model=args.model, project_root=args.project)
    agent = YapAgent(config)

    print_header("Yapper")
    print(f"Project: {Path(args.project).resolve()}\n")

    yap_files = agent.yap_manager.find_all_yap_files()

    if not yap_files and not args.init:
        print_warning("No YAP files found")
        if input("Initialize YAP? [Y/n]: ").strip().lower() not in ('n', 'no'):
            agent.initialize_yap_guided()
            yap_files = agent.yap_manager.find_all_yap_files()

    if args.init:
        agent.initialize_yap_guided()
        return

    # Check for pending YAP changes and show status
    initial_prompt = None
    if yap_files:
        changes = agent.check_for_changes()
        if changes:
            print_warning(f"{len(changes)} YAP file(s) with pending changes:")
            for path, stored_hash, current_hash, timestamp in changes:
                rel = path.relative_to(agent.yap_manager.project_root)
                if stored_hash:
                    print(f"  {Colors.YELLOW}• {rel}{Colors.RESET}")
                    print(f"    {Colors.DIM}Implemented: {timestamp} | {stored_hash} → {current_hash}{Colors.RESET}")
                else:
                    print(f"  {Colors.YELLOW}• {rel} (never implemented){Colors.RESET}")
            print()
        else:
            print_success(f"All {len(yap_files)} YAP file(s) up to date\n")

    # If a request was provided as argument, use that as the initial prompt
    if args.request:
        initial_prompt = args.request

    # Always enter interactive mode
    print_info("Commands: quit, clear, changes, mark <path>\n")

    while True:
        try:
            if initial_prompt:
                request = initial_prompt
                initial_prompt = None
            else:
                request = input(f"{Colors.BOLD}You:{Colors.RESET} ").strip()

            if not request:
                continue
            if request.lower() in ("quit", "exit"):
                break
            if request.lower() == "clear":
                agent.clear_history()
                continue
            if request.lower() == "changes":
                changes = agent.check_for_changes()
                if changes:
                    for path, *_ in changes:
                        print(f"  • {path.relative_to(agent.yap_manager.project_root)}")
                else:
                    print_success("All up to date")
                continue
            if request.lower().startswith("mark "):
                path = request[5:].strip()
                try:
                    agent.yap_manager.mark_implemented(agent.yap_manager.project_root / path)
                    print_success(f"Marked {path}")
                except Exception as e:
                    print_error(str(e))
                continue

            agent.run(request)
            print()
        except KeyboardInterrupt:
            print("\n")
            continue


if __name__ == "__main__":
    main()