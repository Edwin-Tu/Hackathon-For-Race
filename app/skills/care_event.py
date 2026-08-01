"""Skill for recording completed care events."""

from app.skills.base import SkillContext, SkillInstruction


class CareEventSkill:
    """Guide Claude when the user wants to record a completed event."""

    name = "care_event_skill"
    priority = 80

    def evaluate(self, context: SkillContext) -> SkillInstruction | None:
        if context.action != "create_care_event":
            return None

        return SkillInstruction(
            name=self.name,
            priority=self.priority,
            allowed_tools=("create_care_event",),
            instruction=(
                "照護事件記錄技能：\n"
                "- 使用者要求記錄、記下或保存已發生的飲食、活動、睡眠、用藥、行程、情緒或家屬聯絡事件時，只能使用 create_care_event。\n"
                "- 事件類型只能使用 meal、activity、sleep、medication、appointment、mood、family_contact、general。\n"
                "- 若缺少明確日期或時刻，應針對缺少的資訊提出簡短問題，不得自行猜測。\n"
                "- 不得要求或產生 persona_id、resident_id、requester_id、role、SQL 或資料表名稱。\n"
                "- 用藥事件可能需要使用者確認；收到 awaiting_confirmation 時，不得宣稱已記錄。\n"
                "- 只有工具結果 success=true、status=succeeded 且 record_id 非空時，才能說事件已記錄。"
            ),
        )
