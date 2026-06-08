from dataclasses import dataclass
from typing import AsyncIterator

from openai import AsyncOpenAI

from .types import ChatOptions, ChatResponse, Message, StopReason, StreamEvent, EventType


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
            formatted_messages.append({"role": message.role, "content": message.content})
        return formatted_messages
    
    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> ChatResponse:
        options = options or ChatOptions()
        
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=options.max_tokens or 4096,
            messages=self._format_messages(messages, options.system),
        )
        
        choice = response.choices[0]
        stop_reason = (
            StopReason.END_TURN 
            if choice.finish_reason == "stop" 
            else StopReason.MAX_TOKENS
        )
        
        return ChatResponse(
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