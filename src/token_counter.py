import json
import math
from dataclasses import dataclass

from llm.types import ContentBlock, TextBlock, ToolUseBlock, ToolResultBlock, Message, Tool

MODEL_CONTEXT_LIMITS: dict[str, int] = {
    "claude-sonnet-4-20250514": 200_000,
    "claude-haiku-4-20250414": 200_000,
    "claude-3-5-sonnet-20241022": 200_000,
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "deepseek-chat": 64_000,
    "deepseek-coder": 128_000,
}

def get_model_context_limit(model: str) -> int | None:
    return MODEL_CONTEXT_LIMITS.get(model, None)

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    
    cjk_chars = 0
    other_chars = 0
    
    for ch in text:
        code = ord(ch)
        if (
            (0x4E00 <= code <= 0x9FFF)  
            or (0x3000 <= code <= 0x303F) 
            or (0x3040 <= code <= 0x30FF)
            or (0xFF00 <= code <= 0xFFEF) 
        ):
            cjk_chars += 1
        else:
            other_chars += 1
            
    return math.ceil(cjk_chars / 2) + math.ceil(other_chars / 4)

def estimate_block_tokens(block: ContentBlock) -> int:
    if isinstance(block, TextBlock):
        return estimate_tokens(block.text)
    elif isinstance(block, ToolUseBlock):
        return estimate_tokens(block.name) + estimate_tokens(json.dumps(block.input))
    elif isinstance(block, ToolResultBlock):
        return estimate_tokens(block.content)
    
    return 0

def estimate_message_tokens(message: Message) -> int:
    overhead = 4
    
    if isinstance(message.content, str):
        return estimate_tokens(message.content) + overhead
        
    return overhead + sum(estimate_block_tokens(block) for block in message.content)


def estimate_conversation_tokens(
        messages: list[Message],
        system: str | None = None,
        tools: list[Tool] | None = None,
) -> int:
    total_tokens = 0
    
    if system:
        total_tokens += estimate_tokens(system)

    if tools:
        for tool in tools:
            total_tokens +=(
                estimate_tokens(tool.name)
                + estimate_tokens(tool.description)
                + estimate_tokens(json.dumps(tool.input_schema))
            )
            
    for message in messages:
        total_tokens += estimate_message_tokens(message)
    
    return total_tokens

@dataclass
class ContextBudget:
    max_context_tokens: int = 64_000
    reserved_for_response: int = 4096
    
DEFAULT_CONTEXT_BUDGET = ContextBudget()

def remaining_budget(budget: ContextBudget, used_tokens: int) -> int:
    return max(0, budget.max_context_tokens - budget.reserved_for_response - used_tokens)

def is_over_budget(budget: ContextBudget, used_tokens: int) -> bool:
    return used_tokens >= budget.max_context_tokens - budget.reserved_for_response
