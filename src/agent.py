from dataclasses import dataclass, field
from typing import Callable, Awaitable

from llm import LLMProvider
from llm.content_helper import extract_text, extract_tool_uses, create_tool_result
from llm.types import Tool, Message, ChatOptions, ContentBlock

ToolExecutor = Callable[[str, dict], Awaitable[str]]

DEFAULT_MAX_ITERATIONS = 10


@dataclass
class AgentConfig:
    provider: LLMProvider
    system: str
    tools: list[Tool]
    execute_tool: ToolExecutor
    max_iterations: int = DEFAULT_MAX_ITERATIONS
    max_tokens: int | None = None
    
@dataclass
class ToolCallRecord:
    name: str
    input: dict
    result: str
    
@dataclass
class AgentResult:
    text: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    iterations: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    
    
async def run_agent(config: AgentConfig, user_message: str) -> AgentResult:
    messages: list[Message] = [Message(role="user", content = user_message)]
    tool_calls: list[ToolCallRecord] = []
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    
    for i in range(config.max_iterations):
        response = await config.provider.chat(
            messages,
            options=ChatOptions(
                system=config.system,
                tools=config.tools,
                max_tokens=config.max_tokens
            ),
        )
        
        total_input_tokens += response.usage.get("input_tokens", 0)
        total_output_tokens += response.usage.get("output_tokens", 0)

        if response.stop_reason != "tool_use":
            return AgentResult(
                text=extract_text(response.content),
                tool_calls=tool_calls,
                iterations=i+1,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
            )
        
        uses = extract_tool_uses(response.content)
        messages.append(Message(role="assistant", content=response.content))
        
        
        results: list[ContentBlock] = []
        for use in uses:
            result = await config.execute_tool(
                use.name,
                use.input,
            )
            tool_calls.append(
                ToolCallRecord(
                    name=use.name,
                    input=use.input,
                    result=result,
                )
            )
            results.append(create_tool_result(use.id, result))
            
        messages.append(Message(role="user", content=results))
        
    return AgentResult(
        text="(max iterations reached)",
        tool_calls=tool_calls,
        iterations=config.max_iterations,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
    )