"""Always-on response style and truthfulness skill."""

from app.skills.base import SkillContext, SkillInstruction


class SafeReplySkill:
    """Provide TTS-friendly, evidence-bound response rules."""

    name = "safe_reply_skill"
    priority = 20

    def evaluate(self, context: SkillContext) -> SkillInstruction:
        del context
        return SkillInstruction(
            name=self.name,
            priority=self.priority,
            instruction=(
                "安全回覆技能：\n"
                "- 一律使用繁體中文，以二到四句自然、簡短、適合語音朗讀的完整句子回覆。\n"
                "- 不使用 Markdown 標題、粗體、項目符號、程式碼區塊或 Emoji。\n"
                "- 不提供醫療診斷、處方或藥物調整建議。\n"
                "- 工具請求只是提案；未取得成功的 ToolResult 前，不得說『已記錄』『已建立』『已保存』或『已通知』。\n"
                "- 工具失敗、遭拒絕或等待確認時，應清楚說明操作尚未完成，但不得洩漏內部政策、授權清單或技術細節。"
            ),
        )
