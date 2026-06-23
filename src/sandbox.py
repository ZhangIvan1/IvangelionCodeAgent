import os.path
import re
from dataclasses import dataclass

from pip._internal.resolution.resolvelib import candidates


class FileSystemSandbox:
    DEFAULT_BLOCKED = [
        re.compile(r"\.env($|\.)"),        
        re.compile(r"/(\.ssh|\.gnupg)/"),    
        re.compile(r"/\.git/config$"),      
        re.compile(r"/(passwd|shadow)$"),     
        re.compile(r"/credentials\.json$"), 
        re.compile(r"/\.aws/"),                 
    ]
    
    def __init__(
            self, allowed_paths: list[str], extra_blocked: list[re.Pattern] | None = None
    ) -> None:
        self._allowed_paths = allowed_paths
        self._blocked_patterns =self.DEFAULT_BLOCKED + (extra_blocked or [])
        
    def check(self, file_path: str) -> str | None:
        resolved = os.path.abspath(file_path)
        
        for pattern in self._blocked_patterns:
            if pattern.search(resolved):
                return f'Blocked: "{file_path}" matches a blocked pattern: {pattern.pattern}.'
            
        in_allowed = any(
            resolved == allowed or resolved.startswith(allowed + os.sep)
            for allowed in self._allowed_paths
        )
        
        if not in_allowed:
            return f'Blocked: "{resolved}" does not match any of the allowed paths.'
        
        return None
    
    def is_allowed(self, file_path: str) -> bool:
        return self.check(file_path) is None
    
    
_DANGEROUS_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\brm\s+(-[rf]+\s+|.*--no-preserve-root)"), "Recursive/forced file deletion"),
    (re.compile(r"\bgit\s+push\s+.*--force"), "Force push may overwrite remote history"),
    (re.compile(r"\bgit\s+reset\s+--hard"), "Hard reset discards uncommitted changes"),
    (re.compile(r"\bchmod\s+777\b"), "Sets world-writable permissions"),
    (re.compile(r"\bcurl\s+.*\|\s*(sh|bash)\b"), "Piping remote script to shell"),
    (re.compile(r"\bsudo\s+"), "Elevated privilege execution"),
    (re.compile(r"\b(DROP|DELETE\s+FROM|TRUNCATE)\b", re.IGNORECASE), "Destructive database operation"),
    (re.compile(r"\bkill\s+-9\b"), "Forceful process termination"),
]

def check_dangerous_command(command: str) -> str | None:
    for pattern, message in _DANGEROUS_PATTERNS:
        if pattern.search(command):
            return message
    return None

def read_project_config(project_dir: str) -> str | None:
    candidates = ["CLAUDE.md", os.path.join(".claude", "CLAUDE.md")]
    
    for candidate in candidates:
        path = os.path.join(project_dir, candidate)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            continue
    return None

@dataclass
class GitInfo:
    branch: str
    last_commit: str
    status: str
    remote_url: str
    
def parse_git_info(
    branch: str = "",
    last_commit: str = "",
    status: str = "",
    remote_url: str = "",
) -> GitInfo:
    return GitInfo(
        branch=branch,
        last_commit=last_commit,
        status=status,
        remote_url=remote_url,
    )

def format_git_context(info: GitInfo) -> str:
    lines = ["## Project Context"]
    
    if info.branch:
        lines.append(f"  - Branch: {info.branch}")
    if info.last_commit:
        lines.append(f"  - Last Commit: {info.last_commit}")
    if info.status:
        lines.append(f"  - Status: {info.status}")
    if info.remote_url:
        lines.append(f"  - Remote URL: {info.remote_url}")
        
    return "\n".join(lines) if len(lines) > 1 else ""