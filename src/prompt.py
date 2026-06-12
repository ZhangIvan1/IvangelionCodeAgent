from dataclasses import dataclass

from llm.types import Tool


@dataclass
class PromptSection:
    title: str
    content: str
    priority: int = 0
    
class SystemPromptBuilder:
    def __init__(self) -> None:
        self._sections: list[PromptSection] = []
        
    def add_section(self, title: str, content: str, priority: int = 0) -> "SystemPromptBuilder":
        self._sections.append(PromptSection(title, content, priority))
        return self
    
    def set_role(self, role:str) -> "SystemPromptBuilder":
        return self.add_section("Role", role, 100)
    
    def add_rules(self, rules: list[str]) -> "SystemPromptBuilder":
        content = "\n".join(f"- {rule}" for rule in rules)
        return self.add_section("Rules", content, 80)
    
    def add_tool_guides(self, tools: list[Tool]) -> "SystemPromptBuilder":
        content = [f"- **{t.name}**: {t.description}" for t in tools]
        return self.add_section("Available Tools", "\n".join(content), 60)

    def set_output_constraints(self, constraints: str) -> "SystemPromptBuilder":
        return self.add_section("Output Format", constraints, 40)
    
    def build(self) -> str:
        sorted_sections: list[PromptSection] = sorted(self._sections, key=lambda s: s.priority, reverse=True)
        return "\n\n".join(f"## {s.title}\n\n{s.content}" for s in sorted_sections)
    
    def build_with_budget(self, max_chars: int) -> str:
        sorted_sections: list[PromptSection] = sorted(self._sections, key=lambda s: s.priority, reverse=True)
        
        prompts: list[str] = []
        prompts_length: int = 0
        for i, s in enumerate(sorted_sections):
            prompts_part = f"## {s.title}\n\n{s.content}"
            if prompts_length + len(prompts_part) + 2 > max_chars and prompts:
                break
            prompts.append(prompts_part)
            prompts_length += len(prompts_part) + 2
        return "\n\n".join(prompts)
    
    def get_sections(self) -> list[PromptSection]:
        return list(self._sections)
    
    def clear(self) -> "SystemPromptBuilder":
        self._sections.clear()
        return self
    
    

def create_coding_assistant_prompt(tools: list[Tool]) -> str:
    """Create a pre-configured system prompt for a coding assistant."""
    return (
        SystemPromptBuilder()
        .set_role(
            "You are a coding assistant. Help the user with software engineering tasks "
            "by reading files, writing code, and running commands. Be concise and accurate."
        )
        .add_rules([
            "Always read a file before modifying it.",
            "Explain what you are about to do before using tools.",
            "If a task is complex, break it into steps and track progress with task tools.",
            "Never execute destructive commands without confirmation.",
        ])
        .add_tool_guides(tools)
        .set_output_constraints(
            "Respond in the user's language. Use markdown for code blocks. "
            "Keep explanations brief and focused."
        )
        .build()
    )