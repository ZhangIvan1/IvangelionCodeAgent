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