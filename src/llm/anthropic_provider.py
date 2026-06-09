from dataclasses import dataclass
from typing import Any, AsyncIterator

from anthropic import AsyncAnthropic

from llm.types import StreamEvent, EventType
from .types import ChatOptions, ChatResponse, Message, StopReason, StreamEvent, TextBlock, ToolUseBlock


@dataclass
class AnthropicConfig:
    api_key: str
    model: str = 'claude-sonnet-4.6'

class AnthropicProvider:
    def __init__(self, config: AnthropicConfig) -> None:
        self._client = AsyncAnthropic(api_key=config.api_key)
        self.model = config.model
        
    @staticmethod
    def _format_content(content) -> str | list[dict]:
        if isinstance(content, str):
            return content
        result: list[dict] = []
        for block in content:
            if block.type == "text":
                result.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                result.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
            elif block.type == "tool_result":
                d = {
                    "type": "tool_result",
                    "tool_use_id": block.tool_use_id,
                    "content": block.content,
                }
                if block.is_error:
                    d["is_error"] = True
                result.append(d)
        return result   
        
    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> ChatResponse:
        options = options or ChatOptions()
        
        params: dict = {
            "model": self.model,
            "max_tokens": options.max_tokens,
            "messages": [
                {
                    "role": m.role,
                    "content": self._format_content(m.content),
                } for m in messages
            ],
        }
        
        if options.system:
            params["system"] = options.system
            
        if options.tools:
            params["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in options.tools
            ]
            
        response = await self._client.messages.create(**params)
        
        content_blocks: list = []
        for block in response.content:
            if block.type == "tool_use":
                content_blocks.append(ToolUseBlock(id=block.id,
                                                   name=block.name,
                                                   input=block.input))
            else:
                content_blocks.append(TextBlock(text=block.text))
        
        text = "".join(
            b.text for b in response.content if b.type == "text"
        )
        
        if response.stop_reason == "end_turn":
            stop_reason = StopReason.END_TURN
        elif response.stop_reason == "tool_use":
            stop_reason = StopReason.TOOL_USE
        else:
            stop_reason = StopReason.MAX_TOKENS
        
        return ChatResponse(text=text, 
                            stop_reason=stop_reason, 
                            content=content_blocks,
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
                    "content": self._format_content(m.content),
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