#!/usr/bin/env python3
"""
ADL Agent - A conversation-based agentic coding tool.

Features:
- ADL change detection on startup
- Hash-based tracking of implementation status
- Rate limit handling with automatic retry
- Colored output with git-style diffs
- Guided ADL initialization for new repos
"""

import os
import sys
import json
import re
import hashlib
import time
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
    adl_filename: str = "ADL.md"
    retry_delay: int = 60
    max_retries: int = 5


# =============================================================================
# ADL Hash and Tracking
# =============================================================================

class ADLTracker:
    """Tracks ADL file changes via hash at end of file."""
    
    HASH_PATTERN = re.compile(
        r'\n---\n<!-- ADL-HASH: ([a-f0-9]+) \| implemented: (.+?) -->\s*$'
    )
    
    @staticmethod
    def compute_hash(content: str) -> str:
        content = ADLTracker.HASH_PATTERN.sub('', content)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    @staticmethod
    def get_hash_info(content: str) -> tuple[Optional[str], Optional[str]]:
        match = ADLTracker.HASH_PATTERN.search(content)
        if match:
            return match.group(1), match.group(2)
        return None, None
    
    @staticmethod
    def add_hash(content: str) -> str:
        content = ADLTracker.HASH_PATTERN.sub('', content)
        content = content.rstrip() + '\n'
        file_hash = ADLTracker.compute_hash(content)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"{content}\n---\n<!-- ADL-HASH: {file_hash} | implemented: {timestamp} -->\n"
    
    @staticmethod
    def has_changes(content: str) -> bool:
        stored_hash, _ = ADLTracker.get_hash_info(content)
        if stored_hash is None:
            return True
        current_hash = ADLTracker.compute_hash(content)
        return current_hash != stored_hash


# =============================================================================
# ADL File Management
# =============================================================================

class ADLManager:
    def __init__(self, project_root: str, adl_filename: str = "ADL.md"):
        self.project_root = Path(project_root).resolve()
        self.adl_filename = adl_filename
        self.tracker = ADLTracker()
    
    def find_all_adl_files(self) -> list[Path]:
        adl_files = []
        for path in self.project_root.rglob(self.adl_filename):
            adl_files.append(path)
        return sorted(adl_files, key=lambda p: len(p.parts))
    
    def get_adl_for_path(self, target_path: str) -> list[Path]:
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
        
        adl_chain = []
        for path in reversed(paths_to_check):
            adl_file = path / self.adl_filename
            if adl_file.exists():
                adl_chain.append(adl_file)
        
        return adl_chain
    
    def read_adl(self, adl_path: Path) -> str:
        return adl_path.read_text()
    
    def write_adl(self, adl_path: Path, content: str):
        adl_path.write_text(content)
    
    def mark_implemented(self, adl_path: Path):
        content = self.read_adl(adl_path)
        updated = self.tracker.add_hash(content)
        self.write_adl(adl_path, updated)
    
    def get_changed_adl_files(self) -> list[tuple[Path, str, str, str]]:
        changed = []
        for adl_file in self.find_all_adl_files():
            content = self.read_adl(adl_file)
            if self.tracker.has_changes(content):
                stored_hash, timestamp = self.tracker.get_hash_info(content)
                current_hash = self.tracker.compute_hash(content)
                changed.append((adl_file, stored_hash, current_hash, timestamp))
        return changed
    
    def get_project_context(self) -> str:
        adl_files = self.find_all_adl_files()
        if not adl_files:
            return "No ADL.md files found in project."
        
        context_parts = []
        for adl_file in adl_files:
            rel_path = adl_file.relative_to(self.project_root)
            content = self.read_adl(adl_file)
            context_parts.append(f"=== {rel_path} ===\n{content}")
        
        return "\n\n".join(context_parts)
    
    def get_recommended_adl_locations(self) -> list[Path]:
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
        "name": "read_adl_chain",
        "description": "Read ADL.md files relevant to a path. ALWAYS use before working on code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file/directory to work on"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "update_adl",
        "description": "Update an ADL.md file after agreeing on specs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to ADL.md file"},
                "content": {"type": "string", "description": "New content (preserve Notes section)"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "mark_adl_implemented",
        "description": "Mark ADL as implemented (updates hash). Use when done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to ADL.md file"}
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
                "adl_updates": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["summary"]
        }
    }
]


# =============================================================================
# Agent
# =============================================================================

class ADLAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = anthropic.Anthropic()
        self.adl_manager = ADLManager(config.project_root, config.adl_filename)
        self.file_manager = FileManager(config.project_root)
        self.conversation_history = []
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        system_prompt_path = Path(__file__).parent / "AGENT-SYSTEM-PROMPT.md"
        agent_instructions = system_prompt_path.read_text() if system_prompt_path.exists() else ""
        
        adl_spec_path = Path(__file__).parent / "ADL-SPEC.md"
        adl_spec = adl_spec_path.read_text() if adl_spec_path.exists() else ""
        
        project_context = self.adl_manager.get_project_context()
        
        return f"""You are an ADL-aligned coding agent. Turn human intent into specific specs through conversation, then implement.

## ADL Specification
{adl_spec}

## Agent Instructions
{agent_instructions}

## Current Project ADL
{project_context}

## Rules
1. CLARIFY vague intent before proposing specs
2. PROPOSE specs with intent/why/decided before implementing
3. WAIT for approval before coding
4. Use mark_adl_implemented when done
5. Use task_complete to summarize"""
    
    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        try:
            if tool_name == "read_file":
                content = self.file_manager.read_file(tool_input["path"])
                return f"Contents of {tool_input['path']}:\n\n{content}"
            
            elif tool_name == "write_file":
                return self.file_manager.write_file(tool_input["path"], tool_input["content"])
            
            elif tool_name == "list_directory":
                items = self.file_manager.list_directory(tool_input["path"])
                return f"Contents of {tool_input['path']}:\n" + "\n".join(items)
            
            elif tool_name == "read_adl_chain":
                adl_files = self.adl_manager.get_adl_for_path(tool_input["path"])
                if not adl_files:
                    return f"No ADL.md files found for: {tool_input['path']}"
                
                result_parts = []
                for adl_file in adl_files:
                    rel_path = adl_file.relative_to(self.adl_manager.project_root)
                    content = self.adl_manager.read_adl(adl_file)
                    has_changes = self.adl_manager.tracker.has_changes(content)
                    status = " (pending changes)" if has_changes else " (implemented)"
                    result_parts.append(f"=== {rel_path}{status} ===\n{content}")
                return "\n\n".join(result_parts)
            
            elif tool_name == "update_adl":
                adl_path = Path(tool_input["path"])
                if not adl_path.is_absolute():
                    adl_path = self.adl_manager.project_root / adl_path
                
                old_content = ""
                if adl_path.exists():
                    old_content = self.adl_manager.read_adl(adl_path)
                
                self.adl_manager.write_adl(adl_path, tool_input["content"])
                
                if old_content:
                    print_subheader(f"ADL Changes: {tool_input['path']}")
                    print_diff(old_content, tool_input["content"], tool_input["path"])
                else:
                    print_success(f"Created: {tool_input['path']}")
                
                return f"Updated {tool_input['path']}"
            
            elif tool_name == "mark_adl_implemented":
                adl_path = Path(tool_input["path"])
                if not adl_path.is_absolute():
                    adl_path = self.adl_manager.project_root / adl_path
                self.adl_manager.mark_implemented(adl_path)
                print_success(f"Marked {tool_input['path']} as implemented")
                return f"Marked {tool_input['path']} as implemented"
            
            elif tool_name == "task_complete":
                summary = tool_input.get("summary", "Done")
                files = tool_input.get("files_modified", [])
                adl_updates = tool_input.get("adl_updates", [])
                
                print_header("Task Complete")
                print(f"{summary}\n")
                if files:
                    print(f"{Colors.BOLD}Files:{Colors.RESET}")
                    for f in files:
                        print(f"  {Colors.GREEN}• {f}{Colors.RESET}")
                if adl_updates:
                    print(f"\n{Colors.BOLD}ADL:{Colors.RESET}")
                    for f in adl_updates:
                        print(f"  {Colors.BLUE}• {f}{Colors.RESET}")
                return "TASK_COMPLETE"
            
            return f"Unknown tool: {tool_name}"
        except Exception as e:
            print_error(str(e))
            return f"Error: {e}"
    
    def _call_api_with_retry(self, messages: list):
        retries = 0
        while retries < self.config.max_retries:
            try:
                return self.client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    system=self.system_prompt,
                    tools=TOOLS,
                    messages=messages
                )
            except anthropic.RateLimitError:
                retries += 1
                if retries >= self.config.max_retries:
                    raise
                
                print_warning(f"Rate limited. Waiting {self.config.retry_delay}s ({retries}/{self.config.max_retries})...")
                
                try:
                    for remaining in range(self.config.retry_delay, 0, -1):
                        print(f"\r{Colors.DIM}Resuming in {remaining}s... (Ctrl+C to cancel){Colors.RESET}", end="", flush=True)
                        time.sleep(1)
                    print("\r" + " " * 50 + "\r", end="")
                except KeyboardInterrupt:
                    print("\n")
                    raise
    
    def run(self, user_request: str, continue_conversation: bool = True) -> str:
        print_header("User Request")
        print(f"{user_request}\n")
        
        self.conversation_history.append({"role": "user", "content": user_request})
        messages = self.conversation_history.copy()
        
        max_iterations = 30
        for iteration in range(1, max_iterations + 1):
            print_subheader(f"Iteration {iteration}")
            
            try:
                response = self._call_api_with_retry(messages)
            except KeyboardInterrupt:
                print_warning("Cancelled")
                return "Cancelled"
            except anthropic.RateLimitError:
                print_error("Rate limit exceeded")
                return "Rate limit exceeded"
            
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
                print(f"  {Colors.CYAN}Tool:{Colors.RESET} {tool_use.name}")
                input_str = json.dumps(tool_use.input, indent=2)
                if len(input_str) > 200:
                    input_str = input_str[:200] + "..."
                print(f"  {Colors.DIM}Input: {input_str}{Colors.RESET}")
                
                result = self._execute_tool(tool_use.name, tool_use.input)
                result_display = result[:150] + "..." if len(result) > 150 else result
                print(f"  {Colors.DIM}Result: {result_display}{Colors.RESET}\n")
                
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
    
    def clear_history(self):
        self.conversation_history = []
        print_success("History cleared")
    
    def check_for_changes(self) -> list:
        return self.adl_manager.get_changed_adl_files()
    
    def initialize_adl_guided(self):
        locations = self.adl_manager.get_recommended_adl_locations()
        if not locations:
            print_warning("No code files found")
            return
        
        print_info(f"Found {len(locations)} recommended ADL locations:")
        for i, loc in enumerate(locations):
            rel = loc.relative_to(self.adl_manager.project_root) if loc != self.adl_manager.project_root else Path(".")
            exists = (loc / self.adl_manager.adl_filename).exists()
            status = f"{Colors.GREEN}(exists){Colors.RESET}" if exists else f"{Colors.YELLOW}(missing){Colors.RESET}"
            print(f"  {i+1}. {rel}/ {status}")
        print()
        
        for loc in locations:
            rel = loc.relative_to(self.adl_manager.project_root) if loc != self.adl_manager.project_root else Path(".")
            adl_path = loc / self.adl_manager.adl_filename
            
            if adl_path.exists():
                continue
            
            print_subheader(f"Create ADL for: {rel}/")
            code_files = [f.name for f in loc.iterdir() if f.is_file() and not f.name.startswith('.')]
            if code_files:
                print(f"Files: {', '.join(code_files[:10])}")
            
            response = input(f"\nCreate ADL.md? [Y/n/skip all]: ").strip().lower()
            if response == 'skip all':
                break
            elif response in ('n', 'no'):
                continue
            
            self.run(f"""Create ADL.md for: {rel}/
Files: {', '.join(code_files)}

1. Read the files
2. Ask me about intent/decisions  
3. Propose ADL structure
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
    
    parser = argparse.ArgumentParser(description="ADL Agent - Conversation-based coding")
    parser.add_argument("request", nargs="?", help="Task to perform")
    parser.add_argument("--project", "-p", default=".", help="Project root")
    parser.add_argument("--model", "-m", default="claude-sonnet-4-20250514")
    parser.add_argument("--interactive", "-i", action="store_true")
    parser.add_argument("--init", action="store_true", help="Initialize ADL")
    parser.add_argument("--no-color", action="store_true")
    
    args = parser.parse_args()
    
    if args.no_color:
        Colors.disable()
    
    config = AgentConfig(model=args.model, project_root=args.project)
    agent = ADLAgent(config)
    
    print_header("ADL Agent")
    print(f"Project: {Path(args.project).resolve()}\n")
    
    adl_files = agent.adl_manager.find_all_adl_files()
    
    if not adl_files and not args.init:
        print_warning("No ADL files found")
        if input("Initialize ADL? [Y/n]: ").strip().lower() not in ('n', 'no'):
            agent.initialize_adl_guided()
            adl_files = agent.adl_manager.find_all_adl_files()
    
    if args.init:
        agent.initialize_adl_guided()
        return
    
    if adl_files:
        changes = agent.check_for_changes()
        if changes:
            print_warning(f"{len(changes)} ADL file(s) with pending changes:")
            for path, stored_hash, current_hash, timestamp in changes:
                rel = path.relative_to(agent.adl_manager.project_root)
                if stored_hash:
                    print(f"  {Colors.YELLOW}• {rel}{Colors.RESET}")
                    print(f"    {Colors.DIM}Implemented: {timestamp} | {stored_hash} → {current_hash}{Colors.RESET}")
                else:
                    print(f"  {Colors.YELLOW}• {rel} (never implemented){Colors.RESET}")
            
            if input("\nReview changes? [Y/n]: ").strip().lower() not in ('n', 'no'):
                agent.run("Review ADL files with pending changes and summarize what needs implementation.")
        else:
            print_success(f"All {len(adl_files)} ADL file(s) up to date")
    
    print()
    
    if args.interactive:
        print_info("Commands: quit, clear, changes, mark <path>\n")
        
        while True:
            try:
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
                            print(f"  • {path.relative_to(agent.adl_manager.project_root)}")
                    else:
                        print_success("All up to date")
                    continue
                if request.lower().startswith("mark "):
                    path = request[5:].strip()
                    try:
                        agent.adl_manager.mark_implemented(agent.adl_manager.project_root / path)
                        print_success(f"Marked {path}")
                    except Exception as e:
                        print_error(str(e))
                    continue
                
                agent.run(request)
                print()
            except KeyboardInterrupt:
                print("\n")
                continue
    
    elif args.request:
        agent.run(args.request)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()