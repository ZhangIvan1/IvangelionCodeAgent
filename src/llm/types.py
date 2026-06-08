from __future__ import annotations

from dataclasses import dataclass, field

from typing import Protocol


@dataclass
class Message:
    role: str
    content: str

@dataclass
class ChatResponse:
    text: str
    stop_reason: str   ## "end_turn" or "max_tokens"
    usage: dict = field(default_factory=dict)
    
@dataclass
class ChatOptions:
    system: str | None = None
    max_tokens: int | None = None
    
    
class LLMProvider(Protocol):
    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> ChatResponse:
        pass

