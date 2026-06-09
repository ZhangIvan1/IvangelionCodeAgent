from llm.types import Tool

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