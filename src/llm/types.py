from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from typing import Protocol


@dataclass
class Message:
    role: str
    content: str
    
class StopReason(Enum):
    END_TURN = "end_turn"
    TOOL_USE = "tool_use"
    MAX_TOKENS = "max_tokens"
    
class EventType(Enum):
    MESSAGE_START = "message_start"
    TEXT_DELTA = "text_delta"
    MESSAGE_STOP = "message_stop"
    ERROR = "error"
    
@dataclass
class ChatResponse:
    text: str
    stop_reason: StopReason
    content: list = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    
@dataclass
class StreamEvent:
    type: EventType
    text: str | None = None 
    
@dataclass
class ChatOptions:
    system: str | None = None
    max_tokens: int | None = None
    tools: list[Tool] | None = None
    
@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)
    

@dataclass
class TextBlock:
    type: str = "text"
    text: str = ""
    
@dataclass
class ToolUseBlock:
    type: str = "tool_use"
    id: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)
    
@dataclass
class ToolResultBlock:
    type: str = "tool_result"
    tool_use_id: str = ""
    content: str = ""
    is_error: bool = False
    
ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock
    
class LLMProvider(Protocol):
    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> ChatResponse:
        pass

