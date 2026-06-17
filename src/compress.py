import token
from dataclasses import dataclass
from unittest import result

from llm import LLMProvider, Message
from llm.types import TextBlock, ToolUseBlock, ToolResultBlock, ChatOptions
from token_counter import estimate_conversation_tokens, estimate_message_tokens


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

async def compress_conversation(
        config: CompressorConfig,
        messages: list[Message],
) -> CompressResult:
    
    total_tokens = sum(estimate_message_tokens(message) for message in messages)
    
    if total_tokens <= config.max_tokens or len(messages) <= config.keep_recent_messages:
        return CompressResult(
            messages=messages,
            compressed=False,
            original_count=len(messages),
            compressed_count=len(messages),
            summary_tokens=0,
        )
    
    split_index = len(messages) - config.keep_recent_messages
    old_messages = messages[:split_index]
    recent_messages = messages[split_index:]
    
    summary = await summarize_messages(
        provider=config.provider,
        messages=old_messages,
        max_tokens=config.summary_max_tokens,
    )
    
    summary_message = Message(
        role="user",
        content=f"[Previous conversation summary]\n{summary}",
    )
    
    result = [summary_message, *recent_messages]
    
    return CompressResult(
        messages=result,
        compressed=True,
        original_count=len(messages),
        compressed_count=len(result),
        summary_tokens=estimate_message_tokens(summary_message),
    )

def needs_compression(messages: list[Message], max_tokens: int) -> bool:
    total_tokens = sum(estimate_message_tokens(message) for message in messages)
    return total_tokens > max_tokens
    