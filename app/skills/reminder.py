"""Skill for creating reminders."""

from app.skills.base import SkillContext, SkillInstruction


class ReminderSkill:
    """Guide Claude when the user wants to create a reminder."""

    name = "reminder_skill"
    priority = 80

    def evaluate(self, context: SkillContext) -> SkillInstruction | None:
        if context.action != "create_reminder":
            return None

        return SkillInstruction(
            name=self.name,
            priority=self.priority,
            allowed_tools=("create_reminder",),
            instruction=(
                "提醒建立技能：\n"
                "- 使用者要求提醒、建立提醒或設定提醒時，只能使用 create_reminder。\n"
                "- scheduled_at 必須是未來且含時區的明確時間；只有『明天下午』等模糊時段時，先詢問具體時刻。\n"
                "- importance 只能是 low、normal、high。\n"
                "- 醫院、回診、用藥或 high 重要度提醒可能需要確認；收到 awaiting_confirmation 時，不得宣稱已建立。\n"
                "- 不得要求或產生 persona_id、resident_id 或其他授權欄位。\n"
                "- 只有工具結果 success=true、status=succeeded 且 record_id 非空時，才能說提醒已建立。"
            ),
        )
