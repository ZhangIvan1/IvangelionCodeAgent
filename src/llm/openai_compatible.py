import json
from dataclasses import dataclass
from typing import AsyncIterator

from openai import AsyncOpenAI

from .types import ChatOptions, ChatResponse, Message, StopReason, StreamEvent, EventType, TextBlock, ToolUseBlock


@dataclass
class OpenAICompatibleConfig:
    api_key: str
    base_url: str
    model: str
    
    
class OpenAICompatibleProvider:
    
    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self._client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
        self._model = config.model
        
    def _format_messages(self, messages: list[Message], system: str) -> list[dict]:
        formatted_messages: list[dict] = []
        if system:
            formatted_messages.append({"role": "system", "content": system})
        for message in messages:
            if isinstance(message.content, str):
                formatted_messages.append({"role": message.role, "content": message.content})
                continue
                
            if message.role == "assistant":
                text_parts = [ part for part in message.content if part.type == "text" ]
                msg = {"role": "assistant", "content": "".join(part.text for part in text_parts)}
                
                tool_uses = [ part for part in message.content if part.type == "tool_use" ]
                if tool_uses:
                    msg["tool_calls"] = [
                        {
                            "id": tool_use.id,
                            "type": "function",
                            "function": {
                                "name": tool_use.name,
                                "arguments": json.dumps(tool_use.input),
                            },
                        }
                        for tool_use in tool_uses
                    ]
                formatted_messages.append(msg)
                
            else:
                for block in message.content:
                    if block.type == "tool_result":
                        formatted_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": block.tool_use_id,
                                "content": block.content,
                            }
                        )

        return formatted_messages
    
    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> ChatResponse:
        options = options or ChatOptions()
        
        params: dict = {
            "model": self._model,
            "max_tokens": options.max_tokens or 4096,
            "messages": self._format_messages(messages, options.system),
        }
        
        if options.tools:
            params["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    }
                }
                for tool in options.tools
            ]
        
        response = await self._client.chat.completions.create(
            **params
        )
        
        choice = response.choices[0]
        
        content_blocks = []
        if choice.message.content:
            content_blocks.append(TextBlock(text=choice.message.content))
        if choice.message.tool_calls:
            for tool_call in choice.message.tool_calls:
                content_blocks.append(
                    ToolUseBlock(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        input=json.loads(tool_call.function.arguments),
                    )
                )
        
        if choice.finish_reason == "stop":
            stop_reason = StopReason.END_TURN
        elif choice.finish_reason == "tool_calls":
            stop_reason = StopReason.TOOL_USE
        else:
            stop_reason = StopReason.MAX_TOKENS
        
        return ChatResponse(
            content=content_blocks,
            text=choice.message.content or "",
            stop_reason=stop_reason,
            usage={
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0),
            }
        )
        
    async def stream(self, messages: list[Message], options: ChatOptions | None = None) -> AsyncIterator[StreamEvent]:
        options = options or ChatOptions()
        
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=options.max_tokens or 4096,
            messages=self._format_messages(messages, options.system),
            stream=True,
        )
        
        yield StreamEvent(type=EventType.MESSAGE_START)
        
        async for chuck in response:
            delta = chuck.choices[0].delta if chuck.choices else None
            if delta and delta.content:
                yield StreamEvent(type=EventType.TEXT_DELTA, text=delta.content)
                
        yield StreamEvent(type=EventType.MESSAGE_STOP)