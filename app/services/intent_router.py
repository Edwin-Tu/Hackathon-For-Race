"""Deterministic routing for the small, security-sensitive MVP tool set.

The router never executes a tool. It narrows which tool the model may request;
the Tool Gateway remains authoritative for validation, authorization,
confirmation, idempotency, and execution.
"""

import re
from dataclasses import dataclass
from enum import Enum


class RequestedAction(str, Enum):
    """High-level action requested by the user."""

    NO_ACTION = "no_action"
    CREATE_CARE_EVENT = "create_care_event"
    CREATE_REMINDER = "create_reminder"
    GET_USER_SCHEDULE = "get_user_schedule"


@dataclass(frozen=True)
class IntentDecision:
    """Result of deterministic intent routing."""

    action: RequestedAction
    expected_tool: str | None
    is_write: bool
    force_tool: bool = False


_REMINDER_PHRASES = (
    "提醒我",
    "幫我提醒",
    "建立提醒",
    "設定提醒",
    "設提醒",
    "到時候叫我",
    "記得叫我",
    "remind me",
    "set a reminder",
)

_QUERY_PHRASES = (
    "今天有什麼行程",
    "明天有什麼行程",
    "有什麼行程",
    "查看行程",
    "查詢行程",
    "看行程",
    "我的行程",
    "日程安排",
    "查看安排",
    "查詢安排",
    "schedule",
    "what is on my calendar",
)

_RECORD_PHRASES = (
    "幫我記錄",
    "請記錄",
    "記錄一下",
    "記錄我",
    "幫我記下",
    "請記下",
    "新增紀錄",
    "新增記錄",
    "保存這件事",
    "我已經",
    "我今天吃了",
    "我剛吃了",
    "我有散步",
    "我剛散步",
    "散步",
    "服用",
    "吃藥",
    "用餐",
    "睡了",
    "record",
    "log this",
    "save this event",
)

_EXACT_CLOCK_RE = re.compile(
    r"(?:上午|早上|中午|下午|晚上|凌晨)?\s*\d{1,2}\s*(?:點|時)(?:\s*\d{1,2}\s*分)?"
    r"|(?:上午|早上|中午|下午|晚上|凌晨)?\s*[一二三四五六七八九十兩]+\s*(?:點|時)(?:\s*[一二三四五六七八九十兩]+\s*分)?"
    r"|\b\d{1,2}:\d{2}\b"
)


def _has_actionable_time(message: str) -> bool:
    """Return whether the utterance provides a safe time anchor.

    Exact clock times can be converted using the server date/time. Immediate
    expressions such as "剛剛" may safely use the server current time. Broad
    periods such as only "今天下午" intentionally return False, so the model
    can ask a clarification question instead of inventing a clock time.
    """

    if _EXACT_CLOCK_RE.search(message):
        return True
    return any(token in message for token in ("剛剛", "剛才", "剛", "現在"))


def classify_intent(message: str) -> IntentDecision:
    """Classify a user message into the small MVP action set."""

    normalized = " ".join(message.casefold().split())

    if any(phrase in normalized for phrase in _REMINDER_PHRASES):
        return IntentDecision(
            action=RequestedAction.CREATE_REMINDER,
            expected_tool="create_reminder",
            is_write=True,
            force_tool=_has_actionable_time(normalized),
        )

    if any(phrase in normalized for phrase in _QUERY_PHRASES):
        return IntentDecision(
            action=RequestedAction.GET_USER_SCHEDULE,
            expected_tool="get_user_schedule",
            is_write=False,
            force_tool=True,
        )

    if any(phrase in normalized for phrase in _RECORD_PHRASES):
        return IntentDecision(
            action=RequestedAction.CREATE_CARE_EVENT,
            expected_tool="create_care_event",
            is_write=True,
            force_tool=_has_actionable_time(normalized),
        )

    return IntentDecision(
        action=RequestedAction.NO_ACTION,
        expected_tool=None,
        is_write=False,
        force_tool=False,
    )
