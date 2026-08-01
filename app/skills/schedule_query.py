"""Skill for read-only schedule queries."""

from app.skills.base import SkillContext, SkillInstruction


class ScheduleQuerySkill:
    """Guide Claude when the user asks to view a schedule."""

    name = "schedule_query_skill"
    priority = 80

    def evaluate(self, context: SkillContext) -> SkillInstruction | None:
        if context.action != "get_user_schedule":
            return None

        return SkillInstruction(
            name=self.name,
            priority=self.priority,
            allowed_tools=("get_user_schedule",),
            instruction=(
                "行程查詢技能：\n"
                "- 只有使用者要求查看、查詢或列出既有行程時，才能使用 get_user_schedule。\n"
                "- 此工具是唯讀工具，不得用於新增照護事件、保存活動或建立提醒。\n"
                "- 不得要求或產生 persona_id；查詢目標由後端 AuthContext 注入。\n"
                "- 查詢成功只表示 query_completed，不代表完成任何寫入操作。\n"
                "- 回覆應忠實摘要工具結果，不得捏造不存在的行程。"
            ),
        )
