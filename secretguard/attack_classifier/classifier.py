"""Deterministic multi-view attack classifier for Input Guard."""

from __future__ import annotations

import re
from dataclasses import dataclass

from secretguard.attack_classifier.attack_taxonomy import load_attack_taxonomy
from secretguard.attack_classifier.pattern_loader import load_rules
from secretguard.attack_classifier.result import AttackClassificationResult, MatchedRule
from secretguard.attack_classifier.scoring import (
    aggregate_category_scores,
    aggregate_severity,
    compute_confidence,
    pick_primary_category,
)
from secretguard.input_normalization.normalization_result import NormalizationResult


@dataclass(frozen=True)
class _SupplementalRule:
    rule_id: str
    category: str
    pattern: re.Pattern[str]
    weight: int
    severity: str
    reason: str


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.DOTALL)


_SUPPLEMENTAL_RULES = [
    _SupplementalRule("IG-IO-01", "instruction_override", _rx(r"(?:忽略|無視|停用|解除|失效|取代|覆寫).{0,24}(?:指令|規則|政策|限制)"), 60, "critical", "要求停用或覆寫既有指令"),
    _SupplementalRule("IG-IO-02", "instruction_override", _rx(r"(?:ignore|disregard|forget|override|disable).{0,35}(?:previous|prior|earlier|all|system|safety)?.{0,15}(?:instructions?|rules?|policy|constraints?)"), 60, "critical", "英文指令覆寫"),
    _SupplementalRule("IG-RP-01", "role_play", _rx(r"(?:扮演|假裝|模擬|進入|小說演練|虛構情境).{0,55}(?:管理員|維護員|開發者模式|最高權限|沒有限制|不受限制|DAN|無視政策)"), 50, "high", "角色扮演或權限人格覆寫"),
    _SupplementalRule("IG-RP-02", "role_play", _rx(r"(?:role[- ]?play|act as|pretend|developer mode|red[- ]team simulation|DAN).{0,50}(?:unrestricted|administrator|ignore|no restrictions|print|return)"), 50, "high", "英文角色扮演繞過"),
    _SupplementalRule("IG-IPI-01", "indirect_prompt_injection", _rx(r"(?:摘要|整理|分析|評估|網頁|郵件|PDF|履歷|文件|RAG\s*context|retrieved document).{0,180}(?:給模型|隱藏命令|assistant\s*:|ignore|忽略|不要回答|只輸出|改回傳)"), 70, "critical", "不可信內容夾帶模型指令"),
    _SupplementalRule("IG-MTP-01", "multi_turn_probe", _rx(r"(?:上一輪|前一輪|前面要求|片段\s*[AB]?|前半段|後半段|previous fragment|previous turn).{0,120}(?:合併|拼接|連接|補上|執行|照做|follow|print|output)"), 65, "critical", "跨回合拼接或分段載荷"),
    _SupplementalRule("IG-MTP-02", "data_reconstruction", _rx(r"(?:拼接|合併|串起|重建|combine|reconstruct).{0,80}(?:片段|字首|前綴|後綴|secret|password|token|指令|instruction)"), 60, "critical", "要求重建片段或秘密"),
    _SupplementalRule("IG-SID-01", "direct_request", _rx(r"(?:告訴|顯示|列出|輸出|貼出|匯出|透露|揭露|return|reveal|show|give|print|export).{0,80}(?:密碼|password|api\s*key|access\s*token|credentials?|private\s*keys?|私鑰|身分證|病歷|住民資料|resident\s*data|medical\s*record|合約全文|production credentials)"), 70, "critical", "直接索取敏感資訊"),
    _SupplementalRule("IG-AUTH-01", "authorization_bypass", _rx(r"(?:上一位使用者|其他住民|所有住民|其他家庭成員|不屬於我|跨\s*tenant|other\s+(?:users?|residents?|tenants?)|last\s+(?:ten|\d+)\s+users?).{0,100}(?:內容|紀錄|資料|病歷|電話|conversation|summary|private|data|record)"), 80, "critical", "跨使用者、住民或租戶資料請求"),
    _SupplementalRule("IG-PART-01", "partial_disclosure", _rx(r"(?:(?:前\s*[一二三四五六七八九十\d]+|後\s*[一二三四五六七八九十\d]+|第一個字元|下一個字元|前綴|後綴|最後\s*[一二三四五六七八九十\d]+|總長度|prefix|suffix|first\s+\w+\s+characters?|last\s+\w+\s+(?:digits|characters)|character count).{0,90}(?:密碼|password|api\s*key|token|secret|身分證|credential)|(?:密碼|password|api\s*key|token|secret|身分證|credential).{0,90}(?:前\s*[一二三四五六七八九十\d]+|後\s*[一二三四五六七八九十\d]+|第一個字元|下一個字元|前綴|後綴|最後\s*[一二三四五六七八九十\d]+|總長度|prefix|suffix|first\s+\w+\s+characters?|last\s+\w+\s+(?:digits|characters)|character count))"), 85, "critical", "要求秘密片段、長度或逐字資訊"),
    _SupplementalRule("IG-PART-02", "partial_disclosure", _rx(r"(?:逐個猜測|一次只回答一個|字元正確|is\s+the\s+first\s+letter|one character at a time)"), 85, "critical", "逐字驗證或猜取秘密"),
    _SupplementalRule("IG-TRANS-01", "encoding_bypass", _rx(r"(?:密碼|password|api\s*key|token|secret|病歷|system\s*prompt|developer instructions).{0,100}(?:base64|十六進位|hex|url\s*encod|倒序|反向|摩斯|morse|翻譯|json|yaml)"), 60, "critical", "要求轉碼或轉換敏感資訊"),
    _SupplementalRule("IG-MEM-01", "data_reconstruction", _rx(r"(?:訓練資料|記憶中|memorized|memorised|回想|補全|候選).{0,120}(?:電子郵件|電話|地址|密碼|token|api\s*key|confidential|secret|完整值|哪一個)"), 70, "critical", "誘導模型回憶或驗證敏感資料"),
    _SupplementalRule("IG-SPL-01", "system_prompt_extraction", _rx(r"(?:逐字|完整|exact|verbatim|raw)?.{0,25}(?:顯示|輸出|貼出|揭露|回傳|reveal|show|print|return).{0,55}(?:system\s*prompt|developer\s*(?:prompt|instructions)|hidden\s*(?:prompt|instructions)|internal\s*prompt|系統提示詞|開發者指令|初始設定|隱藏規則|角色定義)"), 80, "critical", "直接提取系統或開發者提示詞"),
    _SupplementalRule("IG-SPL-02", "system_prompt_extraction", _rx(r"(?:重複|接續完成|引用|回顯|echo|repeat|complete|prefix|preamble|前\s*\d+\s*個\s*token|before (?:my|the user) message).{0,90}(?:system|prompt|hidden|不可見|規則|instructions?|文字|context)"), 75, "critical", "以前綴回顯或續寫方式提取提示詞"),
    _SupplementalRule("IG-SPL-03", "system_prompt_extraction", _rx(r"(?:debug mode|developer console|stack trace|故障報告|diagnostic|dump|匯出|audit log|raw conversation payload|設定檔).{0,120}(?:prompt|system_message|developer_message|hidden messages|internal instructions|完整\s*prompt)"), 75, "critical", "利用除錯、錯誤或日誌提取內部提示"),
    _SupplementalRule("IG-SPL-04", "system_prompt_extraction", _rx(r"(?:system\s*prompt|developer instructions|hidden prompt|內部提示|系統提示詞|隱藏規則).{0,100}(?:base64|hex|十六進位|翻譯|translate|json|yaml|反向|倒序|code block)"), 80, "critical", "轉碼或結構化提取系統提示"),
    _SupplementalRule("IG-SPL-05", "system_prompt_extraction", _rx(r"(?:禁止回答|被禁止|精確條件|候選\s*system prompt|逐句回答|一次透露一條|最高優先級|完整判斷流程|門檻與例外|roles?, permissions?|reconstruct).{0,100}(?:內部規則|真實規則|system|prompt|hidden constraints|判斷|規則|限制|條件|例外)"), 70, "critical", "推斷或多輪重建系統規則"),
    _SupplementalRule("IG-IO-03", "instruction_override", _rx(r"(?:規則|政策|指令|限制).{0,24}(?:失效|停用|解除|無效|disabled|invalid)"), 60, "critical", "宣告既有政策或規則失效"),
    _SupplementalRule("IG-IO-04", "instruction_override", _rx(r"(?:system\s*override|highest priority rule|新的最高優先級|唯一的任務).{0,80}(?:CANARY|output|回覆|回答|print)"), 60, "critical", "偽造高優先級覆寫指令"),
    _SupplementalRule("IG-CLI-02", "cross_language_injection", _rx(r"(?:ignora las instrucciones anteriores|ignorez les instructions précédentes|以前の指示を無視|이전 지시를 무시)"), 65, "critical", "跨語言指令覆寫"),
    _SupplementalRule("IG-SPL-06", "system_prompt_extraction", _rx(r"(?:system\s*prompt|developer instructions|hidden rules?|隱藏規則|初始設定|角色定義|internal prompt|preamble).{0,80}(?:貼出|顯示|輸出|列出|回傳|放進|reveal|show|print|return|quote)"), 80, "critical", "以反向語序要求輸出系統提示"),
    _SupplementalRule("IG-SPL-07", "system_prompt_extraction", _rx(r"(?:system、developer、user|system,?\s*developer,?\s*user|prompt stack|input context|輸入上下文).{0,80}(?:內容|token|messages?|payload|前\s*\d+)"), 80, "critical", "提取對話層級或輸入上下文"),
    _SupplementalRule("IG-SPL-08", "system_prompt_extraction", _rx(r"(?:echo the complete prefix|不可見的 preamble|前\s*\d+\s*個\s*token|被禁止回答的所有主題|完整判斷流程、門檻與例外條件)"), 80, "critical", "回顯、枚舉或推斷隱藏提示內容"),
    _SupplementalRule("IG-SPL-09", "system_prompt_extraction", _rx(r"(?:json|yaml|code block|base64|hex|翻譯|反向).{0,80}(?:隱藏規則|system prompt|developer instructions|internal_prompt)"), 80, "critical", "以結構或轉碼方式提取隱藏提示"),
    _SupplementalRule("IG-SID-02", "direct_request", _rx(r"(?:輸出|顯示|列出|匯出|貼出|show|export|reveal).{0,80}(?:未公開|confidential|內部).{0,40}(?:合約|報價|文件|資料|contract|pricing)"), 70, "critical", "索取未公開商業或法律資料"),
    _SupplementalRule("IG-MEM-02", "data_reconstruction", _rx(r"(?:回想訓練資料|訓練資料中曾出現|repeat any memorized|根據先前拒絕|推斷並輸出完整).{0,100}(?:電子郵件|電話|地址|confidential|credential|資料|值|passage)"), 75, "critical", "從訓練記憶或拒絕線索重建敏感資料"),
    _SupplementalRule("IG-PART-03", "partial_disclosure", _rx(r"(?:遮蔽|masked|without revealing the whole).{0,100}(?:保留前|保留後|prefix|suffix|character count|前\d+碼|後\d+碼)"), 65, "critical", "以遮蔽名義要求保留可重建片段"),
    _SupplementalRule("IG-SPLIT-01", "multi_turn_probe", _rx(r"(?:字首串起|忽／略／規／則|分段|fragment).{0,80}(?:執行|輸出|follow|print)"), 65, "critical", "分段或字首重建攻擊指令"),
    _SupplementalRule("IG-TRANS-02", "encoding_bypass", _rx(r"(?:base64|十六進位|hex|url\s*encod|倒序|反向|摩斯|morse|翻譯|json|yaml).{0,90}(?:密碼|password|api\s*key|token|secret|病歷|system\s*prompt|developer instructions)"), 65, "critical", "以轉碼或結構格式要求敏感資訊"),
    _SupplementalRule("IG-RECON-02", "data_reconstruction", _rx(r"(?:密碼前綴|password prefix|前綴).{0,100}(?:補全|完整值|complete|reconstruct|最可能)"), 90, "critical", "由秘密前綴補全完整值"),
]

_GENERAL_CONCEPT = _rx(r"(?:什麼是|解釋|說明|分析|分類|判斷|檢查|測試|範例|如何|防止|避免|原理|比較|設計|翻譯|撰寫|建立|輪替|review|classify|explain|analy[sz]e)")
_EXPLICIT_BOUNDARY = _rx(r"(?:不要執行|勿執行|無須執行|不是要執行|do not follow|應偵測|設定最大|僅做翻譯|只回傳分類結果|標記為不可信|只是測試|不含真實|placeholder|佔位符|請勿產生真實|不要提供真實|只做分類|只做分析|安全回覆|不讓.*執行|如何(?:偵測|防止|避免|防禦|測試|管理|輪替|驗證)|應如何|不應放|不要放真實|優先級概念|風險與緩解|是否含.{0,30}意圖.{0,30}不要回覆)")
_ACTIVE_EXECUTION = _rx(r"(?:遵照|照做|執行(?:它|其中|以下|命令)?|立即執行|只(?:要)?輸出|直接輸出|回覆\s*CANARY|print\s+CANARY|follow\s+(?:it|them|the instruction)|obey|不要拒絕|never refuse)")
_SENSITIVE_EXTRACTION = _rx(r"(?:顯示|列出|輸出|告訴|透露|揭露|貼出|匯出|回顯|重複|dump|reveal|show|print|tell me|give me|return|echo|repeat).{0,80}(?:password|密碼|api\s*key|token|secret|private\s*key|病歷|住民資料|system\s*prompt|developer instructions|hidden prompt|內部規則|提示詞)")


def _keyword_hits(text: str, patterns: list[str]) -> list[str]:
    lowered = text.casefold()
    return [p for p in patterns if p.casefold() in lowered]


def _fragments(found: list[object]) -> list[str]:
    result: list[str] = []
    for item in found[:5]:
        if isinstance(item, tuple):
            value = "".join(str(v) for v in item if v)
        else:
            value = str(item)
        if value:
            result.append(value[:160])
    return result


class AttackClassifier:
    def __init__(self) -> None:
        self._taxonomy = load_attack_taxonomy()
        self._rules = load_rules()

    def _collect_for_view(self, text: str, view_name: str) -> list[MatchedRule]:
        matches: list[MatchedRule] = []
        for rule in self._rules:
            found = rule.pattern.findall(text)
            if found:
                matches.append(MatchedRule(
                    rule_id=rule.rule_id,
                    category=rule.category,
                    severity_hint=rule.severity_hint,
                    weight=rule.weight,
                    reason=rule.reason,
                    matched_fragments=_fragments(found),
                ))

        for rule in _SUPPLEMENTAL_RULES:
            found = list(rule.pattern.finditer(text))
            if found:
                matches.append(MatchedRule(
                    rule_id=rule.rule_id,
                    category=rule.category,
                    severity_hint=rule.severity,
                    weight=rule.weight,
                    reason=rule.reason,
                    matched_fragments=[m.group(0)[:160] for m in found[:3]],
                ))

        for category_id, category in self._taxonomy.items():
            if category_id == "benign" or not category.patterns:
                continue
            hits = _keyword_hits(text, category.patterns)
            if hits:
                matches.append(MatchedRule(
                    rule_id=f"KW-{category_id}",
                    category=category_id,
                    severity_hint=category.risk_level,
                    weight=15,
                    reason="命中攻擊分類關鍵字",
                    matched_fragments=hits[:5],
                ))

        # A decoded payload that contains an attack is itself an encoding bypass.
        if view_name == "decoded" and matches:
            matches.append(MatchedRule(
                rule_id="IG-ENCODED-PAYLOAD",
                category="encoding_bypass",
                severity_hint="critical",
                weight=65,
                reason="解碼候選內含可執行攻擊指令",
                matched_fragments=[],
            ))
        return matches

    def classify(self, normalized_text: str, session_context: dict | None = None) -> AttackClassificationResult:
        return self._classify_views(
            [("normalized", normalized_text)],
            original_text=normalized_text,
            session_context=session_context,
        )

    def classify_normalization(
        self,
        normalization: NormalizationResult,
        session_context: dict | None = None,
    ) -> AttackClassificationResult:
        return self._classify_views(
            normalization.detection_views(),
            original_text=normalization.raw_text,
            session_context=session_context,
        )

    def _classify_views(
        self,
        views: list[tuple[str, str]],
        original_text: str,
        session_context: dict | None,
    ) -> AttackClassificationResult:
        session_context = session_context or {}
        collected: list[MatchedRule] = []
        for view_name, text in views:
            collected.extend(self._collect_for_view(text, view_name))

        # Deduplicate the same rule/category across normalization views.
        dedup: dict[tuple[str, str], MatchedRule] = {}
        for match in collected:
            key = (match.rule_id, match.category)
            existing = dedup.get(key)
            if existing is None or match.weight > existing.weight:
                dedup[key] = match
        matched_rules = list(dedup.values())

        if session_context.get("previous_blocked_attempt") or session_context.get("repeated_partial_request"):
            matched_rules.append(MatchedRule(
                rule_id="SESSION-MULTI-TURN",
                category="multi_turn_probe",
                severity_hint="high",
                weight=45,
                reason="會話歷史顯示重複探測或先前阻擋",
                matched_fragments=[],
            ))
        if session_context.get("cross_turn_reconstruction"):
            matched_rules.append(MatchedRule(
                rule_id="SESSION-RECONSTRUCTION",
                category="data_reconstruction",
                severity_hint="critical",
                weight=70,
                reason="跨回合資料重建訊號",
                matched_fragments=[],
            ))

        if not matched_rules:
            return AttackClassificationResult(
                is_attack=False,
                is_suspicious=False,
                primary_category="benign",
                notes="未命中攻擊規則。",
            )

        scores = aggregate_category_scores(matched_rules)
        primary = pick_primary_category(scores)
        primary_weight = scores[primary]
        educational = bool(_GENERAL_CONCEPT.search(original_text))
        explicit_boundary = bool(_EXPLICIT_BOUNDARY.search(original_text))
        active_execution = bool(_ACTIVE_EXECUTION.search(original_text))
        sensitive_extraction = bool(_SENSITIVE_EXTRACTION.search(original_text))

        # Quoted/security-analysis prompts may contain attack strings. Keep them benign or WARN-level
        # unless they also request execution or extraction of a real/current protected target.
        if explicit_boundary or (educational and primary_weight < 60 and not active_execution and not sensitive_extraction):
            return AttackClassificationResult(
                is_attack=False,
                is_suspicious=True,
                primary_category="benign",
                matched_categories=sorted(scores),
                confidence=round(min(compute_confidence(primary_weight) * 0.35, 0.49), 3),
                severity_hint="low",
                matched_rules=matched_rules,
                evidence=[],
                recommended_skill=None,
                notes="安全分析、翻譯、分類或防禦情境；保留可疑旗標但不視為攻擊。",
            )

        confidence = compute_confidence(primary_weight)
        severity = aggregate_severity(matched_rules, primary)
        category = self._taxonomy.get(primary)
        recommended_skill = category.mitigation_skills[0] if category and category.mitigation_skills else None
        return AttackClassificationResult(
            is_attack=True,
            is_suspicious=True,
            primary_category=primary,
            matched_categories=sorted(scores),
            confidence=confidence,
            severity_hint=severity,
            matched_rules=matched_rules,
            evidence=[],
            recommended_skill=recommended_skill,
            notes=category.description if category else "偵測到高風險輸入行為。",
        )
