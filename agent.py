#!/usr/bin/env python3
"""
Yapper - A conversation-based agentic coding tool.

Features:
- .yap file change detection on startup
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
import time
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
    ORANGE = "\033[38;5;208m"
    
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


def get_diff_summary(old_content: str, new_content: str) -> tuple[int, int, int, int]:
    """Get diff summary: (lines_added, lines_removed, first_changed_line, last_changed_line)."""
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()

    # Find first differing line
    first_changed = 0
    for i, (old, new) in enumerate(zip(old_lines, new_lines)):
        if old != new:
            first_changed = i + 1
            break
    else:
        # One is longer than the other
        first_changed = min(len(old_lines), len(new_lines)) + 1

    # Find last differing line (from end)
    last_changed = max(len(old_lines), len(new_lines))
    for i, (old, new) in enumerate(zip(reversed(old_lines), reversed(new_lines))):
        if old != new:
            last_changed = max(len(old_lines), len(new_lines)) - i
            break

    # Count additions and removals using difflib
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    added = 0
    removed = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            removed += i2 - i1
            added += j2 - j1
        elif tag == 'delete':
            removed += i2 - i1
        elif tag == 'insert':
            added += j2 - j1

    return added, removed, first_changed, last_changed


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AgentConfig:
    model: str = "claude-opus-4-5-20251101"
    max_tokens: int = 8192
    max_read_lines: int = 100
    project_root: str = "."
    yap_extension: str = ".yap"
    project_yap: str = "project.yap"


# =============================================================================
# YAP Hash and Tracking
# =============================================================================

class YapTracker:
    """Tracks .yap file changes and code drift via hashes at end of file."""

    # New format: <!-- code: xxx | yap: yyy | 2024-01-15 14:30 -->
    HASH_PATTERN = re.compile(
        r'\n<!-- code: ([a-f0-9]+|none) \| yap: ([a-f0-9]+) \| (.+?) -->\s*$'
    )

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute hash of content, excluding the hash footer."""
        content = YapTracker.HASH_PATTERN.sub('', content)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def compute_code_hash(code_path: Path) -> str:
        """Compute hash of associated code file(s)."""
        if not code_path.exists():
            return "none"
        if code_path.is_file():
            return hashlib.sha256(code_path.read_bytes()).hexdigest()[:16]
        elif code_path.is_dir():
            # Hash all code files in directory
            code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c', '.h'}
            hasher = hashlib.sha256()
            for f in sorted(code_path.rglob('*')):
                if f.is_file() and f.suffix in code_extensions:
                    hasher.update(f.read_bytes())
            return hasher.hexdigest()[:16] if hasher.digest_size else "none"
        return "none"

    @staticmethod
    def get_hash_info(content: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Returns (code_hash, yap_hash, timestamp) or (None, None, None)."""
        match = YapTracker.HASH_PATTERN.search(content)
        if match:
            return match.group(1), match.group(2), match.group(3)
        return None, None, None

    @staticmethod
    def add_hash(content: str, code_hash: str = "none") -> str:
        """Add or update hash footer with both code and yap hashes."""
        content = YapTracker.HASH_PATTERN.sub('', content)
        content = content.rstrip() + '\n'
        yap_hash = YapTracker.compute_hash(content)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"{content}\n<!-- code: {code_hash} | yap: {yap_hash} | {timestamp} -->\n"

    @staticmethod
    def check_status(content: str, code_path: Optional[Path] = None) -> dict:
        """
        Check yap/code sync status.
        Returns dict with: yap_changed, code_changed, code_hash, yap_hash, timestamp
        """
        stored_code, stored_yap, timestamp = YapTracker.get_hash_info(content)
        current_yap = YapTracker.compute_hash(content)
        current_code = YapTracker.compute_code_hash(code_path) if code_path else "none"

        return {
            "yap_changed": stored_yap is None or stored_yap != current_yap,
            "code_changed": stored_code is not None and stored_code != "none" and stored_code != current_code,
            "stored_code_hash": stored_code,
            "stored_yap_hash": stored_yap,
            "current_code_hash": current_code,
            "current_yap_hash": current_yap,
            "timestamp": timestamp
        }


# =============================================================================
# YAP File Management
# =============================================================================

class YapManager:
    def __init__(self, project_root: str, yap_extension: str = ".yap", project_yap: str = "project.yap"):
        self.project_root = Path(project_root).resolve()
        self.yap_extension = yap_extension
        self.project_yap = project_yap
        self.tracker = YapTracker()

    def find_all_yap_files(self) -> list[Path]:
        """Find all .yap files in project."""
        yap_files = []
        for path in self.project_root.rglob(f"*{self.yap_extension}"):
            yap_files.append(path)
        return sorted(yap_files, key=lambda p: (len(p.parts), p.name))

    def get_code_path_for_yap(self, yap_path: Path) -> Optional[Path]:
        """Get the code file/directory associated with a .yap file."""
        if yap_path.name == self.project_yap:
            return self.project_root  # project.yap covers the whole project

        # foo.yap -> foo.py or foo/ directory
        base_name = yap_path.stem  # removes .yap
        parent = yap_path.parent

        # Check for code file with same name
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c']:
            code_file = parent / f"{base_name}{ext}"
            if code_file.exists():
                return code_file

        # Check for directory with same name
        code_dir = parent / base_name
        if code_dir.is_dir():
            return code_dir

        return None

    def get_yap_for_path(self, target_path: str) -> list[Path]:
        """Get relevant .yap files for a given code path."""
        target = Path(target_path)
        if not target.is_absolute():
            target = self.project_root / target
        target = target.resolve()

        yap_chain = []

        # Always include project.yap if it exists
        project_yap_path = self.project_root / self.project_yap
        if project_yap_path.exists():
            yap_chain.append(project_yap_path)

        # Look for specific .yap file for this code
        if target.is_file():
            # foo.py -> foo.yap
            specific_yap = target.parent / f"{target.stem}{self.yap_extension}"
            if specific_yap.exists():
                yap_chain.append(specific_yap)
        elif target.is_dir():
            # foo/ -> foo.yap (in parent) or foo/project.yap
            specific_yap = target.parent / f"{target.name}{self.yap_extension}"
            if specific_yap.exists():
                yap_chain.append(specific_yap)
            # Also check for .yap files inside the directory
            for yap_file in sorted(target.glob(f"*{self.yap_extension}")):
                if yap_file not in yap_chain:
                    yap_chain.append(yap_file)

        return yap_chain

    def read_yap(self, yap_path: Path) -> str:
        return yap_path.read_text()

    def write_yap(self, yap_path: Path, content: str):
        yap_path.write_text(content)

    def mark_implemented(self, yap_path: Path):
        """Mark yap as implemented, computing both yap and code hashes."""
        content = self.read_yap(yap_path)
        code_path = self.get_code_path_for_yap(yap_path)
        code_hash = self.tracker.compute_code_hash(code_path) if code_path else "none"
        updated = self.tracker.add_hash(content, code_hash)
        self.write_yap(yap_path, updated)

    def read_yap_section(self, yap_path: Path, section_name: str) -> tuple[str, bool]:
        """Read a specific section from a YAP file. Returns (section_content, found)."""
        content = self.read_yap(yap_path)
        lines = content.split('\n')

        # Normalize section name for comparison
        target = section_name.lower().strip()
        if not target.startswith('## '):
            target = f"## {target}"
        target = target.lower()

        section_start = None
        section_end = None

        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            if line_lower == target or (line_lower.startswith('## ') and target.replace('## ', '') in line_lower):
                section_start = i
            elif section_start is not None and line.strip().startswith('## '):
                section_end = i
                break

        if section_start is None:
            return "", False

        if section_end is None:
            section_end = len(lines)

        # Return section content (including header)
        section_lines = lines[section_start:section_end]
        return '\n'.join(section_lines).strip(), True

    def write_yap_section(self, yap_path: Path, section_name: str, section_content: str) -> str:
        """Write/replace a specific section in a YAP file. Returns status message."""
        content = self.read_yap(yap_path)
        lines = content.split('\n')

        # Normalize section name
        target = section_name.lower().strip()
        if not target.startswith('## '):
            target = f"## {target}"
        target = target.lower()

        section_start = None
        section_end = None

        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            if line_lower == target or (line_lower.startswith('## ') and target.replace('## ', '') in line_lower):
                section_start = i
            elif section_start is not None and line.strip().startswith('## '):
                section_end = i
                break

        # Ensure section_content has proper header
        content_lines = section_content.strip().split('\n')
        if not content_lines[0].strip().startswith('## '):
            content_lines.insert(0, f"## {section_name.replace('## ', '').title()}")

        if section_start is None:
            # Section doesn't exist, append it before the hash footer if present
            hash_match = self.tracker.HASH_PATTERN.search(content)
            if hash_match:
                insert_pos = content.find('\n---\n<!-- YAP-HASH:')
                new_content = content[:insert_pos] + '\n' + '\n'.join(content_lines) + '\n' + content[insert_pos:]
            else:
                new_content = content.rstrip() + '\n\n' + '\n'.join(content_lines) + '\n'
            self.write_yap(yap_path, new_content)
            return f"Added section '{section_name}'"

        if section_end is None:
            section_end = len(lines)

        # Replace the section
        new_lines = lines[:section_start] + content_lines + [''] + lines[section_end:]
        new_content = '\n'.join(new_lines)

        old_section_len = section_end - section_start
        new_section_len = len(content_lines)

        self.write_yap(yap_path, new_content)
        return f"Updated section '{section_name}' ({Colors.GREEN}+{new_section_len}{Colors.RESET}, {Colors.RED}-{old_section_len}{Colors.RESET} lines)"

    def clear_yap_here(self, yap_path: Path) -> tuple[str, bool]:
        """Clear the 'Yap Here' section. Returns (updated_content, had_human_notes)."""
        content = self.read_yap(yap_path)
        lines = content.split('\n')

        yap_here_start = None
        yap_here_end = None
        had_human_notes = False

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for "## Yap Here" section
            if line.lower() == "## yap here":
                yap_here_start = i
                i += 1

                # Collect content until next ## section or end of file
                while i < len(lines):
                    line = lines[i].strip()

                    # Stop at next section
                    if line.startswith('## ') and not line.lower().startswith('## yap here'):
                        yap_here_end = i
                        break

                    # Check for human notes (non-comment, non-agent content)
                    if (line and
                        not line.startswith('<!--') and
                        not line.startswith('-->') and
                        not line.startswith('### Agent Working State') and
                        not line.startswith('- **Implementation Status') and
                        not line.startswith('- **Active') and
                        not line.startswith('- **Next')):
                        if not any(marker in line for marker in ['AGENT:', 'Agent Working State']):
                            had_human_notes = True

                    i += 1

                # If no next section found, end at file end
                if yap_here_end is None:
                    yap_here_end = len(lines)
                break
            i += 1

        if yap_here_start is None:
            # No "Yap Here" section found
            return content, False

        # Create cleared section
        cleared_section = [
            "## Yap Here",
            "",
            "<!--",
            "Yap yap, write down your thoughts here and the agent will take care of it..",
            "-->"
        ]

        # Replace the section
        new_lines = lines[:yap_here_start] + cleared_section + lines[yap_here_end:]

        return '\n'.join(new_lines), had_human_notes

    def get_pending_tasks(self, yap_path: Path) -> list[str]:
        """Extract pending tasks from Yap Here section."""
        content = self.read_yap(yap_path)
        tasks = []

        # Look for pending items in various formats:
        # <!-- Pending implementation: - [ ] Task1 -->
        # <!-- Pending: - item1 - item2 -->
        import re
        pending_pattern = re.compile(r'<!--\s*Pending[^:]*:(.*?)-->', re.DOTALL | re.IGNORECASE)
        matches = pending_pattern.findall(content)

        for match in matches:
            # Extract individual items (- [ ] item or - item)
            items = re.findall(r'-\s*(?:\[\s*\])?\s*(.+?)(?=\n-|\n*$)', match, re.DOTALL)
            tasks.extend([item.strip() for item in items if item.strip()])

        return tasks

    def add_pending_task(self, yap_path: Path, task: str) -> str:
        """Add a pending task to Yap Here section."""
        content = self.read_yap(yap_path)

        # Check if there's already a pending block
        import re
        pending_pattern = re.compile(r'(<!--\s*Pending[^:]*:)(.*?)(-->)', re.DOTALL | re.IGNORECASE)
        match = pending_pattern.search(content)

        if match:
            # Add to existing pending block
            prefix, existing, suffix = match.groups()
            new_item = f"\n- [ ] {task}"
            new_block = f"{prefix}{existing.rstrip()}{new_item}\n{suffix}"
            new_content = content[:match.start()] + new_block + content[match.end():]
        else:
            # Create new pending block in Yap Here
            yap_here_pattern = re.compile(r'(## Yap Here\n)', re.IGNORECASE)
            yap_match = yap_here_pattern.search(content)

            if yap_match:
                pending_block = f"\n<!-- Pending implementation:\n- [ ] {task}\n-->\n"
                insert_pos = yap_match.end()
                new_content = content[:insert_pos] + pending_block + content[insert_pos:]
            else:
                # No Yap Here section, add one
                hash_match = self.tracker.HASH_PATTERN.search(content)
                pending_block = f"\n## Yap Here\n\n<!-- Pending implementation:\n- [ ] {task}\n-->\n"
                if hash_match:
                    insert_pos = hash_match.start()
                    new_content = content[:insert_pos].rstrip() + pending_block + "\n" + content[insert_pos:]
                else:
                    new_content = content.rstrip() + pending_block

        self.write_yap(yap_path, new_content)
        return f"Added pending task: {task}"

    def complete_pending_task(self, yap_path: Path, task: str) -> str:
        """Mark a pending task as complete. Returns status message."""
        content = self.read_yap(yap_path)

        import re
        pending_pattern = re.compile(r'(<!--\s*Pending[^:]*:)(.*?)(-->)', re.DOTALL | re.IGNORECASE)
        match = pending_pattern.search(content)

        if not match:
            return "No pending tasks found"

        prefix, task_block, suffix = match.groups()

        # Find and remove the matching task
        task_lower = task.lower()
        lines = task_block.strip().split('\n')
        new_lines = []
        found = False

        for line in lines:
            # Check if this line contains the task (partial match)
            line_content = re.sub(r'^-\s*(?:\[\s*\])?\s*', '', line.strip())
            if task_lower in line_content.lower() and not found:
                found = True
                continue  # Remove this task
            new_lines.append(line)

        if not found:
            return f"Task not found: {task}"

        # Check if all tasks are done
        remaining_tasks = [l for l in new_lines if l.strip() and l.strip().startswith('-')]

        if not remaining_tasks:
            # All done - replace with "All implemented"
            new_block = "<!-- All implemented -->"
        else:
            new_block = f"{prefix}\n" + '\n'.join(new_lines) + f"\n{suffix}"

        new_content = content[:match.start()] + new_block + content[match.end():]
        self.write_yap(yap_path, new_content)

        if not remaining_tasks:
            return f"Completed task: {task}. All tasks done!"
        return f"Completed task: {task}. {len(remaining_tasks)} remaining."

    def get_all_implementation_status(self) -> list[dict]:
        """Get implementation status of all yap files including pending tasks."""
        results = []
        for yap_file in self.find_all_yap_files():
            content = self.read_yap(yap_file)
            code_path = self.get_code_path_for_yap(yap_file)
            status = self.tracker.check_status(content, code_path)
            pending_tasks = self.get_pending_tasks(yap_file)

            # Check for "All implemented" marker
            all_implemented = "<!-- all implemented -->" in content.lower()

            results.append({
                "path": yap_file,
                "code_path": code_path,
                "yap_changed": status["yap_changed"],
                "code_changed": status["code_changed"],
                "pending_tasks": pending_tasks,
                "all_implemented": all_implemented and not pending_tasks,
                "timestamp": status["timestamp"],
            })
        return results

    def get_changed_yap_files(self) -> list[dict]:
        """
        Get all yap files with changes (either yap or code changed).
        Returns list of dicts with: path, yap_changed, code_changed, status info
        """
        results = []
        for yap_file in self.find_all_yap_files():
            content = self.read_yap(yap_file)
            code_path = self.get_code_path_for_yap(yap_file)
            status = self.tracker.check_status(content, code_path)

            if status["yap_changed"] or status["code_changed"]:
                results.append({
                    "path": yap_file,
                    "code_path": code_path,
                    "yap_changed": status["yap_changed"],
                    "code_changed": status["code_changed"],
                    "timestamp": status["timestamp"],
                    "stored_yap_hash": status["stored_yap_hash"],
                    "current_yap_hash": status["current_yap_hash"],
                    "stored_code_hash": status["stored_code_hash"],
                    "current_code_hash": status["current_code_hash"],
                })
        return results

    def get_project_context(self) -> str:
        yap_files = self.find_all_yap_files()
        if not yap_files:
            return "No .yap files found in project."

        context_parts = []
        for yap_file in yap_files:
            rel_path = yap_file.relative_to(self.project_root)
            content = self.read_yap(yap_file)
            context_parts.append(f"=== {rel_path} ===\n{content}")

        return "\n\n".join(context_parts)

    def get_recommended_yap_locations(self) -> list[dict]:
        """
        Get recommended .yap files to create.
        Returns list of dicts with: yap_path, code_path, type (project/file/dir)
        """
        recommendations = []
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java', '.cpp', '.c', '.h'}

        # Always recommend project.yap
        project_yap = self.project_root / self.project_yap
        if not project_yap.exists():
            recommendations.append({
                "yap_path": project_yap,
                "code_path": self.project_root,
                "type": "project"
            })

        # Find significant code files that don't have yap files
        for item in self.project_root.rglob('*'):
            if item.is_file() and item.suffix in code_extensions:
                # Skip small files and __init__.py
                if item.name.startswith('__'):
                    continue
                try:
                    lines = len(item.read_text().splitlines())
                    if lines < 50:  # Skip small files
                        continue
                except:
                    continue

                yap_path = item.parent / f"{item.stem}{self.yap_extension}"
                if not yap_path.exists():
                    recommendations.append({
                        "yap_path": yap_path,
                        "code_path": item,
                        "type": "file"
                    })

        return sorted(recommendations, key=lambda r: (r["type"] != "project", str(r["yap_path"])))


# =============================================================================
# File Protection (Yapignore)
# =============================================================================

class YapIgnore:
    """Handles .yapignore file parsing and file protection checking."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.yapignore_path = self.project_root / '.yapignore'
        self.patterns = []
        self._load_patterns()
    
    def _load_patterns(self):
        """Load patterns from .yapignore file."""
        self.patterns = []
        if not self.yapignore_path.exists():
            return
            
        try:
            content = self.yapignore_path.read_text()
            for line in content.splitlines():
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                self.patterns.append(line)
        except (UnicodeDecodeError, PermissionError):
            # If .yapignore is unreadable, just use empty patterns
            pass
    
    def is_protected(self, path: str) -> tuple[bool, str]:
        """
        Check if a file is protected by yapignore patterns.
        Returns (is_protected, matching_pattern).
        """
        if not self.patterns:
            return False, ""
            
        # Convert path to Path object and make it relative to project root
        file_path = Path(path)
        if file_path.is_absolute():
            try:
                rel_path = file_path.relative_to(self.project_root)
            except ValueError:
                # Path is outside project root, not protected
                return False, ""
        else:
            rel_path = file_path
        
        # Convert to forward slashes for consistent pattern matching
        path_str = str(rel_path).replace('\\', '/')
        
        # Check each pattern (most specific match wins)
        matched_pattern = ""
        is_ignored = False
        
        for pattern in self.patterns:
            if pattern.startswith('!'):
                # Negation pattern - if this matches, file is NOT ignored
                neg_pattern = pattern[1:]
                if self._pattern_matches(neg_pattern, path_str, rel_path):
                    is_ignored = False
                    matched_pattern = ""
            else:
                # Normal ignore pattern
                if self._pattern_matches(pattern, path_str, rel_path):
                    is_ignored = True
                    matched_pattern = pattern
        
        return is_ignored, matched_pattern
    
    def _pattern_matches(self, pattern: str, path_str: str, rel_path: Path) -> bool:
        """Check if a gitignore-style pattern matches the given path."""
        import fnmatch
        
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            # Only matches directories
            pattern = pattern[:-1]
            if not (self.project_root / rel_path).is_dir():
                return False
        
        # Handle patterns starting with /
        if pattern.startswith('/'):
            # Absolute pattern (from project root)
            pattern = pattern[1:]
            return fnmatch.fnmatch(path_str, pattern)
        
        # Handle patterns with **/ (recursive directory match)
        if '**/' in pattern:
            # Convert ** to * for basic fnmatch
            simple_pattern = pattern.replace('**/', '*/')
            return fnmatch.fnmatch(path_str, simple_pattern) or \
                   any(fnmatch.fnmatch(str(Path(*path_parts)), simple_pattern) 
                       for i in range(len(rel_path.parts)) 
                       for path_parts in [rel_path.parts[i:]])
        
        # Regular pattern - check if it matches the filename or any parent path
        if fnmatch.fnmatch(path_str, pattern):
            return True
        if fnmatch.fnmatch(rel_path.name, pattern):
            return True
        
        # Check if pattern matches any part of the path
        parts = rel_path.parts
        for i in range(len(parts)):
            partial_path = '/'.join(parts[i:])
            if fnmatch.fnmatch(partial_path, pattern):
                return True
                
        return False
    
    def create_default_yapignore(self):
        """Create a default .yapignore file with common protection patterns."""
        if self.yapignore_path.exists():
            return False  # Don't overwrite existing file
            
        default_patterns = [
            "# Yapper ignore file - protects sensitive files from agent access",
            "# Uses gitignore syntax: https://git-scm.com/docs/gitignore",
            "",
            "# Environment files with secrets",
            ".env*",
            "",
            "# Cryptographic keys", 
            "*.key",
            "*.pem",
            "*.crt",
            "*.p12",
            "",
            "# Cache and build directories",
            "__pycache__/",
            "node_modules/",
            ".pytest_cache/",
            "build/",
            "dist/",
            "",
            "# Log files",
            "*.log",
            "logs/",
            "",
            "# Version control",
            ".git/",
            "",
            "# IDE files",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "",
            "# OS files",
            ".DS_Store",
            "Thumbs.db"
        ]
        
        self.yapignore_path.write_text('\n'.join(default_patterns) + '\n')
        self._load_patterns()  # Reload patterns
        return True


# =============================================================================
# File Operations
# =============================================================================

class FileManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self._file_cache = {}
        self.yapignore = YapIgnore(project_root)

    def read_file(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None, max_lines: int = 100) -> tuple[str, int, bool]:
        """Read file content, optionally a specific line range. Returns (content, total_lines, was_truncated)."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Check yapignore protection
        is_protected, pattern = self.yapignore.is_protected(path)
        if is_protected:
            raise PermissionError(f"File '{path}' is protected by .yapignore (pattern: '{pattern}')")

        content = full_path.read_text()
        self._file_cache[str(full_path)] = content
        lines = content.splitlines()
        total_lines = len(lines)

        start = (start_line or 1) - 1  # Convert to 0-indexed
        end = end_line or total_lines

        # Enforce max_lines limit
        requested_lines = end - start
        was_truncated = requested_lines > max_lines
        if was_truncated:
            end = start + max_lines

        selected_lines = lines[start:end]
        # Add line numbers
        numbered = [f"{i+start+1:4d}│ {line}" for i, line in enumerate(selected_lines)]
        return "\n".join(numbered), total_lines, was_truncated

    def search_files(self, pattern: str, path: str = ".", max_results: int = 20) -> tuple[list[dict], list[dict]]:
        """
        Search for pattern in files.
        Returns (results, protected_matches) where:
        - results: list of {file, line, content} for accessible files
        - protected_matches: list of {file, pattern} for protected files that matched
        """
        search_path = self._resolve_path(path)
        results = []
        protected_matches = []

        # Compile regex
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            # Fall back to literal search
            regex = re.compile(re.escape(pattern), re.IGNORECASE)

        def search_file(file_path: Path):
            try:
                # Check yapignore protection for this file
                rel_path = str(file_path.relative_to(self.project_root))
                is_protected, prot_pattern = self.yapignore.is_protected(rel_path)

                content = file_path.read_text()
                has_match = False
                for i, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        has_match = True
                        if is_protected:
                            # Record that this protected file has matches
                            protected_matches.append({
                                "file": rel_path,
                                "pattern": prot_pattern
                            })
                            break  # Only record once per file
                        else:
                            results.append({
                                "file": rel_path,
                                "line": i,
                                "content": line.strip()[:100]
                            })
                            if len(results) >= max_results:
                                return True
            except (UnicodeDecodeError, PermissionError):
                pass
            return False

        if search_path.is_file():
            # Check if the specific file is protected
            rel_path = str(search_path.relative_to(self.project_root))
            is_protected, prot_pattern = self.yapignore.is_protected(rel_path)
            if is_protected:
                raise PermissionError(f"File '{rel_path}' is protected by .yapignore (pattern: '{prot_pattern}')")
            search_file(search_path)
        else:
            for file_path in search_path.rglob("*"):
                if file_path.is_file() and not any(p.startswith('.') for p in file_path.parts):
                    if search_file(file_path):
                        break

        return results, protected_matches

    def file_info(self, path: str) -> dict:
        """Get file metadata without reading full content."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Check yapignore protection
        is_protected, pattern = self.yapignore.is_protected(path)
        if is_protected:
            raise PermissionError(f"File '{path}' is protected by .yapignore (pattern: '{pattern}')")

        stat = full_path.stat()
        content = full_path.read_text()
        lines = content.splitlines()

        return {
            "path": path,
            "size_bytes": stat.st_size,
            "lines": len(lines),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        }
    
    def write_file(self, path: str, content: str) -> str:
        full_path = self._resolve_path(path)
        
        # Check yapignore protection
        is_protected, pattern = self.yapignore.is_protected(path)
        if is_protected:
            raise PermissionError(f"File '{path}' is protected by .yapignore (pattern: '{pattern}')")
        
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        old_content = self._file_cache.get(str(full_path), "")
        if not old_content and full_path.exists():
            old_content = full_path.read_text()
        
        full_path.write_text(content)
        self._file_cache[str(full_path)] = content
        
        if old_content and old_content != content:
            added, removed, first_line, last_line = get_diff_summary(old_content, content)
            lines_info = f"line {first_line}" if first_line == last_line else f"lines {first_line}-{last_line}"
            return f"Successfully wrote to {path} ({Colors.GREEN}+{added}{Colors.RESET}, {Colors.RED}-{removed}{Colors.RESET} @ {lines_info})"
        elif not old_content:
            line_count = content.count('\n') + 1
            return f"Created {path} ({line_count} lines)"

        return f"Successfully wrote to {path} (no changes)"

    def edit_file(self, path: str, old_string: str, new_string: str) -> str:
        """Edit a file by replacing old_string with new_string."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Check yapignore protection
        is_protected, pattern = self.yapignore.is_protected(path)
        if is_protected:
            raise PermissionError(f"File '{path}' is protected by .yapignore (pattern: '{pattern}')")

        content = full_path.read_text()

        # Check if old_string exists
        if old_string not in content:
            # Try to find similar content for helpful error
            lines = content.splitlines()
            first_line = old_string.splitlines()[0] if old_string else ""
            for i, line in enumerate(lines):
                if first_line and first_line.strip() in line:
                    context = "\n".join(lines[max(0, i-2):i+3])
                    return f"Error: old_string not found. Similar content at line {i+1}:\n{context}"
            return "Error: old_string not found in file. Read the file first to get exact content."

        # Check for multiple occurrences
        count = content.count(old_string)
        if count > 1:
            return f"Error: old_string appears {count} times. Make it more specific to match exactly once."

        # Perform the replacement
        new_content = content.replace(old_string, new_string)
        self._file_cache[str(full_path)] = new_content
        full_path.write_text(new_content)

        # Get diff summary
        added, removed, first_line, last_line = get_diff_summary(content, new_content)
        lines_info = f"line {first_line}" if first_line == last_line else f"lines {first_line}-{last_line}"

        return f"Edited {path} ({Colors.GREEN}+{added}{Colors.RESET}, {Colors.RED}-{removed}{Colors.RESET} @ {lines_info})"

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

    def remove_file(self, path: str) -> str:
        """Remove a file. Cannot remove directories."""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if full_path.is_dir():
            raise IsADirectoryError(f"Cannot remove directory: {path}. Use rmdir for empty directories.")

        # Check yapignore protection
        is_protected, pattern = self.yapignore.is_protected(path)
        if is_protected:
            raise PermissionError(f"File '{path}' is protected by .yapignore (pattern: '{pattern}')")

        # Remove from cache if present
        cache_key = str(full_path)
        if cache_key in self._file_cache:
            del self._file_cache[cache_key]

        # Delete the file
        full_path.unlink()
        return f"Removed {path}"
    
    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return (self.project_root / p).resolve()
    
    def reload_yapignore(self):
        """Reload .yapignore patterns (useful if .yapignore file was modified)."""
        self.yapignore._load_patterns()
    
    def check_protection(self, path: str) -> tuple[bool, str]:
        """Check if a file is protected. Returns (is_protected, matching_pattern)."""
        return self.yapignore.is_protected(path)

    def list_functions(self, path: str) -> list[dict]:
        """List all functions/methods in a Python or JavaScript/TypeScript file with line numbers and signatures."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Check yapignore protection
        is_protected, pattern = self.yapignore.is_protected(path)
        if is_protected:
            raise PermissionError(f"File '{path}' is protected by .yapignore (pattern: '{pattern}')")

        if path.endswith('.py'):
            return self._list_python_functions(full_path, path)
        elif any(path.endswith(ext) for ext in ['.js', '.ts', '.jsx', '.tsx', '.mjs', '.mts']):
            return self._list_js_functions(full_path)
        else:
            raise ValueError(f"Only Python and JavaScript/TypeScript files supported, got: {path}")

    def _list_python_functions(self, full_path: Path, path: str) -> list[dict]:
        """List functions in a Python file using AST."""
        import ast

        content = full_path.read_text()
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {path}: {e}")

        functions = []

        def get_signature(node):
            """Extract function signature."""
            args = []
            # Regular args
            for arg in node.args.args:
                arg_str = arg.arg
                if arg.annotation:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                args.append(arg_str)
            # *args
            if node.args.vararg:
                args.append(f"*{node.args.vararg.arg}")
            # **kwargs
            if node.args.kwarg:
                args.append(f"**{node.args.kwarg.arg}")

            returns = ""
            if node.returns:
                returns = f" -> {ast.unparse(node.returns)}"

            return f"({', '.join(args)}){returns}"

        def visit_node(node, class_name=None):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                name = node.name
                if class_name:
                    name = f"{class_name}.{name}"

                # Get first line of docstring if present
                docstring = ""
                if (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)):
                    doc = node.body[0].value.value.strip()
                    first_line = doc.split('\n')[0]
                    if len(first_line) > 60:
                        first_line = first_line[:57] + "..."
                    docstring = first_line

                functions.append({
                    "name": name,
                    "line": node.lineno,
                    "signature": get_signature(node),
                    "docstring": docstring,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })

            elif isinstance(node, ast.ClassDef):
                # Visit methods within classes
                for child in node.body:
                    visit_node(child, class_name=node.name)

        for node in ast.walk(tree):
            if isinstance(node, ast.Module):
                for child in node.body:
                    visit_node(child)

        # Sort by line number
        functions.sort(key=lambda f: f["line"])
        return functions

    def _list_js_functions(self, full_path: Path) -> list[dict]:
        """List functions in a JavaScript/TypeScript file using regex patterns."""
        content = full_path.read_text()
        lines = content.split('\n')
        functions = []

        # Patterns for different JS/TS function styles
        patterns = [
            # Regular function: function name(args) or async function name(args)
            (r'^(\s*)(export\s+)?(async\s+)?function\s+(\w+)\s*(<[^>]+>)?\s*\(([^)]*)\)', 'function'),
            # Arrow function: const name = (args) => or const name = async (args) =>
            (r'^(\s*)(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\(?([^)=]*)\)?\s*=>', 'arrow'),
            # Method in class/object: name(args) { or async name(args) {
            (r'^(\s*)(public\s+|private\s+|protected\s+|static\s+|async\s+)*(readonly\s+)?(\w+)\s*(<[^>]+>)?\s*\(([^)]*)\)\s*(:\s*[^{]+)?\s*\{', 'method'),
            # Class declaration: class Name
            (r'^(\s*)(export\s+)?(abstract\s+)?class\s+(\w+)', 'class'),
        ]

        current_class = None
        class_indent = -1

        for line_num, line in enumerate(lines, 1):
            # Track class context based on indentation
            if current_class:
                line_indent = len(line) - len(line.lstrip())
                if line.strip() and line_indent <= class_indent:
                    current_class = None
                    class_indent = -1

            for pattern, func_type in patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()

                    if func_type == 'class':
                        current_class = groups[3]
                        class_indent = len(groups[0]) if groups[0] else 0
                        continue

                    name = ""
                    params = ""
                    is_async = False

                    if func_type == 'function':
                        is_async = bool(groups[2])
                        name = groups[3]
                        params = groups[5] if groups[5] else ""
                    elif func_type == 'arrow':
                        is_async = bool(groups[4])
                        name = groups[3]
                        params = groups[5] if groups[5] else ""
                    elif func_type == 'method':
                        modifiers = groups[1] or ""
                        is_async = 'async' in modifiers
                        name = groups[3]
                        params = groups[5] if groups[5] else ""
                        # Skip constructor-like patterns that aren't actually methods
                        if name in ('if', 'for', 'while', 'switch', 'catch'):
                            continue

                    # Clean up params
                    params = params.strip()
                    if len(params) > 50:
                        params = params[:47] + "..."

                    full_name = f"{current_class}.{name}" if current_class and func_type == 'method' else name

                    functions.append({
                        "name": full_name,
                        "line": line_num,
                        "signature": f"({params})",
                        "docstring": "",  # Could parse JSDoc but keeping it simple
                        "is_async": is_async
                    })
                    break

        # Sort by line number
        functions.sort(key=lambda f: f["line"])
        return functions


# =============================================================================
# Tools
# =============================================================================

TOOLS = [
    {
        "name": "read_file",
        "description": "Read file contents. LIMITED TO 100 LINES per call. Use start_line to paginate through larger files. Use file_info first to check total lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file relative to project root"},
                "start_line": {"type": "integer", "description": "First line to read (1-indexed, default: 1)"},
                "end_line": {"type": "integer", "description": "Last line to read (max 100 lines from start_line)"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "file_info",
        "description": "Get file metadata (size, line count) without reading content. Use before read_file on unknown files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for pattern in files. Returns matching lines with file paths and line numbers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "File or directory to search in (default: project root)"},
                "max_results": {"type": "integer", "description": "Maximum results to return (default: 20)"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "edit_file",
        "description": "Edit a file by replacing old_string with new_string. PREFERRED over write_file for existing files. old_string must match exactly once.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file"},
                "old_string": {"type": "string", "description": "Exact string to find (must be unique in file)"},
                "new_string": {"type": "string", "description": "String to replace it with"}
            },
            "required": ["path", "old_string", "new_string"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a NEW file. Use edit_file for existing files. Creates directories if needed.",
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
        "name": "remove_file",
        "description": "Delete a file. Use with caution. Cannot remove directories or .yap files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file to delete"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_functions",
        "description": "List all functions/methods in a Python or JavaScript/TypeScript file with line numbers and signatures. Efficient way to understand file structure without reading entire content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to code file (.py, .js, .ts, .jsx, .tsx, .mjs, .mts)"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "read_yap_chain",
        "description": "Read .yap files relevant to a path (project.yap + specific file.yap). ALWAYS use before working on code.",
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
        "description": "Update a .yap file after agreeing on specs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to .yap file"},
                "content": {"type": "string", "description": "New content"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "mark_yap_implemented",
        "description": "Mark .yap as implemented (updates yap and code hashes). Use when done syncing yap with code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to .yap file"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "read_yap_section",
        "description": "Read a specific section from a .yap file. More efficient than reading entire file. Sections: 'Yap Here', 'What This Does', 'Key Decisions', 'Contracts', etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to .yap file"},
                "section": {"type": "string", "description": "Section name (e.g., 'Yap Here', 'What This Does', 'Key Decisions')"}
            },
            "required": ["path", "section"]
        }
    },
    {
        "name": "write_yap_section",
        "description": "Write/update a specific section in a .yap file. Creates section if it doesn't exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to .yap file"},
                "section": {"type": "string", "description": "Section name (e.g., 'Yap Here', 'What This Does', 'Key Decisions')"},
                "content": {"type": "string", "description": "New content for the section (header will be auto-added if missing)"}
            },
            "required": ["path", "section", "content"]
        }
    },
    {
        "name": "clear_yap_here",
        "description": "Clear 'Yap Here' section after marking .yap as implemented.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to .yap file"},
                "preserve_human_notes": {"type": "boolean", "description": "If true, ask human before clearing if notes found"}
            },
            "required": ["path"]
        }
    },
    # Implementation state tools
    {
        "name": "get_implementation_status",
        "description": "Get implementation status of all .yap files. Shows which have pending tasks, code drift, or are fully synced.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "add_pending_task",
        "description": "Add a pending implementation task to a .yap file's 'Yap Here' section.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to .yap file"},
                "task": {"type": "string", "description": "Task description to add"}
            },
            "required": ["path", "task"]
        }
    },
    {
        "name": "complete_pending_task",
        "description": "Mark a pending task as complete in a .yap file. If all tasks done, updates to 'All implemented'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to .yap file"},
                "task": {"type": "string", "description": "Task to mark complete (partial match OK)"}
            },
            "required": ["path", "task"]
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
    },
    # Reference management tools
    {
        "name": "list_refs",
        "description": "List all stored references with their summaries. Everything becomes a reference: tool outputs, actions, decisions, conversation. Auto-reviewed each turn.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "select_refs",
        "description": "Select references to include in your working context. Selected refs are injected into each API call. Use for content you need to work with.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ref_ids": {"type": "array", "items": {"type": "string"}, "description": "Reference IDs to select (e.g., ['ref_1', 'ref_3'])"}
            },
            "required": ["ref_ids"]
        }
    },
    {
        "name": "deselect_refs",
        "description": "Remove references from working context. Use when done with content to reduce token usage.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ref_ids": {"type": "array", "items": {"type": "string"}, "description": "Reference IDs to deselect. Use ['all'] to clear all."}
            },
            "required": ["ref_ids"]
        }
    },
    {
        "name": "get_ref",
        "description": "Get full content of a specific reference without selecting it. Use for one-time access.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ref_id": {"type": "string", "description": "Reference ID to retrieve"}
            },
            "required": ["ref_id"]
        }
    },
    {
        "name": "switch_mode",
        "description": "Switch between YAP_MODE and CODE_MODE. YAP_MODE: conversation, specs, proposals. CODE_MODE: implementation of approved specs only. STRICT ENTRY: CODE_MODE requires human approval, no PENDING specs, and implementation plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "description": "Target mode: 'YAP_MODE' or 'CODE_MODE'"},
                "reason": {"type": "string", "description": "Why switching modes. For CODE_MODE: must show human approval and implementation plan"}
            },
            "required": ["mode", "reason"]
        }
    }
]


# =============================================================================
# Agent
# =============================================================================

class ReferenceStore:
    """
    Enhanced reference system that stores EVERYTHING except current user prompt.
    
    Everything becomes a reference:
    - Tool outputs (file reads, searches, etc.)
    - Agent actions (edits, creates, yap updates)
    - Agent decisions (proposals, reasoning) 
    - Human responses (approvals, clarifications)
    - Context loads (yap content, system state)
    
    Workflow:
    1. ALL interactions stored as references with summaries
    2. At start of each turn: auto-clear with iterative review
    3. Agent decides what context to keep based on current task
    4. Selected references injected into API calls
    5. Process repeats each turn
    """

    def __init__(self):
        self._refs = {}  # ref_id -> {content, ref_type, tool_name, path, created_at, summary}
        self._counter = 0
        self._selected = set()  # Currently selected reference IDs
        self._turn_summaries = []  # Summaries from previous turns

    def store(self, content: str, tool_name: str, tool_input: dict, ref_type: str = "tool_output") -> str:
        """Store content and return reference ID with summary."""
        self._counter += 1
        ref_id = f"ref_{self._counter}"

        # Extract path for display
        path = tool_input.get("path", tool_input.get("pattern", ""))

        # Create brief summary for reference listing
        lines = content.splitlines()
        summary = self._create_enhanced_summary(content, tool_name, ref_type, path, len(lines))

        self._refs[ref_id] = {
            "content": content,
            "ref_type": ref_type,
            "tool_name": tool_name,
            "path": path,
            "summary": summary,
            "lines": len(lines),
            "chars": len(content),
            "created_at": time.time()
        }

        return ref_id
    
    def store_action(self, action_description: str, context: str = "", path: str = "") -> str:
        """Store agent action as reference."""
        return self.store(
            content=f"Action: {action_description}\nContext: {context}",
            tool_name="agent_action",
            tool_input={"path": path},
            ref_type="agent_action"
        )
    
    def store_decision(self, decision: str, reasoning: str = "", context: str = "") -> str:
        """Store agent decision as reference."""
        return self.store(
            content=f"Decision: {decision}\nReasoning: {reasoning}\nContext: {context}",
            tool_name="agent_decision", 
            tool_input={"path": ""},
            ref_type="agent_decision"
        )
    
    def store_conversation(self, content: str, speaker: str = "human") -> str:
        """Store human conversation as reference."""
        return self.store(
            content=f"{speaker.title()}: {content}",
            tool_name="conversation",
            tool_input={"path": ""},
            ref_type="conversation"
        )

    def _create_enhanced_summary(self, content: str, tool_name: str, ref_type: str, path: str, line_count: int) -> str:
        """Create enhanced summary for all reference types."""
        if ref_type == "tool_output":
            if tool_name == "read_file":
                # Extract key info from file content
                if path.endswith('.py'):
                    class_count = content.count('\nclass ')
                    func_count = content.count('\ndef ')
                    return f"Python file: {class_count} classes, {func_count} functions ({line_count} lines)"
                elif path.endswith('.yap'):
                    if "Key Decisions" in content:
                        return f"YAP file: decisions, contracts, specs ({line_count} lines)"
                    return f"YAP file: project context ({line_count} lines)"
                else:
                    return f"File content ({line_count} lines)"
            elif tool_name == "search_files":
                match_count = content.count('\n') - 1 if "Found" in content else 0
                pattern = content.split('\n')[0].split(': ')[-1] if 'Found' in content else "pattern"
                return f"Search '{pattern}': {match_count} matches found"
            elif tool_name == "list_functions":
                return f"Functions in {path}: {line_count} items"
            elif tool_name == "list_directory":
                return f"Directory {path}: {line_count} items"
            else:
                return f"{tool_name} output ({line_count} lines)"
                
        elif ref_type == "agent_action":
            action = content.split('\n')[0].replace('Action: ', '')
            return f"Action: {action[:50]}{'...' if len(action) > 50 else ''}"
            
        elif ref_type == "agent_decision":
            decision = content.split('\n')[0].replace('Decision: ', '')
            return f"Decision: {decision[:50]}{'...' if len(decision) > 50 else ''}"
            
        elif ref_type == "conversation":
            speaker = content.split(':')[0]
            text = content.split(':', 1)[1].strip()[:50]
            return f"{speaker}: {text}{'...' if len(content.split(':', 1)[1].strip()) > 50 else ''}"
            
        else:
            return f"{ref_type} ({line_count} lines)"

    def list_refs(self, use_colors: bool = True) -> str:
        """List all available references with summaries."""
        if not self._refs:
            return "No references stored yet."

        lines = ["References:"]
        for ref_id, info in self._refs.items():
            if ref_id in self._selected:
                if use_colors:
                    indicator = f"{Colors.GREEN}●{Colors.RESET}"
                else:
                    indicator = "●"
            else:
                if use_colors:
                    indicator = f"{Colors.DIM}○{Colors.RESET}"
                else:
                    indicator = "○"
            lines.append(f"  {indicator} {ref_id}: {info['path']} - {info['summary']}")

        if self._selected:
            lines.append(f"\n{Colors.DIM}Selected: {len(self._selected)} ref(s) in context{Colors.RESET}" if use_colors else f"\nSelected: {len(self._selected)} ref(s) in context")

        return "\n".join(lines)

    def get_status_line(self) -> str:
        """Get a compact status line showing selected refs for display in prompt."""
        if not self._selected:
            return ""
        selected_paths = []
        for ref_id in sorted(self._selected):
            if ref_id in self._refs:
                path = self._refs[ref_id]["path"]
                # Shorten path for display
                if len(path) > 20:
                    path = "..." + path[-17:]
                selected_paths.append(f"{ref_id}:{path}")
        return f"{Colors.GREEN}refs:{Colors.RESET} {', '.join(selected_paths)}"

    def select(self, ref_ids: list[str]) -> str:
        """Select references to include in context."""
        valid = []
        invalid = []
        for ref_id in ref_ids:
            if ref_id in self._refs:
                self._selected.add(ref_id)
                valid.append(ref_id)
            else:
                invalid.append(ref_id)

        result = f"{Colors.ORANGE}Selected {len(valid)} reference(s){Colors.RESET}"
        if invalid:
            result += f". Unknown: {', '.join(invalid)}"
        return result

    def deselect(self, ref_ids: list[str]) -> str:
        """Deselect references from context."""
        for ref_id in ref_ids:
            self._selected.discard(ref_id)
        return f"{Colors.ORANGE}Deselected {len(ref_ids)} reference(s){Colors.RESET}"

    def deselect_all(self) -> str:
        """Clear all selections."""
        count = len(self._selected)
        self._selected.clear()
        return f"{Colors.ORANGE}Deselected all ({count}) references{Colors.RESET}"

    def get_selected_content(self) -> str:
        """Get content of all selected references for context injection."""
        parts = []
        
        # Include turn summaries from previous iterations
        if self._turn_summaries:
            summary_content = "\n".join(f"- {summary}" for summary in self._turn_summaries[-3:])
            parts.append(f"=== Previous Turn Summaries ===\n{summary_content}")
        
        # Include current selected references
        if self._selected:
            for ref_id in sorted(self._selected):
                if ref_id in self._refs:
                    info = self._refs[ref_id]
                    ref_type = info.get('ref_type', 'tool_output')
                    path_display = f" ({info['path']})" if info['path'] else ""
                    parts.append(f"=== {ref_id}: {ref_type}{path_display} ===\n{info['content']}")

        return "\n\n".join(parts) if parts else ""

    def get(self, ref_id: str) -> str | None:
        """Get content of a specific reference."""
        if ref_id in self._refs:
            return self._refs[ref_id]["content"]
        return None

    def generate_summary(self) -> str:
        """Generate summary of all references before clearing."""
        if not self._refs:
            return "No references to summarize."
        
        summaries = []
        for ref_id, info in self._refs.items():
            selected_marker = "●" if ref_id in self._selected else "○"
            summaries.append(f"  {selected_marker} {ref_id}: {info['path']} - {info['summary']}")
        
        return f"References to be cleared:\n" + "\n".join(summaries)

    def get_keep_selection_prompt(self) -> str:
        """Generate prompt asking which references to keep."""
        if not self._refs:
            return ""
        
        lines = ["Which references would you like to keep for the next conversation turn?"]
        for ref_id, info in self._refs.items():
            selected_marker = "●" if ref_id in self._selected else "○"
            lines.append(f"  {selected_marker} {ref_id}: {info['path']} - {info['summary']}")
        
        lines.append("\nEnter reference IDs to keep (space-separated), or 'none' to clear all:")
        return "\n".join(lines)

    def start_turn_review(self, current_task_context: str = "") -> str:
        """Agent reviews all reference summaries and decides what to keep for current turn."""
        if not self._refs:
            return "Turn review: no references to review"
        
        original_count = len(self._refs)
        
        # Auto-generate summaries for all references
        self._auto_summarize_all()
        
        # Agent decides what's relevant to current task
        relevant_refs = self._agent_filter_relevant(current_task_context)
        
        # Keep essential context (always keep certain types)
        essential_refs = self._get_essential_refs()
        refs_to_keep = relevant_refs | essential_refs
        
        # Create turn summary before clearing
        cleared_summary = self._create_turn_summary(refs_to_keep)
        if cleared_summary:
            self._turn_summaries.append(cleared_summary)
            # Keep only last 5 turn summaries
            self._turn_summaries = self._turn_summaries[-5:]
        
        # Clear non-essential references
        refs_cleared = []
        for ref_id in list(self._refs.keys()):
            if ref_id not in refs_to_keep:
                del self._refs[ref_id]
                refs_cleared.append(ref_id)
                self._selected.discard(ref_id)
        
        # Auto-select kept references
        self._selected = refs_to_keep & set(self._refs.keys())
        
        kept_count = len(refs_to_keep & set(self._refs.keys()))
        if kept_count > 0:
            # Show first few kept refs to avoid clutter
            kept_refs = sorted(refs_to_keep & set(self._refs.keys()))
            kept_display = ', '.join(kept_refs[:3])
            if len(kept_refs) > 3:
                kept_display += f" +{len(kept_refs)-3} more"
            return f"Turn review: kept {kept_count}/{original_count} refs ({kept_display})"
        else:
            self._counter = 0  # Reset counter if all cleared
            return f"Turn review: cleared all {original_count} references"
    
    def _auto_summarize_all(self):
        """Ensure all references have summaries."""
        for ref_id, info in self._refs.items():
            if 'summary' not in info or not info['summary']:
                info['summary'] = self._create_enhanced_summary(
                    info['content'], 
                    info['tool_name'], 
                    info.get('ref_type', 'tool_output'),
                    info.get('path', ''),
                    info.get('lines', 0)
                )
    
    def _agent_filter_relevant(self, current_task_context: str) -> set:
        """Agent logic to determine relevant references."""
        relevant = set()
        
        # Extract current files/paths from context
        current_files = set()
        if current_task_context:
            # Look for file patterns in context
            import re
            file_patterns = re.findall(r'\b\w+\.(py|yap|js|ts|json|md)\b', current_task_context.lower())
            current_files.update(pattern.split('.')[0] for pattern in file_patterns)
        
        for ref_id, info in self._refs.items():
            path = info.get('path', '')
            ref_type = info.get('ref_type', 'tool_output')
            
            # Always keep recent conversation and decisions
            if ref_type in ['conversation', 'agent_decision']:
                relevant.add(ref_id)
            
            # Keep file content if mentioned in current task
            elif ref_type == 'tool_output' and path:
                path_base = path.split('.')[0].lower()
                if any(cf in path_base or path_base in cf for cf in current_files):
                    relevant.add(ref_id)
            
            # Keep recent actions (last 3)
            elif ref_type == 'agent_action':
                # Keep recent actions - get last 3 action refs
                action_refs = [(rid, info) for rid, info in self._refs.items() 
                              if info.get('ref_type') == 'agent_action']
                action_refs.sort(key=lambda x: x[1].get('created_at', 0), reverse=True)
                if ref_id in [r[0] for r in action_refs[:3]]:
                    relevant.add(ref_id)
        
        return relevant
    
    def _get_essential_refs(self) -> set:
        """Get references that should always be kept."""
        essential = set()
        
        for ref_id, info in self._refs.items():
            path = info.get('path', '')
            
            # Always keep current project.yap and recent yap files
            if path and (path == 'project.yap' or path.endswith('.yap')):
                essential.add(ref_id)
                
        return essential
    
    def _create_turn_summary(self, kept_refs: set) -> str:
        """Create summary of cleared references for future turns."""
        cleared_refs = {rid: info for rid, info in self._refs.items() if rid not in kept_refs}
        
        if not cleared_refs:
            return ""
        
        summaries = []
        for ref_id, info in cleared_refs.items():
            ref_type = info.get('ref_type', 'tool_output')
            summary = info.get('summary', 'No summary')
            summaries.append(f"{ref_type}: {summary}")
        
        return f"Turn summary ({len(cleared_refs)} items): " + "; ".join(summaries[:5])
    
    def auto_clear_with_prompt(self, prompt_callback=None) -> str:
        """Legacy method - now redirects to start_turn_review."""
        return self.start_turn_review("user interaction")

    def clear(self):
        """Clear all references (e.g., when conversation is cleared)."""
        self._refs.clear()
        self._selected.clear()
        self._counter = 0


class YapAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = anthropic.Anthropic()
        self.yap_manager = YapManager(config.project_root, config.yap_extension, config.project_yap)
        self.file_manager = FileManager(config.project_root)
        self.conversation_history = []
        self.system_prompt = self._build_system_prompt()
        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cache_read_tokens = 0
        self.total_cache_creation_tokens = 0
        # Reference-based context management
        self.refs = ReferenceStore()
        # Mode system - start in YAP_MODE
        self.mode = "YAP_MODE"
        # Tool call counter for reference cycling
        self.tool_call_count = 0
        self.refs_cleared_this_iteration = False
        self.pending_mode_switch = None  # Requires user approval

    def _build_system_prompt(self) -> str:
        # Condensed YAP spec - key rules only
        yap_spec_condensed = """# YAP Format (Condensed)

## GOLDEN RULES
1. YAP FIRST, THEN CODE - Agree on specs BEFORE writing code
2. HUMAN APPROVAL REQUIRED - Proposals are PENDING until human says "yes"/"approved"
3. CLEAR ATTRIBUTION - Mark your proposals as (PENDING) until approved

## File Structure
- project.yap - project-level context
- foo.yap - context for foo.py (or foo/ directory)

## Proposing Changes
Always propose in Yap Here with clear PENDING marker:
<!-- AGENT PROPOSAL (pending approval):
- Feature X
  > why: reasoning
  > decided: agent, human approved (PENDING)
-->
WAIT for "yes"/"approved"/"looks good" before implementing.

## Allowed Sections
- Yap Here - proposals, conversation, implementation state
- What This Does - architectural purpose
- Key Decisions - approved choices with attribution
- Contracts - what must be true
- Depends On / Used By - relationships

## Implementation State (in Yap Here)
- <!-- All implemented --> - everything in sync
- <!-- Not implemented --> - nothing implemented yet
- <!-- Pending: - item1 - item2 --> - specific items to implement

## Attribution (for approved decisions)
- decided: human - human specified
- decided: agent, human approved - you proposed, human agreed
- decided: conversation - back-and-forth discussion

## Rules
1. Use read_yap_chain BEFORE working on code
2. PROPOSE changes, WAIT for approval, THEN implement
3. Never use read_file/write_file/edit_file on .yap files
4. mark_yap_implemented updates both code and yap hashes

## Iteration Limits
You have ~30 tool calls per turn. When running low:
1. Wrap up current task cleanly
2. Save state in Yap Here if needed
3. Return to human with summary
Don't leave work half-done."""

        system_prompt_path = Path(__file__).parent / "AGENT-SYSTEM-PROMPT.md"
        agent_instructions = system_prompt_path.read_text() if system_prompt_path.exists() else ""

        # Note: Project YAP context is loaded on-demand via read_yap_chain tool, not in system prompt
        return f"""You are a Yapper coding agent. Turn human intent into specific specs through conversation, then implement.

{yap_spec_condensed}

## Agent Instructions
{agent_instructions}

## Workflow (Conversational)
The workflow is iterative, not linear. Go back and forth with human:
- Propose → discuss → refine → implement → review → adjust
- You can implement, then return to discussion
- Always get approval before major changes
- When done with a phase, return to human for next steps

## Mode System
You operate in two modes that enforce the yap-first workflow:

**YAP_MODE (default)**: Conversation, questions, spec proposals
- Available tools: yap tools + shared tools (list_directory, refs)
- Focus on understanding requirements from yap files, proposing specs, getting approval
- Cannot search or read code files - work from yap documentation

**CODE_MODE**: Implementation
- Available tools: code tools (read_file, search_files, edit_file, write_file) + shared tools
- Focus on implementing approved specs

**Mode Switching (requires user approval):**
When you call switch_mode, it creates a PENDING request that the user must approve.

```
Agent: [calls switch_mode with reason: "Implement approved rate limiting specs"]
System: "Mode switch requested: YAP_MODE → CODE_MODE. Waiting for user approval..."
Human: "yes" / "approved" / "go ahead"  (or "no" to reject)
System: [executes mode switch]
```

The user sees the pending switch and your reason, then decides whether to approve.
Always provide a clear reason explaining what you plan to do in the new mode.

## Reference System
Everything becomes a reference: tool outputs, agent actions, decisions, conversation.
- Use list_refs to see available references
- Use select_refs to add references to your working context (they'll be included in each API call)
- Use deselect_refs to remove references when done (reduces token usage)
- Use get_ref for one-time access without selecting
- References persist across conversation turns until cleared"""
    
    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        try:
            # Mode restrictions
            yap_tools = {
                "read_yap_chain", "read_yap_section", "write_yap_section", "update_yap",
                "mark_yap_implemented", "clear_yap_here", "get_implementation_status",
                "add_pending_task", "complete_pending_task"
            }

            code_tools = {
                "read_file", "file_info", "search_files", "edit_file", "write_file",
                "remove_file", "list_functions"
            }

            shared_tools = {
                "list_refs", "select_refs", "deselect_refs", "get_ref", "task_complete",
                "switch_mode",  # Available in both modes
                "list_directory"  # Read-only directory listing, useful in both modes
            }
            
            # Check mode restrictions
            if self.mode == "YAP_MODE" and tool_name in code_tools and tool_name not in shared_tools:
                return f"Error: {tool_name} not available in YAP_MODE. Use switch_mode to change to CODE_MODE first."
            
            if self.mode == "CODE_MODE" and tool_name in yap_tools and tool_name not in shared_tools and tool_name != "switch_mode":
                return f"Error: {tool_name} not available in CODE_MODE. Use switch_mode to change to YAP_MODE first."
            if tool_name == "read_file":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                # Block .yap files - use read_yap_section instead
                if tool_input["path"].endswith(self.config.yap_extension):
                    return f"Error: Use read_yap_section or read_yap_chain for .yap files, not read_file."
                start_line = tool_input.get("start_line")
                end_line = tool_input.get("end_line")
                content, total_lines, was_truncated = self.file_manager.read_file(
                    tool_input["path"], start_line, end_line, self.config.max_read_lines
                )
                start = start_line or 1
                actual_end = min((end_line or total_lines), start + self.config.max_read_lines - 1)
                range_str = f"lines {start}-{actual_end} of {total_lines}"
                truncate_note = f" [TRUNCATED - use start_line={actual_end + 1} to continue]" if was_truncated else ""
                result = f"{tool_input['path']} ({range_str}){truncate_note}:\n\n{content}"
                # Store as reference
                ref_id = self.refs.store(result, tool_name, tool_input)
                return f"{Colors.ORANGE}[Stored as {ref_id}]{Colors.RESET}\n{result}"

            elif tool_name == "file_info":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                info = self.file_manager.file_info(tool_input["path"])
                return f"{info['path']}: {info['lines']} lines, {info['size_bytes']} bytes, modified {info['modified']}"

            elif tool_name == "search_files":
                if "pattern" not in tool_input:
                    return "Error: Missing required parameter 'pattern'"
                results, protected = self.file_manager.search_files(
                    tool_input["pattern"],
                    tool_input.get("path", "."),
                    tool_input.get("max_results", 20)
                )
                if not results and not protected:
                    return f"No matches for: {tool_input['pattern']}"

                output_lines = []
                if results:
                    output_lines.append(f"Found {len(results)} match(es):")
                    for r in results:
                        output_lines.append(f"  {r['file']}:{r['line']}: {r['content']}")

                if protected:
                    output_lines.append(f"\n⚠ {len(protected)} protected file(s) also matched (content not shown):")
                    for p in protected:
                        output_lines.append(f"  {p['file']} [protected by: {p['pattern']}]")

                result = "\n".join(output_lines)
                # Store as reference if results are substantial
                if len(results) > 3:
                    ref_id = self.refs.store(result, tool_name, tool_input)
                    return f"{Colors.ORANGE}[Stored as {ref_id}]{Colors.RESET}\n{result}"
                return result

            elif tool_name == "edit_file":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                # Block .yap files - use write_yap_section instead
                if tool_input["path"].endswith(self.config.yap_extension):
                    return f"Error: Use write_yap_section for .yap files, not edit_file."
                if "old_string" not in tool_input:
                    return "Error: Missing required parameter 'old_string'"
                if "new_string" not in tool_input:
                    return "Error: Missing required parameter 'new_string'"
                
                result = self.file_manager.edit_file(
                    tool_input["path"], tool_input["old_string"], tool_input["new_string"]
                )
                
                # Store action reference
                old_preview = tool_input["old_string"][:50] + ("..." if len(tool_input["old_string"]) > 50 else "")
                new_preview = tool_input["new_string"][:50] + ("..." if len(tool_input["new_string"]) > 50 else "")
                action_ref = self.refs.store_action(
                    f"Edited {tool_input['path']}: '{old_preview}' → '{new_preview}'",
                    context=f"Modified existing file content",
                    path=tool_input["path"]
                )
                
                return result

            elif tool_name == "write_file":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                # Block .yap files - use write_yap_section or update_yap instead
                if tool_input["path"].endswith(self.config.yap_extension):
                    return f"Error: Use write_yap_section or update_yap for .yap files, not write_file."
                if "content" not in tool_input:
                    return "Error: Missing required parameter 'content'"
                
                result = self.file_manager.write_file(tool_input["path"], tool_input["content"])
                
                # Store action reference
                content_size = len(tool_input["content"])
                line_count = tool_input["content"].count('\n') + 1
                action_ref = self.refs.store_action(
                    f"Created {tool_input['path']} ({content_size} chars, {line_count} lines)",
                    context="Created new file",
                    path=tool_input["path"]
                )
                
                return result

            elif tool_name == "list_directory":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                items = self.file_manager.list_directory(tool_input["path"])
                return f"Contents of {tool_input['path']}:\n" + "\n".join(items)

            elif tool_name == "remove_file":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                # Block .yap files
                if tool_input["path"].endswith(self.config.yap_extension):
                    return f"Error: Cannot remove .yap files directly."
                return self.file_manager.remove_file(tool_input["path"])

            elif tool_name == "list_functions":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                functions = self.file_manager.list_functions(tool_input["path"])
                if not functions:
                    return f"No functions found in {tool_input['path']}"
                lines = []
                for f in functions:
                    prefix = "async " if f["is_async"] else ""
                    doc = f" - {f['docstring']}" if f["docstring"] else ""
                    lines.append(f"{f['line']:4d}: {prefix}{f['name']}{f['signature']}{doc}")
                result = f"Functions in {tool_input['path']}:\n" + "\n".join(lines)
                # Store as reference if many functions
                if len(functions) > 5:
                    ref_id = self.refs.store(result, tool_name, tool_input)
                    return f"{Colors.ORANGE}[Stored as {ref_id}]{Colors.RESET}\n{result}"
                return result

            elif tool_name == "read_yap_chain":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                yap_files = self.yap_manager.get_yap_for_path(tool_input["path"])
                if not yap_files:
                    return f"No .yap files found for: {tool_input['path']}"

                result_parts = []
                for yap_file in yap_files:
                    rel_path = yap_file.relative_to(self.yap_manager.project_root)
                    content = self.yap_manager.read_yap(yap_file)
                    code_path = self.yap_manager.get_code_path_for_yap(yap_file)
                    status_info = self.yap_manager.tracker.check_status(content, code_path)
                    has_changes = status_info["yap_changed"] or status_info["code_changed"]
                    status = " (pending changes)" if has_changes else " (synced)"
                    result_parts.append(f"=== {rel_path}{status} ===\n{content}")
                result = "\n\n".join(result_parts)
                # Store as reference
                ref_id = self.refs.store(result, tool_name, tool_input)
                return f"{Colors.ORANGE}[Stored as {ref_id}]{Colors.RESET}\n{result}"

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
                    added, removed, first_line, last_line = get_diff_summary(old_content, tool_input["content"])
                    lines_info = f"line {first_line}" if first_line == last_line else f"lines {first_line}-{last_line}"
                    return f"Updated {tool_input['path']} ({Colors.GREEN}+{added}{Colors.RESET}, {Colors.RED}-{removed}{Colors.RESET} @ {lines_info})"
                else:
                    line_count = tool_input["content"].count('\n') + 1
                    return f"Created {tool_input['path']} ({line_count} lines)"

            elif tool_name == "mark_yap_implemented":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                yap_path = Path(tool_input["path"])
                if not yap_path.is_absolute():
                    yap_path = self.yap_manager.project_root / yap_path
                self.yap_manager.mark_implemented(yap_path)
                return f"Marked {tool_input['path']} as implemented"

            elif tool_name == "read_yap_section":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                if "section" not in tool_input:
                    return "Error: Missing required parameter 'section'"
                yap_path = Path(tool_input["path"])
                if not yap_path.is_absolute():
                    yap_path = self.yap_manager.project_root / yap_path
                if not yap_path.exists():
                    return f"Error: YAP file not found: {tool_input['path']}"

                section_content, found = self.yap_manager.read_yap_section(yap_path, tool_input["section"])
                if not found:
                    return f"Section '{tool_input['section']}' not found in {tool_input['path']}"
                return section_content

            elif tool_name == "write_yap_section":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                if "section" not in tool_input:
                    return "Error: Missing required parameter 'section'"
                if "content" not in tool_input:
                    return "Error: Missing required parameter 'content'"
                yap_path = Path(tool_input["path"])
                if not yap_path.is_absolute():
                    yap_path = self.yap_manager.project_root / yap_path
                if not yap_path.exists():
                    return f"Error: YAP file not found: {tool_input['path']}"

                result = self.yap_manager.write_yap_section(yap_path, tool_input["section"], tool_input["content"])
                
                # Store action reference
                content_preview = tool_input["content"][:100].replace('\n', ' ')
                action_ref = self.refs.store_action(
                    f"Updated {tool_input['section']} in {tool_input['path']}: {content_preview}{'...' if len(tool_input['content']) > 100 else ''}",
                    context="Modified YAP section",
                    path=tool_input["path"]
                )
                
                return result

            elif tool_name == "clear_yap_here":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                yap_path = Path(tool_input["path"])
                if not yap_path.is_absolute():
                    yap_path = self.yap_manager.project_root / yap_path

                preserve_notes = tool_input.get("preserve_human_notes", True)
                updated_content, had_notes = self.yap_manager.clear_yap_here(yap_path)

                if had_notes and preserve_notes:
                    return f"Found human notes in {tool_input['path']}. Ask human if any thoughts should be preserved in permanent sections before clearing."
                else:
                    self.yap_manager.write_yap(yap_path, updated_content)
                    return f"Cleared 'Yap Here' section in {tool_input['path']}"

            # Implementation state tools
            elif tool_name == "get_implementation_status":
                statuses = self.yap_manager.get_all_implementation_status()
                if not statuses:
                    return "No .yap files found in project."

                lines = ["Implementation Status:"]
                for s in statuses:
                    rel_path = s["path"].relative_to(self.yap_manager.project_root)

                    # Determine status indicator
                    if s["all_implemented"]:
                        indicator = f"{Colors.GREEN}✓{Colors.RESET}"
                        status_text = "all implemented"
                    elif s["code_changed"]:
                        indicator = f"{Colors.RED}⚠{Colors.RESET}"
                        status_text = "code drifted"
                    elif s["pending_tasks"]:
                        indicator = f"{Colors.YELLOW}○{Colors.RESET}"
                        status_text = f"{len(s['pending_tasks'])} pending"
                    elif s["yap_changed"]:
                        indicator = f"{Colors.YELLOW}△{Colors.RESET}"
                        status_text = "yap changed"
                    else:
                        indicator = f"{Colors.DIM}?{Colors.RESET}"
                        status_text = "unknown"

                    lines.append(f"  {indicator} {rel_path} - {status_text}")

                    # Show pending tasks if any
                    if s["pending_tasks"]:
                        for task in s["pending_tasks"][:3]:  # Show first 3
                            lines.append(f"      - {task}")
                        if len(s["pending_tasks"]) > 3:
                            lines.append(f"      ... and {len(s['pending_tasks']) - 3} more")

                return "\n".join(lines)

            elif tool_name == "add_pending_task":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                if "task" not in tool_input:
                    return "Error: Missing required parameter 'task'"
                yap_path = Path(tool_input["path"])
                if not yap_path.is_absolute():
                    yap_path = self.yap_manager.project_root / yap_path
                if not yap_path.exists():
                    return f"Error: YAP file not found: {tool_input['path']}"
                return self.yap_manager.add_pending_task(yap_path, tool_input["task"])

            elif tool_name == "complete_pending_task":
                if "path" not in tool_input:
                    return "Error: Missing required parameter 'path'"
                if "task" not in tool_input:
                    return "Error: Missing required parameter 'task'"
                yap_path = Path(tool_input["path"])
                if not yap_path.is_absolute():
                    yap_path = self.yap_manager.project_root / yap_path
                if not yap_path.exists():
                    return f"Error: YAP file not found: {tool_input['path']}"
                return self.yap_manager.complete_pending_task(yap_path, tool_input["task"])

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

            # Reference management tools
            elif tool_name == "list_refs":
                return self.refs.list_refs()

            elif tool_name == "select_refs":
                ref_ids = tool_input.get("ref_ids", [])
                if not ref_ids:
                    return "Error: No ref_ids provided"
                result = self.refs.select(ref_ids)
                # Show updated refs status
                status = self.refs.get_status_line()
                if status:
                    print(f"  {status}")
                return result

            elif tool_name == "deselect_refs":
                ref_ids = tool_input.get("ref_ids", [])
                if not ref_ids:
                    return "Error: No ref_ids provided"
                if ref_ids == ["all"]:
                    result = self.refs.deselect_all()
                else:
                    result = self.refs.deselect(ref_ids)
                # Show updated refs status (or indicate none selected)
                status = self.refs.get_status_line()
                if status:
                    print(f"  {status}")
                else:
                    print(f"  {Colors.DIM}refs: (none selected){Colors.RESET}")
                return result

            elif tool_name == "get_ref":
                ref_id = tool_input.get("ref_id", "")
                if not ref_id:
                    return "Error: No ref_id provided"
                content = self.refs.get(ref_id)
                if content is None:
                    return f"Error: Reference '{ref_id}' not found. Use list_refs to see available references."
                return content

            elif tool_name == "switch_mode":
                new_mode = tool_input.get("mode", "").upper()
                reason = tool_input.get("reason", "")

                if new_mode not in ["YAP_MODE", "CODE_MODE"]:
                    return "Error: Mode must be 'YAP_MODE' or 'CODE_MODE'"

                if new_mode == self.mode:
                    return f"Already in {new_mode}"

                if not reason:
                    return "Error: Must provide reason for mode switch"

                # Store pending mode switch - requires user approval
                self.pending_mode_switch = {
                    "from": self.mode,
                    "to": new_mode,
                    "reason": reason
                }

                return (f"{Colors.ORANGE}Mode switch requested: {self.mode} → {new_mode}{Colors.RESET}\n"
                       f"Reason: {reason}\n\n"
                       f"{Colors.BOLD}Waiting for user approval...{Colors.RESET}\n"
                       f"User must respond to approve or reject this mode switch.")

            return f"Unknown tool: {tool_name}"
        except Exception as e:
            print_error(str(e))
            return f"Error: {e}"

    def _print_token_usage(self, usage):
        """Print compact token usage stats."""
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
        cache_read = getattr(usage, 'cache_read_input_tokens', 0) or 0
        cache_creation = getattr(usage, 'cache_creation_input_tokens', 0) or 0

        # Build compact usage string for this call
        parts = [f"in:{input_tokens}"]
        if cache_read > 0:
            parts.append(f"cached:{cache_read}")
        if cache_creation > 0:
            parts.append(f"cache+:{cache_creation}")
        parts.append(f"out:{output_tokens}")

        # Show session totals
        total_in = self.total_input_tokens
        total_out = self.total_output_tokens

        print(f"{Colors.CYAN}tokens:{Colors.RESET} {Colors.DIM}[{' '.join(parts)}] session: {total_in:,}in / {total_out:,}out{Colors.RESET}")

    def _call_api_streaming(self, messages: list):
        """Call API with streaming, returns (content_blocks, stop_reason, streamed_text)."""
        while True:
            try:
                content_blocks = []
                stop_reason = None
                current_text = ""
                current_tool_use = None
                streamed_any_text = False

                # Build system content with selected references
                system_content = self.system_prompt
                selected_refs = self.refs.get_selected_content()
                if selected_refs:
                    system_content += f"\n\n## Selected References (currently in context)\n{selected_refs}"

                with self.client.messages.stream(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    system=[{"type": "text", "text": system_content, "cache_control": {"type": "ephemeral"}}],
                    tools=TOOLS,
                    messages=messages
                ) as stream:
                    for event in stream:
                        if event.type == "content_block_start":
                            if event.content_block.type == "text":
                                current_text = ""
                            elif event.content_block.type == "tool_use":
                                # End any pending text output
                                if streamed_any_text:
                                    print()  # Newline before tool
                                    streamed_any_text = False
                                # Show tool being called
                                print(f"  {Colors.DIM}● {event.content_block.name}...{Colors.RESET}", end="", flush=True)
                                current_tool_use = {
                                    "type": "tool_use",
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": {}
                                }
                        elif event.type == "content_block_delta":
                            if event.delta.type == "text_delta":
                                text = event.delta.text
                                current_text += text
                                # Stream text to terminal in real-time
                                if not streamed_any_text:
                                    print(f"{Colors.MAGENTA}Agent:{Colors.RESET} ", end="", flush=True)
                                    streamed_any_text = True
                                print(text, end="", flush=True)
                            elif event.delta.type == "input_json_delta":
                                # Accumulate JSON for tool input
                                pass
                        elif event.type == "content_block_stop":
                            if current_text:
                                content_blocks.append(type("TextBlock", (), {"type": "text", "text": current_text})())
                                current_text = ""
                            if current_tool_use:
                                # Clear the "tool..." line, will be replaced with result
                                print(f"\r{' ' * 60}\r", end="", flush=True)
                                content_blocks.append(current_tool_use)
                                current_tool_use = None
                        elif event.type == "message_stop":
                            pass

                    # Get final message for complete tool inputs
                    final_message = stream.get_final_message()
                    stop_reason = final_message.stop_reason
                    # Use the final message content for accurate tool inputs
                    content_blocks = final_message.content

                    # Track token usage
                    usage = final_message.usage
                    self.total_input_tokens += usage.input_tokens
                    self.total_output_tokens += usage.output_tokens
                    # Cache tokens (if available)
                    if hasattr(usage, 'cache_read_input_tokens'):
                        self.total_cache_read_tokens += usage.cache_read_input_tokens or 0
                    if hasattr(usage, 'cache_creation_input_tokens'):
                        self.total_cache_creation_tokens += usage.cache_creation_input_tokens or 0

                if streamed_any_text:
                    print()  # End the streamed line

                # Display token usage (flush to ensure visibility)
                self._print_token_usage(usage)
                sys.stdout.flush()

                return content_blocks, stop_reason

            except anthropic.RateLimitError as e:
                # Extract retry-after from headers if available, default to 60s
                retry_after = 60
                if hasattr(e, 'response') and e.response is not None:
                    retry_after = int(e.response.headers.get('retry-after', 60))

                print_warning(f"Rate limited. Waiting {retry_after}s...")
                try:
                    for remaining in range(retry_after, 0, -1):
                        print(f"\r{Colors.DIM}  Resuming in {remaining}s (Ctrl+C to cancel){Colors.RESET}", end="", flush=True)
                        time.sleep(1)
                    print("\r" + " " * 50 + "\r", end="", flush=True)
                except KeyboardInterrupt:
                    print()
                    raise
    
    def run(self, user_request: str, continue_conversation: bool = True) -> str:
        # Store human conversation as reference (everything becomes a reference except current prompt)
        if continue_conversation:
            self.refs.store_conversation(user_request, "human")
        
        # ITERATIVE REVIEW: Agent reviews all references and decides what to keep
        if continue_conversation and self.refs._refs:
            review_result = self.refs.start_turn_review(user_request)
            print(f"{Colors.DIM}{review_result}{Colors.RESET}")
        
        self.conversation_history.append({"role": "user", "content": user_request})
        messages = self.conversation_history.copy()

        max_iterations = 50
        for iteration in range(1, max_iterations + 1):
            # Reset per-iteration state
            self.tool_call_count = 0
            self.refs_cleared_this_iteration = False
            
            try:
                content, stop_reason = self._call_api_streaming(messages)
            except KeyboardInterrupt:
                print_warning("Cancelled")
                return "Cancelled"

            if stop_reason == "end_turn":
                final_text = "".join(b.text for b in content if hasattr(b, "text"))
                if continue_conversation:
                    self.conversation_history.append({"role": "assistant", "content": content})
                    # Store agent response as reference
                    self.refs.store_conversation(final_text, "agent")
                    # Note: References now cleared at START of next turn via start_turn_review
                # Text already streamed to terminal
                return final_text

            tool_uses = [b for b in content if getattr(b, "type", None) == "tool_use"]
            if not tool_uses:
                final_text = "".join(b.text for b in content if hasattr(b, "text"))
                if continue_conversation:
                    self.conversation_history.append({"role": "assistant", "content": content})
                    # Store agent response as reference
                    self.refs.store_conversation(final_text, "agent")
                    # Note: References now cleared at START of next turn via start_turn_review
                return final_text

            messages.append({"role": "assistant", "content": content})

            tool_results = []
            for tool_use in tool_uses:
                tool_input = tool_use.input if hasattr(tool_use, "input") else tool_use.get("input", {})
                tool_name = tool_use.name if hasattr(tool_use, "name") else tool_use.get("name", "")
                tool_id = tool_use.id if hasattr(tool_use, "id") else tool_use.get("id", "")

                # Increment tool call counter
                self.tool_call_count += 1

                result = self._execute_tool(tool_name, tool_input)

                # Compact tool output
                if result.startswith("Error:"):
                    print(f"  {Colors.RED}✗ {tool_name}: {result}{Colors.RESET}")
                else:
                    # Show tool name with brief summary
                    summary = self._get_tool_summary(tool_name, tool_input, result)
                    print(f"  {Colors.DIM}→ {summary}{Colors.RESET}")

                # Check if we should clear references mid-iteration
                if self._should_clear_mid_iteration(tool_name):
                    self._mid_iteration_clear_refs(tool_name)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result
                })

                if result == "TASK_COMPLETE":
                    if continue_conversation:
                        self.conversation_history.append({"role": "assistant", "content": content})
                        self.conversation_history.append({"role": "user", "content": tool_results})
                        # Store task completion as reference
                        self.refs.store_action("Task completed", "TASK_COMPLETE signal received")
                        # Note: References now cleared at START of next turn via start_turn_review
                    return "Task completed"

            messages.append({"role": "user", "content": tool_results})

        print_warning("Max iterations reached")
        if continue_conversation:
            # Store max iterations reached as reference
            self.refs.store_action("Max iterations reached", f"Hit limit of {max_iterations} iterations")
            # Note: References now cleared at START of next turn via start_turn_review
        return "Max iterations reached"

    def _get_tool_summary(self, tool_name: str, tool_input: dict, result: str) -> str:
        """Generate a concise summary of tool execution."""
        path = tool_input.get("path", "")
        if tool_name == "read_file":
            # Extract line info from result
            truncated = "[TRUNCATED]" in result
            truncate_flag = f" {Colors.YELLOW}[truncated]{Colors.RESET}" if truncated else ""
            # Parse "lines X-Y of Z" from result
            import re as regex
            match = regex.search(r'lines (\d+)-(\d+) of (\d+)', result)
            if match:
                start, end, total = match.groups()
                return f"read {path} (lines {start}-{end}/{total}){truncate_flag}"
            return f"read {path}{truncate_flag}"
        elif tool_name == "file_info":
            return f"info {path}"
        elif tool_name == "search_files":
            pattern = tool_input.get("pattern", "")
            matches = result.count('\n') if "Found" in result else 0
            return f"search '{pattern}' ({matches} matches)"
        elif tool_name == "edit_file":
            return f"edited {path}"
        elif tool_name == "write_file":
            lines = tool_input.get("content", "").count('\n') + 1
            return f"wrote {path} ({lines} lines)"
        elif tool_name == "list_directory":
            items = result.count('\n')
            return f"listed {path} ({items} items)"
        elif tool_name == "list_functions":
            funcs = result.count('\n')
            return f"listed {funcs} functions in {path}"
        elif tool_name == "read_yap_chain":
            return f"read YAP for {path}"
        elif tool_name == "update_yap":
            lines = tool_input.get("content", "").count('\n') + 1
            return f"updated {path} ({lines} lines)"
        elif tool_name == "mark_yap_implemented":
            return f"marked {path} implemented"
        elif tool_name == "clear_yap_here":
            return f"cleared Yap Here in {path}"
        elif tool_name == "read_yap_section":
            section = tool_input.get("section", "")
            return f"read '{section}' from {path}"
        elif tool_name == "write_yap_section":
            section = tool_input.get("section", "")
            return f"wrote '{section}' to {path}"
        elif tool_name == "task_complete":
            return "task complete"
        return f"{tool_name}"
    
    def _should_clear_mid_iteration(self, tool_name: str) -> bool:
        """Determine if references should be cleared mid-iteration."""
        # Clear after heavy operations
        heavy_ops = ["read_file", "search_files", "read_yap_chain", "list_functions"]
        if tool_name in heavy_ops:
            return True
        
        # Clear every 7 tool calls
        if self.tool_call_count > 0 and self.tool_call_count % 7 == 0:
            return True
        
        return False

    def _smart_retain_refs(self) -> set[str]:
        """Get reference IDs to retain during mid-iteration clearing."""
        if not self.refs._refs:
            return set()
        
        # Sort refs by creation order (newest first)
        sorted_refs = sorted(
            self.refs._refs.items(), 
            key=lambda x: int(x[0].split('_')[1]),  # Extract number from ref_X
            reverse=True
        )
        
        # Keep last 2-3 refs (most recently created)
        refs_to_keep = set()
        for ref_id, info in sorted_refs[:3]:
            refs_to_keep.add(ref_id)
        
        # Also keep currently selected refs that are in the retention list
        retained_selected = refs_to_keep & self.refs._selected
        
        return retained_selected

    def _mid_iteration_clear_refs(self, tool_name: str) -> str:
        """Clear references mid-iteration with smart retention."""
        if not self.refs._refs or self.refs_cleared_this_iteration:
            return ""  # Skip if already cleared this iteration
        
        refs_to_keep = self._smart_retain_refs()
        
        # Clear refs not in keep list
        refs_cleared = []
        for ref_id in list(self.refs._refs.keys()):
            if ref_id not in refs_to_keep:
                del self.refs._refs[ref_id]
                refs_cleared.append(ref_id)
                self.refs._selected.discard(ref_id)
        
        # Update selected to only include kept refs
        self.refs._selected &= refs_to_keep
        
        if refs_cleared:
            self.refs_cleared_this_iteration = True
            reason = f"after {tool_name}" if tool_name in ["read_file", "search_files", "read_yap_chain", "list_functions"] else f"at {self.tool_call_count} calls"
            print(f"{Colors.DIM}  → cleared {len(refs_cleared)} refs ({reason}), kept {len(refs_to_keep)}{Colors.RESET}")
            return f"Mid-iteration clear: removed {len(refs_cleared)} refs, kept {len(refs_to_keep)}"
        
        return ""

    def _auto_clear_references(self) -> str:
        """Legacy method - references now cleared at START of each turn via start_turn_review."""
        # References are now automatically reviewed and cleared at the start of each turn
        # This method is kept for backwards compatibility but does nothing
        return ""

    def clear_history(self):
        self.conversation_history = []
        self.refs.clear()
        print_success("History and references cleared")
    
    def check_for_changes(self) -> list:
        return self.yap_manager.get_changed_yap_files()

    def initialize_yap_guided(self):
        recommendations = self.yap_manager.get_recommended_yap_locations()
        if not recommendations:
            print_warning("No code files found needing .yap files")
            return

        print_info(f"Found {len(recommendations)} recommended .yap files to create:")
        for i, rec in enumerate(recommendations):
            yap_rel = rec["yap_path"].relative_to(self.yap_manager.project_root)
            code_rel = rec["code_path"].relative_to(self.yap_manager.project_root) if rec["code_path"] != self.yap_manager.project_root else "."
            type_label = f"[{rec['type']}]"
            print(f"  {i+1}. {yap_rel} → {code_rel} {Colors.DIM}{type_label}{Colors.RESET}")
        print()

        for rec in recommendations:
            yap_path = rec["yap_path"]
            code_path = rec["code_path"]
            yap_rel = yap_path.relative_to(self.yap_manager.project_root)
            code_rel = code_path.relative_to(self.yap_manager.project_root) if code_path != self.yap_manager.project_root else "."

            print_subheader(f"Create: {yap_rel}")
            print(f"For: {code_rel}")

            response = input(f"\nCreate {yap_rel}? [Y/n/skip all]: ").strip().lower()
            if response == 'skip all':
                break
            elif response in ('n', 'no'):
                continue

            self.run(f"""Create {yap_rel} for: {code_rel}

1. Read the code file(s)
2. Ask me about intent/decisions
3. Propose .yap structure following the spec
4. Wait for approval before writing""")

            print()
            if input("Next? [Y/n]: ").strip().lower() in ('n', 'no'):
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
            yap_changed = [c for c in changes if c["yap_changed"]]
            code_changed = [c for c in changes if c["code_changed"]]

            if yap_changed:
                print_warning(f"{len(yap_changed)} .yap file(s) with pending changes:")
                for c in yap_changed:
                    rel = c["path"].relative_to(agent.yap_manager.project_root)
                    if c["timestamp"]:
                        print(f"  {Colors.YELLOW}• {rel}{Colors.RESET}")
                        print(f"    {Colors.DIM}yap: {c['stored_yap_hash']} → {c['current_yap_hash']}{Colors.RESET}")
                    else:
                        print(f"  {Colors.YELLOW}• {rel} (never synced){Colors.RESET}")

            if code_changed:
                print_warning(f"{len(code_changed)} code file(s) changed without yap review:")
                for c in code_changed:
                    rel = c["path"].relative_to(agent.yap_manager.project_root)
                    code_rel = c["code_path"].relative_to(agent.yap_manager.project_root) if c["code_path"] else "?"
                    print(f"  {Colors.RED}• {rel}{Colors.RESET} (code: {code_rel})")
                    print(f"    {Colors.DIM}code: {c['stored_code_hash']} → {c['current_code_hash']}{Colors.RESET}")

            print()
        else:
            print_success(f"All {len(yap_files)} .yap file(s) up to date\n")

    # If a request was provided as argument, use that as the initial prompt
    if args.request:
        initial_prompt = args.request

    # Always enter interactive mode
    print_info("Commands: quit, clear, changes, refs, mark <path>\n")

    while True:
        try:
            if initial_prompt:
                request = initial_prompt
                initial_prompt = None
            else:
                # Show current mode and refs status
                mode_color = Colors.GREEN if agent.mode == "CODE_MODE" else Colors.BLUE
                print(f"  {mode_color}mode: {agent.mode}{Colors.RESET}")

                # Show pending mode switch if any
                if agent.pending_mode_switch:
                    pending = agent.pending_mode_switch
                    print(f"  {Colors.ORANGE}pending: {pending['from']} → {pending['to']}{Colors.RESET}")
                    print(f"  {Colors.DIM}reason: {pending['reason']}{Colors.RESET}")
                    print(f"  {Colors.BOLD}Approve mode switch? (yes/no){Colors.RESET}")

                # Show refs status line if any refs are selected
                refs_status = agent.refs.get_status_line()
                if refs_status:
                    print(refs_status)
                request = input(f"{Colors.BOLD}You:{Colors.RESET} ").strip()

            if not request:
                continue
            if request.lower() in ("quit", "exit"):
                break

            # Handle pending mode switch approval
            if agent.pending_mode_switch:
                pending = agent.pending_mode_switch
                # Check for approval keywords
                approval_keywords = ["yes", "y", "approved", "approve", "ok", "go", "go ahead", "sure", "do it", "proceed"]
                rejection_keywords = ["no", "n", "reject", "denied", "cancel", "stop", "don't", "dont"]

                request_lower = request.lower().strip()
                if any(kw == request_lower or request_lower.startswith(kw + " ") or request_lower.startswith(kw + ",") for kw in approval_keywords):
                    # Approved - execute the mode switch
                    old_mode = agent.mode
                    agent.mode = pending["to"]
                    agent.pending_mode_switch = None
                    mode_color = Colors.GREEN if agent.mode == "CODE_MODE" else Colors.BLUE
                    print(f"{mode_color}Mode switched: {old_mode} → {agent.mode}{Colors.RESET}")
                    print(f"User approved: {request}")
                    # Continue with any additional message content
                    remaining = request_lower
                    for kw in approval_keywords:
                        if remaining.startswith(kw):
                            remaining = remaining[len(kw):].lstrip(" ,.-")
                            break
                    if not remaining:
                        continue
                    request = remaining
                elif any(kw == request_lower or request_lower.startswith(kw + " ") for kw in rejection_keywords):
                    # Rejected - cancel the mode switch
                    agent.pending_mode_switch = None
                    print(f"{Colors.ORANGE}Mode switch cancelled by user{Colors.RESET}")
                    print(f"User said: {request}")
                    continue
                # If neither clear approval nor rejection, pass to agent to interpret

            if request.lower() == "clear":
                agent.clear_history()
                continue
            if request.lower() == "changes":
                changes = agent.check_for_changes()
                if changes:
                    for c in changes:
                        rel = c["path"].relative_to(agent.yap_manager.project_root)
                        flags = []
                        if c["yap_changed"]:
                            flags.append("yap changed")
                        if c["code_changed"]:
                            flags.append("code drifted")
                        print(f"  • {rel} ({', '.join(flags)})")
                else:
                    print_success("All up to date")
                continue
            if request.lower() == "refs":
                print(agent.refs.list_refs())
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