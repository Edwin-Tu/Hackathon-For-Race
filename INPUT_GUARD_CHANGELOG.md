# Input Guard correction summary

## Added

- Unified `secretguard.input_guard.InputGuardService` entry point.
- Typed request, decision, and risk-breakdown models.
- Pre-validation for input type, length, NUL bytes, and control-character ratio.
- Multi-view classification over normalized, case-folded, symbol-stripped, and decoded views.
- Deterministic intent inference and server-side authorization separation.
- In-memory session signals for blocked attempts, encoding-after-refusal, and reconstruction attempts.
- 180-case OWASP LLM01/LLM02/LLM07 validation dataset.
- Dataset evaluator and JSON report.
- Security regression tests.

## Corrected

- Authorization no longer subtracts from prompt-injection attack risk.
- `owner` and `authorized` identities cannot downgrade system-prompt extraction or instruction override.
- Attack risk and access risk are scored separately.
- Policy uses hard rules before score thresholds.
- Quoted attack strings, defensive analysis, ordinary translation, and sensitive security vocabulary are recognized as benign contexts.
- Input normalization transformations no longer serialize original or decoded text.
- Asset and token match serialization no longer returns raw matched values.
- Exact protected values are redacted from `InputGuardDecision.normalized_text`.
- Encoding probes are bounded by candidate, token, and decoded-length limits.

## Validation result

- Dataset: 180 / 180 expected decisions passed.
- LLM01: 30 / 30.
- LLM02: 30 / 30.
- LLM07: 30 / 30.
- Normal prompts: 90 / 90.
- Security regression tests: 9 / 9.
