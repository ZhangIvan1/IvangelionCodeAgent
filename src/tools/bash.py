import asyncio
from dataclasses import dataclass

from llm.types import Tool

MAX_OUTPUT_SIZE = 100_000

BASH_TOOL_DEFINITION = Tool(
    name="bash",
    description=(
        "Execute a bash command and return its output. "
        "Use this to run shell commands, scripts, or system utilities."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to run",
            },
            "timeout": {
                "type": "number",
                "description": "Timeout in seconds (default: 30.0)",
            }
        },
        "required": ["command"],
    },
)

@dataclass
class BashToolInput:
    command: str
    timeout: float = 30.0


def _truncate_output(output: str) -> str:
    if len(output) > MAX_OUTPUT_SIZE:
        half_size = MAX_OUTPUT_SIZE // 2
        return output[:half_size] + "\n\n... (truncated) ...\n\n" + output[-half_size:]
    return output


async def execute_bash_tool(input: BashToolInput) -> str:
    command = input.command
    timeout = input.timeout
    
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        try:
            srdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise ValueError(f"Timeout: Command {command} did not complete in {timeout} seconds")
    
    except OSError as e:
        raise ValueError(f"Error: Failed to execute command {command}: {e}")
    
    stdout = srdout_bytes.decode("utf-8", errors="replace").strip()
    stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
    
    parts: list[str] = []
    if stdout:
        parts.append(_truncate_output(stdout))
    if stderr:
        parts.append(f"STDERR:\n{_truncate_output(stderr)}")
    
    if process.returncode != 0:
        raise ValueError(f"Error: Failed to execute command {command}: Exit code {process.returncode}")
    
    return "\n".join(parts) or "(no output)"
    
    