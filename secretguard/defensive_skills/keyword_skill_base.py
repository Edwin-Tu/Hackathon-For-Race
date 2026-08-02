"""共用的關鍵字型技能基類，供 20 個攻擊技能檔繼承以減少重複邏輯。

每個技能檔仍是獨立檔案、獨立 skill_name/attack_categories（符合 F09 三的
「約 20 個攻擊技能檔」結構），但共用同一套「以 attacks.json patterns 為主、
可疊加技能專屬規則」的偵測邏輯與依 action 產生 DefenseResult 的邏輯。
"""

from __future__ import annotations

from secretguard.attack_classifier.attack_taxonomy import get_category
from secretguard.common.enums import PolicyAction
from secretguard.defensive_skills.base_skill import BaseSkill
from secretguard.defensive_skills.skill_models import DefenseResult, DetectionResult, SkillInput


class KeywordBasedSkill(BaseSkill):
    """以類別關鍵字為主要偵測依據的技能基類。"""

    # 子類別需覆寫：
    skill_name: str = "keyword_based_skill"
    attack_categories: list[str] = []
    default_action: str = PolicyAction.WARN.value
    refusal_message: str = "偵測到可疑請求，已依安全政策處理。"
    extra_keywords: list[str] = []

    def _category_id(self) -> str:
        return self.attack_categories[0] if self.attack_categories else ""

    def detect(self, skill_input: SkillInput) -> DetectionResult:
        text = skill_input.normalized_prompt or skill_input.original_prompt
        lowered = text.lower()

        category_id = self._category_id()
        category = get_category(category_id)
        keywords = list(category.patterns) if category else []
        keywords.extend(self.extra_keywords)

        matched_keywords = [kw for kw in keywords if kw.lower() in lowered]

        # 若分類器已判定該請求屬於本技能負責的類別，即使關鍵字比對沒抓到，
        # 也視為命中（信任上游分類結果），避免技能與分類器判斷不一致。
        classifier_matched = skill_input.attack_category in self.attack_categories

        matched = bool(matched_keywords) or classifier_matched
        confidence = 0.9 if matched_keywords else (0.6 if classifier_matched else 0.0)

        reasons = []
        if matched_keywords:
            reasons.append(f"命中關鍵字: {', '.join(matched_keywords)}")
        if classifier_matched and not matched_keywords:
            reasons.append(f"分類器判定攻擊類別為 {skill_input.attack_category}")

        return DetectionResult(
            matched=matched,
            confidence=confidence,
            matched_rules=[self.skill_name],
            matched_assets=[],
            reasons=reasons,
            risk_tags=[category_id] if category_id else [],
        )

    def defend(self, skill_input: SkillInput, detection: DetectionResult) -> DefenseResult:
        if not detection.matched:
            return DefenseResult(action=PolicyAction.ALLOW.value)

        action = self.default_action
        restrictions: list[str] = []
        response_message: str | None = None
        safe_prompt: str | None = None

        if action == PolicyAction.BLOCK.value:
            response_message = self.refusal_message
        elif action == PolicyAction.RESTRICT.value:
            restrictions.append(f"{self.skill_name}: 限制輸出範圍，禁止揭露受保護資產原始值")
            response_message = self.refusal_message
        elif action == PolicyAction.ESCALATE.value:
            restrictions.append(f"{self.skill_name}: 升級為嚴格監控，記錄會話訊號")
            response_message = self.refusal_message
        elif action == PolicyAction.WARN.value:
            safe_prompt = skill_input.normalized_prompt
            response_message = self.refusal_message

        return DefenseResult(
            action=action,
            safe_prompt=safe_prompt,
            response_message=response_message,
            restrictions=restrictions,
            risk_tags=detection.risk_tags,
            runtime_checks=[f"{self.skill_name}_check"],
            evidence={"reasons": detection.reasons, "confidence": detection.confidence},
        )
