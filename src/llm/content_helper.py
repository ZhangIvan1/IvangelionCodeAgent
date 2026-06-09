from .types import ContentBlock, ToolUseBlock, ToolResultBlock


def extract_text(content: list[ContentBlock]) -> str:
    return "".join( block.text for block in content if block.type == "text" )

def extract_tool_uses(content: list[ContentBlock]) -> list[ToolUseBlock]:
    return [ block for block in content if isinstance(block, ToolUseBlock) ]
    
def create_tool_result(tool_use_id: str, content: str, is_error: bool = False) -> ToolResultBlock:
    return ToolResultBlock(
        tool_use_id=tool_use_id,
        content=content,
        is_error=is_error,
    )