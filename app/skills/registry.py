"""Skill registry and deterministic routing for the current project."""

from __future__ import annotations

from collections.abc import Iterable

from app.skills.base import (
    Skill,
    SkillContext,
    SkillInstruction,
    SkillRoutingResult,
)
from app.skills.care_event import CareEventSkill
from app.skills.reminder import ReminderSkill
from app.skills.safe_reply import SafeReplySkill
from app.skills.schedule_query import ScheduleQuerySkill
from app.skills.security_refusal import SecurityRefusalSkill


class SkillRegistry:
    """Register, select, prioritize, and merge project skills."""

    def __init__(self, skills: Iterable[Skill] | None = None) -> None:
        self._skills: dict[str, Skill] = {}
        for skill in skills or ():
            self.register(skill)

    def register(self, skill: Skill) -> None:
        """Register a skill by its stable name."""
        if skill.name in self._skills:
            raise ValueError(f"Duplicate skill name: {skill.name}")
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list_names(self) -> tuple[str, ...]:
        return tuple(self._skills.keys())

    def route(self, context: SkillContext) -> SkillRoutingResult:
        """Evaluate all skills and merge results by descending priority."""
        activated: list[SkillInstruction] = []
        for skill in self._skills.values():
            result = skill.evaluate(context)
            if result is not None:
                activated.append(result)

        activated.sort(key=lambda item: (-item.priority, item.name))
        blocked = any(item.blocked for item in activated)

        allowed_tools: list[str] = []
        risk_tags: list[str] = []
        for item in activated:
            for tool in item.allowed_tools:
                if tool not in allowed_tools:
                    allowed_tools.append(tool)
            for tag in item.risk_tags:
                if tag not in risk_tags:
                    risk_tags.append(tag)

        safe_response = next(
            (item.safe_response for item in activated if item.safe_response),
            None,
        )

        if blocked:
            allowed_tools = []

        return SkillRoutingResult(
            selected_skills=tuple(item.name for item in activated),
            instructions=tuple(item.instruction for item in activated),
            allowed_tools=tuple(allowed_tools),
            blocked=blocked,
            safe_response=safe_response,
            risk_tags=tuple(risk_tags),
        )


def create_default_skill_registry() -> SkillRegistry:
    """Create the thin first-version skill set for this project."""
    return SkillRegistry(
        skills=(
            SecurityRefusalSkill(),
            CareEventSkill(),
            ReminderSkill(),
            ScheduleQuerySkill(),
            SafeReplySkill(),
        )
    )
