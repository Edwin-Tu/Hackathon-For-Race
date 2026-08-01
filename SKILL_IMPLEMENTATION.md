# Skill Layer Implementation

## Scope

This version adds a lightweight Skill layer between deterministic intent routing and the Bedrock prompt/tool configuration.

It does not replace ToolGateway. Skills guide model behaviour; ToolGateway remains authoritative for authorization, schema validation, confirmation, idempotency, timeout, audit, and execution.

## Included skills

| Skill | Purpose | Allowed tools |
|---|---|---|
| `care_event_skill` | Record completed care events and request missing time details | `create_care_event` |
| `reminder_skill` | Create future reminders and handle confirmation-sensitive reminders | `create_reminder` |
| `schedule_query_skill` | Read existing schedules only | `get_user_schedule` |
| `safe_reply_skill` | Traditional Chinese, TTS-friendly, evidence-bound replies | None |
| `security_refusal_skill` | Short-circuit obvious prompt override, secret extraction, or dangerous tool requests | None |

## Runtime flow

```text
User message
  -> deterministic intent router
  -> SkillRegistry.route()
  -> selected skill instructions
  -> filtered Bedrock toolConfig
  -> Claude Haiku 4.5
  -> ToolGateway
```

If `security_refusal_skill` blocks a request, the Bedrock provider is not called and no tool is exposed.

## Frozen boundaries

The Skill layer may select instructions and narrow model-visible tools. It must not:

- authorize a user;
- inject a trusted Persona ID;
- validate tool arguments;
- execute handlers;
- bypass confirmation or idempotency;
- claim an operation succeeded.

Those responsibilities remain in ToolGateway and backend evidence handling.

## Validation

```bash
uv run pytest -q
uv run python -m scripts.skill_demo
uv run python -m compileall -q app scripts tests
```

Validation result for this package: `79 passed`.
