from __future__ import annotations

from llm import Message


class MessageHistory:
    
    def __init__(self) -> None:
        self._messages: list[Message] = []
    
    def add_user(self, content: str) -> None:
        self._messages.append(Message(role="user", content=content))
        
    def add_assistant(self, content: str) -> None:
        self._messages.append(Message(role="assistant", content=content))
        
    def get_messages(self) -> list[Message]:
        return list(self._messages)
    
    def get_last_n(self, n: int) -> list[Message]:
        return list(self._messages[-n:])
    
    def get_last_message(self) -> Message | None:
        return self._messages[-1] if self._messages else None
    
    def remove_last(self) ->  Message | None:
        return self._messages.pop() if self._messages else None
        
    def clear(self) -> None:
        self._messages.clear()
        
    @property
    def length(self) -> int:
        return len(self._messages)