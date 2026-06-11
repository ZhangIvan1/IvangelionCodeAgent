import asyncio
import random
from dataclasses import dataclass
from typing import AsyncIterator, Callable, Awaitable

from llm import LLMProvider, Message, ChatOptions, ChatResponse
from llm.types import StreamEvent


def is_retryable(error: Exception) -> bool:
    msg = str(error).lower()

    if any(kw in msg for kw in ("network", "timeout", "connection")):
        return True

    if "rate limit" in msg or "429" in msg:
        return True

    if any(kw in msg for kw in ("500", "502", "503")):
        return True

    status_code = getattr(error, "status_code", None) or getattr(error, "status", None)
    if isinstance(status_code, int):
        return status_code >= 500 or status_code == 429

    return False


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0

DEFAULT_RETRY_CONFIG = RetryConfig()

def calculate_delay(attempt: int, config: RetryConfig = DEFAULT_RETRY_CONFIG) -> float:
    exponential = config.base_delay * (2 ** attempt)
    capped = min(exponential, config.max_delay)
    return random.random() * capped


class RetryProvider:
    def __init__(self, provider: LLMProvider, config: RetryConfig):
        self._provider = provider
        self._config = config or DEFAULT_RETRY_CONFIG

    async def chat(self, messages: list[Message], options: ChatOptions | None = None) -> ChatResponse:
        last_error: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                return await self._provider.chat(messages, options)
            except Exception as e:
                last_error = e
                if not is_retryable(e) or attempt == self._config.max_retries:
                    raise
                delay = calculate_delay(attempt, self._config)
                await asyncio.sleep(delay)

        raise last_error

    async def stream(self, messages: list[Message], options: ChatOptions | None = None) -> AsyncIterator[StreamEvent]:
        last_error: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                async for event in self._provider.stream(messages, options):
                    yield event
                return
            except Exception as e:
                last_error = e
                if not is_retryable(e) or attempt == self._config.max_retries:
                    raise
                delay = calculate_delay(attempt, self._config)
                await asyncio.sleep(delay)

        raise last_error


def safe_tool_executor(executor: Callable[[str, dict], Awaitable[str]], known_tools: set[str] | None = None,) -> Callable[[str, dict], Awaitable[str]]:
    async def wrapped(name:str, input: dict) -> str:
        if known_tools is not None and name not in known_tools:
            available = ",".join(sorted(known_tools))
            return f'Error: unknown tool "{name}". Available tools: {available}'

        try:
            return await executor(name, input)
        except Exception as e:
            return f'Error executing tool [{name}]: {e}"'

    return wrapped

