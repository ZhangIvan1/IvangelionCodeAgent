from dataclasses import dataclass
from typing import Any, AsyncIterator

from anthropic import AsyncAnthropic
from anthropic.types import stop_reason

from llm.types import StreamEvent, EventType
from .types import ChatOptions, ChatResponse, Message, StopReason, StreamEvent


@dataclass
class AnthropicConfig:
    api_key: str
    model: str = 'claude-sonnet-4.6'

class AnthropicProvider:
    def __init__(self, config: AnthropicConfig) -> None:
        self._client = AsyncAnthropic(api_key=config.api_key)
        self.model = config.model
        
    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> ChatResponse:
        options = options or ChatOptions()
        
        params: dict = {
            "model": self.model,
            "max_tokens": options.max_tokens,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content
                } for m in messages
            ],
        }
        
        if options.system:
            params["system"] = options.system
            
        response = await self._client.messages.create(**params)
        
        text = "".join(
            b.text for b in response.content if b.type == "text"
        )
        
        stop_reason = (
            StopReason.END_TURN 
            if response.stop_reason == "end_turn" 
            else StopReason.MAX_TOKENS
        )
        
        return ChatResponse(text=text, 
                            stop_reason=stop_reason, 
                            usage={
                                "input_tokens": response.usage.input_tokens,
                                "output_tokens": response.usage.output_tokens,
                            })
        
    async def stream(self, messages: list[Message], options: ChatOptions | None = None) -> AsyncIterator[StreamEvent]:
        options = options or ChatOptions()

        params: dict = {
            "model": self.model,
            "max_tokens": options.max_tokens,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content
                } for m in messages
            ],
        }

        if options.system:
            params["system"] = options.system

        yield StreamEvent(type=EventType.MESSAGE_START)
        
        async with self._client.messages.stream(**params) as stream:
            async for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "text_delta":
                    yield StreamEvent(type=EventType.TEXT_DELTA, text=event.delta.text)
                    
        yield StreamEvent(type=EventType.MESSAGE_STOP)