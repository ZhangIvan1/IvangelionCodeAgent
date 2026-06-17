import sys
from dataclasses import dataclass, field
from typing import Callable, Awaitable


def is_multi_line(text: str) -> bool:
    return "\n" in text

def normalize_text(text: str) -> str:
    return text.strip()

def parse_command(text: str) -> str:
    return text.strip().split()[0].lower() if text.strip() else ""

@dataclass
class Command:
    name: str
    description: str
    execute: Callable[[], str | None]
    
@dataclass
class ReplConfig:
    prompt: str = "> "
    exit_keywords: list[str] = field(default_factory=lambda: ["/exit", "/quit"])
    commands: list[Command] = field(default_factory=list)
    on_input: Callable[[str], Awaitable[str]] | None = None
    
def _default_commands() -> list[Command]:
    return [
        Command(
            name="/help",
            description="Show available commands",
            execute=lambda: "help_placeholder", 
        ),
        Command(
            name="/clear",
            description="Clear the screen",
            execute=lambda: (sys.stdout.write("\033[2J\033[H"), None)[-1],
        ),
    ]

def format_help(commands: list[Command], exit_keywords: list[str]) -> str:
    lines = ["Available commands:"]
    for cmd in commands:
        lines.append(f"  {cmd.name:<12} {cmd.description}")
    lines.append(f"  {exit_keywords[0]:<12} Exit the REPL")
    return "\n".join(lines)


class Repl:
    def __init__(self, config: ReplConfig | None = None) -> None:
        self._config = config or ReplConfig()
        self._all_commands: list[Command] = _default_commands() + list(self._config.commands)
        
        for cmd in self._all_commands:
            if cmd.name == "/help":
                cmd.execute = lambda : format_help(
                    self._all_commands,
                    self._config.exit_keywords
                )
                break
                
    async def process_input(self, raw: str) -> str | None:
        text = normalize_text(raw)
        if not text:
            return ""
        
        cmd_name = parse_command(text)
        if cmd_name in self._config.exit_keywords:
            return None
        
        for cmd in self._all_commands:
            if cmd.name == cmd_name:
                result = cmd.execute()
                return result if result is not None else ""
            
        if self._config.on_input:
            return await self._config.on_input(text)
        
        return f"Unknown command: {cmd_name}. Type /help for available commands."
    
    async def run(self) -> None:
        print("AI Coding Agent (type /help for available commands, /exit to quit)\n")
        
        while True:
            try:
                raw_text = input(self._config.prompt)
            except EOFError:
                print("Goodbye!")
                break
            
            result = await self.process_input(raw_text)
            
            if result is None:
                print("Goodbye!")
                break
            
            if result:
                print(result)
            