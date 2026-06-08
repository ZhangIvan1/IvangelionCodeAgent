from dataclasses import dataclass

from anthropic import AsyncAnthropic
from anthropic.types import stop_reason

from .types import ChatOptions, ChatResponse, Message, StopReason


@dataclass
class AnthropicConfig:
    api_key: str
    model: str = 'claude-sonnet-4.6'

class AnthropicProvider:
    def __init__(self, config: AnthropicConfig):
        self.api_key = AsyncAnthropic(api_key=config.api_key)
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
            
        response = await self.api_key.messages.create(**params)
        
        text = "".join(
            b.text for b in response.content if b.type == "text"
        )
        
        stop_reason = (
            StopReason.END_TURN 
            if response.stop_reason == StopReason.END_TURN 
            else StopReason.MAX_TOKENS
        )
        
        return ChatResponse(text=text, 
                            stop_reason=stop_reason, 
                            usage={
                                "input_tokens": response.usage.input_tokens,
                                "output_tokens": response.usage.output_tokens,
                            })
        