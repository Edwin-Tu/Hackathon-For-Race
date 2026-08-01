"""技能登錄表（F09 4.8：SkillRegistry）。

內部結構：技能對應表、類別到技能名稱的對應、技能優先序對應。
支援註冊、查詢、設定優先序。
"""

from __future__ import annotations

from secretguard.defensive_skills.cross_language_injection_skill import (
    CrossLanguageInjectionSkill,
)
from secretguard.defensive_skills.data_reconstruction_skill import DataReconstructionSkill
from secretguard.defensive_skills.direct_request_skill import DirectRequestSkill
from secretguard.defensive_skills.encoding_bypass_skill import EncodingBypassSkill
from secretguard.defensive_skills.format_smuggling_skill import FormatSmugglingSkill
from secretguard.defensive_skills.homoglyph_obfuscation_skill import (
    HomoglyphObfuscationSkill,
)
from secretguard.defensive_skills.indirect_prompt_injection_skill import (
    IndirectPromptInjectionSkill,
)
from secretguard.defensive_skills.instruction_override_skill import (
    InstructionOverrideSkill,
)
from secretguard.defensive_skills.log_access_skill import LogAccessSkill
from secretguard.defensive_skills.multi_turn_probe_skill import MultiTurnProbeSkill
from secretguard.defensive_skills.output_constraint_bypass_skill import (
    OutputConstraintBypassSkill,
)
from secretguard.defensive_skills.partial_disclosure_skill import PartialDisclosureSkill
from secretguard.defensive_skills.persona_override_skill import PersonaOverrideSkill
from secretguard.defensive_skills.policy_confusion_skill import PolicyConfusionSkill
from secretguard.defensive_skills.reasoning_trap_skill import ReasoningTrapSkill
from secretguard.defensive_skills.refusal_suppression_skill import (
    RefusalSuppressionSkill,
)
from secretguard.defensive_skills.role_play_skill import RolePlaySkill
from secretguard.defensive_skills.structured_output_skill import StructuredOutputSkill
from secretguard.defensive_skills.system_prompt_extraction_skill import (
    SystemPromptExtractionSkill,
)
from secretguard.defensive_skills.translation_bypass_skill import TranslationBypassSkill
from secretguard.skill_router.skill_adapter import SkillAdapter
from secretguard.skill_router.skill_priority import build_priority_map, get_priority

# 所有內建技能類別，對應 F09 五之技能清單（共 20 個）。
_BUILTIN_SKILL_CLASSES = [
    DirectRequestSkill,
    RolePlaySkill,
    InstructionOverrideSkill,
    SystemPromptExtractionSkill,
    EncodingBypassSkill,
    PartialDisclosureSkill,
    TranslationBypassSkill,
    StructuredOutputSkill,
    LogAccessSkill,
    MultiTurnProbeSkill,
    PolicyConfusionSkill,
    IndirectPromptInjectionSkill,
    FormatSmugglingSkill,
    OutputConstraintBypassSkill,
    ReasoningTrapSkill,
    RefusalSuppressionSkill,
    PersonaOverrideSkill,
    DataReconstructionSkill,
    CrossLanguageInjectionSkill,
    HomoglyphObfuscationSkill,
]


class SkillRegistry:
    """技能登錄表：管理技能實例、類別到技能名稱的對應、以及技能優先序。"""

    def __init__(self) -> None:
        self._skills: dict[str, SkillAdapter] = {}
        self._category_to_skills: dict[str, list[str]] = {}
        self._priority_map: dict[str, int] = build_priority_map()

        for skill_cls in _BUILTIN_SKILL_CLASSES:
            self.register(skill_cls())

    def register(self, skill: object) -> None:
        """註冊一個技能（現代或舊版介面皆可，內部以 SkillAdapter 包裝）。"""

        adapter = SkillAdapter(skill)
        self._skills[adapter.name] = adapter

        categories = getattr(skill, "attack_categories", [])
        for category in categories:
            self._category_to_skills.setdefault(category, [])
            if adapter.name not in self._category_to_skills[category]:
                self._category_to_skills[category].append(adapter.name)

    def get_skill(self, skill_name: str) -> SkillAdapter | None:
        return self._skills.get(skill_name)

    def get_skills_for_category(self, category: str) -> list[SkillAdapter]:
        names = self._category_to_skills.get(category, [])
        return [self._skills[n] for n in names if n in self._skills]

    def set_priority(self, skill_name: str, priority: int) -> None:
        self._priority_map[skill_name] = priority

    def get_priority(self, skill_name: str) -> int:
        return get_priority(skill_name, self._priority_map)

    def list_skill_names(self) -> list[str]:
        return list(self._skills.keys())

    def sort_by_priority(self, skill_names: list[str]) -> list[str]:
        """依優先序（數字越小越優先）排序技能名稱清單。"""

        return sorted(skill_names, key=lambda name: self.get_priority(name))
