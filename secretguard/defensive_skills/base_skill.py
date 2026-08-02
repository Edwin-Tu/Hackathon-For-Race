"""技能抽象基類（F09 三、五）。

現代介面：技能子類別需提供 skill_name、attack_categories 兩個類別屬性，
並實作 detect(skill_input) -> DetectionResult 與 defend(skill_input, detection) -> DefenseResult。

F09 五之注意事項：技能存在兩代介面（現代 skill_name/attack_categories 風格與
舊版 name/detect/defend 風格）。BaseSkill 本身即代表現代介面；舊版介面技能
由 skill_router.skill_adapter.SkillAdapter 轉接成統一呼叫方式，不要求所有
技能都繼承 BaseSkill，只要求具備可被 adapter 識別的最小介面。
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from secretguard.defensive_skills.skill_models import DefenseResult, DetectionResult, SkillInput


class BaseSkill(ABC):
    """所有防禦技能的抽象基類（現代介面）。"""

    skill_name: str = "base_skill"
    attack_categories: list[str] = []

    @abstractmethod
    def detect(self, skill_input: SkillInput) -> DetectionResult:
        """偵測輸入是否符合本技能負責的攻擊模式。"""

        raise NotImplementedError

    @abstractmethod
    def defend(self, skill_input: SkillInput, detection: DetectionResult) -> DefenseResult:
        """依偵測結果產生防禦動作（允許、警告、改寫、限制、授權、升級、阻擋）。"""

        raise NotImplementedError

    def run(self, skill_input: SkillInput) -> tuple[DetectionResult, DefenseResult]:
        """便利方法：依序執行 detect 再 defend，回傳兩者結果。"""

        detection = self.detect(skill_input)
        defense = self.defend(skill_input, detection)
        return detection, defense
