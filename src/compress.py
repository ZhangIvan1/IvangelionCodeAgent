from dataclasses import dataclass

from llm import LLMProvider, Message
from llm.types import TextBlock, ToolUseBlock, ToolResultBlock, ChatOptions


@dataclass
class CompressorConfig:
    provider: LLMProvider
    max_tokens: int = 50000
    keep_recent_messages: int = 6
    summary_max_tokens: int = 1024
    

@dataclass
class CompressResult:
    messages: list[Message]
    compressed: bool
    original_count: int
    compressed_count: int
    summary_tokens: int
    
    
def _format_content(message: Message) -> str:
    if isinstance(message.content, str):
        return message.content
    
    parts: list[str] = []
    for block in message.content:
        if isinstance(block, TextBlock):
            parts.append(block.text)
        elif isinstance(block, ToolUseBlock):
            parts.append(f"[Tool call: {block.name}]")
        elif isinstance(block, ToolResultBlock):
            parts.append(f"[Tool result: {block.content[:200]}]")
    return "\n".join(parts)

async def summarize_messages(
        provider: LLMProvider,
        messages: list[Message],
        max_tokens: int,
) -> str:
    formatted = "\n\n".join(
        f"{messages.role}: {_format_content(message)}" for message in messages
    )
    
    response = await provider.chat(
        [
            Message(role="user",content=(
                    "Summarize this conversation concisely. Focus on: what the user asked, "
                    "what tools were used, what was accomplished, and any important decisions "
                    f"or findings.\n\n{formatted}"
                ),
            ),
        ],
        options=ChatOptions(
            system=(
                "You are a conversation summarizer. Produce a concise summary that "
                "captures the key information needed to continue the conversation. "
                "Do not include pleasantries or meta-commentary."
            ),
            max_tokens=max_tokens
        ),
    )
    
    return response.text
    