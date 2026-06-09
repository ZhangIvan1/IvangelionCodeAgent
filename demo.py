import asyncio

from llm.factory import ProviderConfig, create_provider
from llm.types import Message


async def main():
    provider = create_provider(
        ProviderConfig(
            provider="openai-compatible",
            # api_key=os.environ["DEEPSEEK_API_KEY"],
            api_key="sk-52eedb1086f543f8b99359615ff67772",
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
        )
    )

    response = await provider.chat(
        [Message(role="user", content="用一句话解释什么是 TypeScript")],
    )

    print("Response:", response.text)
    print("Stop reason:", response.stop_reason)
    print("Usage:", response.usage)


asyncio.run(main())