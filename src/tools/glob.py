import fnmatch
import os
from dataclasses import dataclass

from llm.types import Tool

MAX_RESULTS = 200
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "dist", "build",
    ".next", ".cache", "coverage",
}

GLOB_TOOL_DEFINITION = Tool(
    name="glob",
    description=("Find files matching a glob-like pattern. "
        "Searches recursively from the given directory. "
        "Returns matching file paths sorted alphabetically."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": 'The pattern to match files against (e.g. "*.ts", "src/**/*.py")',
            },
            "path": {
                "type": "string",
                "description": "The directory to search in (default: current directory)",
            }
        },
        "required": ["pattern"],
    }
)

@dataclass
class GlobToolInput:
    pattern: str
    path: str = "."
    
def execute_glob_tool(input: GlobToolInput) -> str:
    patten = input.pattern
    search_path = input.path
    
    if not os.path.exists(search_path):
        raise ValueError(f"Error: Path not found: {search_path}")
    if not os.path.isdir(search_path):
        raise ValueError(f"Error: Path is not a directory: {search_path}")
    
    results: list[str] = []
    has_double_star = "**" in patten
    
    for root, dirs, files in os.walk(search_path):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        
        for name in files:
            if len(results) >= MAX_RESULTS:
                break
            relative_path = os.path.relpath(os.path.join(root, name), search_path)
            if has_double_star:
                if fnmatch.fnmatch(relative_path, patten):
                    results.append(os.path.join(root, name))
            else:
                if fnmatch.fnmatch(name, patten):
                    results.append(relative_path)
        
        if len(results) >= MAX_RESULTS:
            break
            
    results.sort()
    
    if not results:
        raise ValueError(f'No files found matching pattern "{patten}" in directory "{search_path}"')
    
    output = "\n".join(results)
    if len(results) >= MAX_RESULTS:
        output += f"\n\n(showing {MAX_RESULTS} of {len(results)} results)"
    return output