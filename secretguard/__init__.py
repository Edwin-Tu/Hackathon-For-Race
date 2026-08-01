"""SecretGuard 防禦管線套件。

依 F09~F13 規格文件實作：
- F09 攻擊分類與防禦技能 (attack_classifier / defensive_skills / skill_router)
- F10 風險評分與政策引擎 (risk_scoring / policy_engine / policy_builder)
- F11 輸入正規化與保護提示詞建構 (input_normalization / prompt_builder)
- F12 輸出守衛與洩漏驗證 (output_guard / leakage_verifier)
- F13 資產註冊與 Token 守衛 (asset_registry / token_guard)
"""

__version__ = "0.1.0"
