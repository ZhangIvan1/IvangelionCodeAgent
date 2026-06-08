from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm.anthropic_provider import AnthropicProvider, AnthropicConfig
from llm.openai_compatible import OpenAICompatibleProvider, OpenAICompatibleConfig
from llm.types import Message, StreamEvent, EventType


async def collect_events(stream) -> list[StreamEvent]:
    """Collect all events from an async iterator."""
    events = []
    async for event in stream:
        events.append(event)
    return events


@pytest.mark.asyncio
class TestAnthropicStreaming:
    async def test_yield_stream_events(self):
        with patch("llm.anthropic_provider.AsyncAnthropic"):
            provider = AnthropicProvider(AnthropicConfig(api_key="test-key"))

        # Mock the stream context manager
        mock_event1 = MagicMock()
        mock_event1.type = "content_block_delta"
        mock_event1.delta.type = "text_delta"
        mock_event1.delta.text = "Hello"

        mock_event2 = MagicMock()
        mock_event2.type = "content_block_delta"
        mock_event2.delta.type = "text_delta"
        mock_event2.delta.text = " world"

        mock_stream = MagicMock()
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=False)
        async def async_iter():
            yield mock_event1
            yield mock_event2

        mock_stream.__aiter__ = lambda self: async_iter()

        provider._client.messages.stream = MagicMock(return_value=mock_stream)

        messages = [Message(role="user", content="Hi")]
        events = await collect_events(provider.stream(messages))

        assert events[0].type == EventType.MESSAGE_START
        assert events[1] == StreamEvent(type=EventType.TEXT_DELTA, text="Hello")
        assert events[2] == StreamEvent(type=EventType.TEXT_DELTA, text=" world")
        assert events[-1].type == EventType.MESSAGE_STOP