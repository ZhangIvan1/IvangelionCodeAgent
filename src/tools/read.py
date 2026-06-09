import os
from dataclasses import dataclass

from llm.types import Tool

MAX_FILE_SIZE = 1024 * 1024

READ_TOOL_DEFINITION = Tool(
    name="read_file",
    description=(
        "Read the contents of a file. Returns the file content with line numbers. "
        "Use offset and limit to read specific portions of large files."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute or relative path to the file to read",
            },
            "offset": {
                "type": "number",
                "description": "Line number to start reading from (1-based, default: 1)",
            },
            "limit": {
                "type": "number",
                "description": "Maximum number of lines to read (default: all)",
            }
        },
        "required": ["file_path"],
    },
)


@dataclass
class ReadToolInput:
    file_path: str
    offset: int = 1
    limit: int | None = None


def _is_binary(raw: bytes) -> bool:
    return b"\x00" in raw


def _format_with_line_numbers(content: str, offset: int) -> str:
    lines = content.split("\n")

    if lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return ""
    max_line_num = offset + len(lines) - 1
    pad_width = len(str(max_line_num))
    return "\n".join(
        f"{str(offset + i).rjust(pad_width)}\t{line}"
        for i, line in enumerate(lines)
    )


def execute_read_tool(input: ReadToolInput) -> str:
    file_path = input.file_path
    offset = input.offset
    limit = input.limit

    if offset < 1:
        raise ValueError("Error: Offset must be a positive integer")

    if not os.path.exists(file_path):
        raise ValueError(f"Error: File not found: {file_path}")
    if not os.path.isfile(file_path):
        raise ValueError(f"Error: Path is not a file: {file_path}")

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"Error: File size exceeds limit: {file_size} > {MAX_FILE_SIZE}")

    try:
        with open(file_path, "rb") as f:
            raw = f.read()
    except OSError as e:
        raise ValueError(f"Error: Failed to read file: {e}")

    if _is_binary(raw):
        raise ValueError("Error: File is binary and cannot be read as text")

    content = raw.decode("utf-8", errors="replace")
    all_lines = content.split("\n")

    start_idx = offset - 1
    end_idx = offset + limit - 1 if limit is not None else len(all_lines)
    selected_lines = all_lines[start_idx:end_idx]

    if not selected_lines:
        raise ValueError(f"Empty: File has {len(all_lines)} lines, offset {offset}, limit {limit}")

    return _format_with_line_numbers("\n".join(selected_lines), offset)
