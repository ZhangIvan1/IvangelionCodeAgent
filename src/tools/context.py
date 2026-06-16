import re

from llm.types import Tool, Message
from token_counter import estimate_message_tokens


class Scratchpad:
    
    def __init__(self) -> None:
        self._entries: list[dict[str, str]] = []
        
    def set(self, key: str, value: str) -> None:
        for entry in self._entries:
            if entry["key"] == key:
                entry["value"] = value
                return
        self._entries.append({"key": key, "value": value})
        
    def get(self, key: str) -> str | None:
        for entry in self._entries:
            if entry["key"] == key:
                return entry["value"]
        return None
    
    def delete(self, key: str) -> bool:
        for entry in self._entries:
            if entry["key"] == key:
                self._entries.remove(entry)
                return True
        return False
    
    def has(self, key: str) -> bool:
        for entry in self._entries:
            if entry["key"] == key:
                return True
        return False
    
    def clear(self) -> None:
        self._entries.clear()
        
    def format(self) -> str:
        if not self._entries:
            return ""
        lines = [f"- **{e['key']}**: {e['value']}" for e in self._entries]
        return f"## Scratchpad\n" + "\n".join(lines)
    
    @property 
    def size(self) -> int:
        return len(self._entries)
    
    
# Scratchpad tool definitions for the agent
SCRATCHPAD_TOOLS: list[Tool] = [
    Tool(
        name="scratchpad_set",
        description="Save a note to the scratchpad. Use this to track your plan, findings, or decisions.",
        input_schema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Note key (e.g. 'plan', 'findings')"},
                "value": {"type": "string", "description": "Note content"},
            },
            "required": ["key", "value"],
        },
    ),
    Tool(
        name="scratchpad_get",
        description="Read a note from the scratchpad by key.",
        input_schema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Note key to read"},
            },
            "required": ["key"],
        },
    ),
    Tool(
        name="scratchpad_list",
        description="List all scratchpad entries.",
        input_schema={"type": "object", "properties": {}},
    ),
]


def execute_scratchpad_tool(
        scratchpad: Scratchpad,
        name: str,
        input: dict,
) -> str:
    if name == "scratchpad_set":
        key = input["key"]
        value = input["value"]
        scratchpad.set(key, value)
        return f"Saved: {key} = {value}"
    elif name == "scratchpad_get":
        key = input["key"]
        return scratchpad.get(key) or f"No entry found for {key}"
    elif name == "scratchpad_list":
        return scratchpad.format() or "Scratchpad is empty."
    return f"Unknown scratchpad tool: {name}"


def select_messages(messages: list[Message], max_tokens) -> list[Message]:
    if len(messages) <= 2:
        return list(messages)

    first = messages[0]
    first_tokens = estimate_message_tokens(first)

    if first_tokens > max_tokens:
        return [first]

    budget = max_tokens - first_tokens
    tail: list[Message] = []

    for i in range(len(messages) - 1, 0, -1):
        tokens = estimate_message_tokens(messages[i])
        if tokens > budget:
            break
        budget -= tokens
        tail.insert(0, messages[i])

    return [first, *tail]

def detect_context_poisoning(text: str) -> list[str]:
    patterns = [
        (re.compile(r"ignore (?:all )?(?:previous |above )?instructions", re.IGNORECASE), "instruction override"),
        (re.compile(r"you are now", re.IGNORECASE), "role hijacking"),
        (re.compile(r"system:\s", re.IGNORECASE), "system prompt injection"),
        (re.compile(r"\bdo not\b.*\btool", re.IGNORECASE), "tool suppression"),
        (re.compile(r"</?(?:system|instruction|prompt)>", re.IGNORECASE), "fake XML tags"),
    ]
    
    found: list[str] = []
    for pattern, name in patterns:
        if pattern.search(text):
            found.append(name)
    return found