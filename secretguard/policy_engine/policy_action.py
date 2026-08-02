"""政策動作列舉（F10 4.5：PolicyAction）。

實際定義集中於 secretguard.common.enums.PolicyAction，此處重新匯出，
對應規格文件中 policy_engine 套件下應有 policy_action 檔案的結構。
"""

from __future__ import annotations

from secretguard.common.enums import ACTION_SEVERITY, PolicyAction, max_severity_action

__all__ = ["PolicyAction", "ACTION_SEVERITY", "max_severity_action"]
