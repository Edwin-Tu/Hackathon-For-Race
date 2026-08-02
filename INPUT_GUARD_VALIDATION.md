# Input Guard validation

## Public API

```python
from secretguard.input_guard import InputGuardRequest, InputGuardService

service = InputGuardService()
decision = service.inspect(
    InputGuardRequest(
        request_id="req-001",
        session_id="session-001",
        text="幫我記錄住民今天下午散步三十分鐘。",
        user_role="staff",
        authorization_status="authorized",
    )
)

print(decision.to_dict())
```

The caller must provide `user_role` and `authorization_status` from trusted server-side context. A role claim written inside the prompt is never treated as authorization.

## Run validation

```bash
python -m unittest discover -s tests -v
python scripts/evaluate_input_guard.py \
  --output reports/input_guard_evaluation.json
```

The bundled dataset contains 180 deterministic cases:

- LLM01 Prompt Injection: 30
- LLM02 Sensitive Information Disclosure: 30
- LLM07 System Prompt Leakage: 30
- General benign prompts: 30
- Boundary benign prompts: 30
- Benign prompts containing sensitive vocabulary: 30

## Security properties covered

- Attack risk is independent of authorization state.
- System-prompt extraction is blocked even for `owner`.
- Multi-view normalization feeds decoded and symbol-stripped views into detection.
- Decoded candidates are never treated as executable instructions.
- Serialized normalization, asset-match, and token-match results omit raw secrets.
- Excessive input and control-character payloads fail closed.
