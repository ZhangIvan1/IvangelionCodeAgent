from dataclasses import dataclass

from llm.anthropic_provider import AnthropicProvider, AnthropicConfig
from llm.openai_compatible import OpenAICompatibleProvider, OpenAICompatibleConfig


@dataclass
class ProviderConfig:
    provider: str
    api_key: str
    model: str | None = None
    base_url: str | None = None
    
def create_provider(config: ProviderConfig):
    if config.provider == "anthropic":
        return AnthropicProvider(
            AnthropicConfig(
                api_key=config.api_key,
                model=config.model,
            )
        )
    
    if config.provider == "openai":
        if not config.base_url:
            raise ValueError("OpenAI provider requires a base_url")
        if not config.model:
            raise ValueError("OpenAI provider requires a model")
        return OpenAICompatibleProvider(                
            OpenAICompatibleConfig(
                api_key=config.api_key,
                base_url=config.base_url,
                model=config.model,
            )
        )
    
    raise ValueError(f"Unsupported provider: {config.provider}")