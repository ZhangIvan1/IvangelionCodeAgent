import fnmatch
import os
import re
from dataclasses import dataclass

from llm.types import Tool

MAX_MATCHES = 100
MAX_FILE_SIZE = 512 * 1024

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "dist", "build",
    ".next", ".cache", "coverage",
}

GREP_TOOL_DEFINITION = Tool(
    name="grep",
    description=("Find files matching a glob-like pattern. "
        "Searches recursively from the given directory. "
        "Returns matching file paths sorted alphabetically."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "The regex pattern to search for",
            },
            "path": {
                "type": "string",
                "description": "File or directory to search in (default: current directory)",
            },
            "include": {
                "type": "string",
                "description": 'Glob filter for file names (e.g. "*.ts", "*.py")',
            },
        },
        "required": ["pattern"],
    }
)

@dataclass
class GrepToolInput:
    pattern: str
    path: str = "."
    include: str | None = None
    
@dataclass
class _GrepMatch:
    file: str
    line: int
    text: str
    
def _is_binary(raw: bytes) -> bool:
    return b"\x00" in raw
    
def _search_files(
        file_path: str,
        relative_path: str,
        regex: re.Pattern,
        matches: list[_GrepMatch]) -> None:
    try:
        file_size = os.path.getsize(file_path)
    except OSError as e:
        return
    if file_size > MAX_FILE_SIZE:
        return
    
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
    except OSError as e:
        return
    
    if _is_binary(raw):
        return
    
    content = raw.decode("utf-8", errors="replace")
    for i, line in enumerate(content.split("\n")):
        if len(matches) >= MAX_MATCHES:
            return
        if regex.search(line):
            matches.append(_GrepMatch(file=relative_path, line= i + 1, text=line))

def execute_grep_tool(input: GrepToolInput) -> str:
    try:
        regex = re.compile(input.pattern)
    except re.error as e:
        raise ValueError(f"Error: Invalid regex pattern: {e}")
    
    search_path = input.path
    include = input.include
    
    if not os.path.exists(search_path):
        raise ValueError(f"Error: Path not found: {search_path}")
    
    matches: list[_GrepMatch] = []
    
    if os.path.isfile(search_path):
        _search_files(search_path, search_path, regex, matches)
    elif os.path.isdir(search_path):
        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            
            for name in files:
                if len(matches) >= MAX_MATCHES:
                    break
                if include and not fnmatch.fnmatch(name, include):
                    continue
                _search_files(os.path.join(root, name), name, regex, matches)
                
            if len(matches) >= MAX_MATCHES:
                break
    else:
        return f"Error: Invalid path: {search_path}"
    
    if not matches:
        return f"Error: No matches found for pattern: {input.pattern}"
    
    output = "\n".join([f"{m.file}:{m.line}: {m.text}" for m in matches])
    if len(matches) >= MAX_MATCHES:
        output += f"\n\n(showing {MAX_MATCHES} of {len(matches)} results)"
    return output
    