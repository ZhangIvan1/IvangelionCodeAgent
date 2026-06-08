from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from typing import Protocol

from pygments.lexers import felix


@dataclass
class Message:
    role: str
    content: str
    
class StopReason(Enum):
    END_TURN = "end_turn"
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
    usage: dict = field(default_factory=dict)
    
@dataclass
class StreamEvent:
    type: EventType
    text: str | None = None 
    
@dataclass
class ChatOptions:
    system: str | None = None
    max_tokens: int | None = None
    
@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)
    
    
class LLMProvider(Protocol):
    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> ChatResponse:
        pass

