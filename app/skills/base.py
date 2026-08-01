"""Core contracts for the lightweight project skill layer.

Skills guide model behaviour for one turn. They do not authorize or execute
operations; ToolGateway remains the authoritative security boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SkillContext:
    """Trusted context used to decide which skills are active for a turn."""

    message: str
    action: str
    user_role: str


@dataclass(frozen=True)
class SkillInstruction:
    """One activated skill and its prompt/tool constraints."""

    name: str
    priority: int
    instruction: str
    allowed_tools: tuple[str, ...] = ()
    blocked: bool = False
    safe_response: str | None = None
    risk_tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillRoutingResult:
    """Merged result of all skills selected for one turn."""

    selected_skills: tuple[str, ...]
    instructions: tuple[str, ...]
    allowed_tools: tuple[str, ...]
    blocked: bool = False
    safe_response: str | None = None
    risk_tags: tuple[str, ...] = ()

    def to_prompt_block(self) -> str:
        """Render a stable prompt block without including user input."""
        if not self.instructions:
            return "本回合沒有額外技能指令。"

        sections = []
        for index, instruction in enumerate(self.instructions, start=1):
            sections.append(f"技能 {index}：\n{instruction.strip()}")
        return "\n\n".join(sections)


class Skill(Protocol):
    """Protocol implemented by each skill."""

    name: str
    priority: int

    def evaluate(self, context: SkillContext) -> SkillInstruction | None:
        """Return an instruction when this skill applies to the context."""
