# Implementation Plan: Session Budget Enforcement Guardrails

**Branch**: `109-session-budget-guardrails` | **Date**: 2026-08-14 | **Spec**: `specs/109-session-budget-guardrails/spec.md`
**Input**: Feature specification + research from live $11 cost incident

## Summary

Extend the existing `netclaw_tokens` SessionLedger with enforcement capabilities
(cost ceiling, tool-call depth limit) and add configuration schema for per-agent
and per-interface budget policies. The enforcement hooks integrate with the
OpenClaw gateway's existing token-optimization plugin path.

## Technical Context

**Language/Version**: Python 3.12 (library), Node.js (gateway consumer)
**Primary Dependencies**: `netclaw_tokens` (existing library, `src/netclaw_tokens/`)
**Storage**: In-memory (SessionLedger is per-session, already thread-safe)
**Testing**: pytest (existing test infrastructure in `tests/`)
**Target Platform**: Linux server (OpenClaw gateway runtime)
**Project Type**: Library extension + configuration schema
**Performance Goals**: `is_over_budget()` check must be <1ms (it's a float comparison)
**Constraints**: Zero regression for existing alert-agent behavior; no gateway binary changes required
**Scale/Scope**: Single-operator deployments (hobby/personal), 1-10 concurrent sessions

## Project Structure

### Documentation (this feature)

```text
specs/109-session-budget-guardrails/
├── spec.md              # Feature specification (done)
├── research.md          # Research findings (done)
├── plan.md              # This file
├── data-model.md        # Budget configuration schema
├── quickstart.md        # Operator setup guide
└── tasks.md             # Implementation tasks
```

### Source Code (repository root)

```text
src/netclaw_tokens/
├── __init__.py              # Extended with BudgetPolicy dataclass
├── session_ledger.py        # Extended with enforcement methods
├── budget_policy.py         # NEW: BudgetPolicy loading + defaults
└── cost_calculator.py       # Unchanged (already correct)

tests/
├── test_session_budget.py   # NEW: Budget enforcement unit tests
└── test_budget_policy.py    # NEW: Config loading tests
```

### Configuration (openclaw.json schema addition)

```json
{
  "agents": {
    "defaults": {
      "budget": {
        "sessionBudgetUsd": 5.0,
        "maxToolCallsPerTurn": 20,
        "contextWarningTokens": 100000,
        "contextAutoSummarize": false
      },
      "interfaceDefaults": {
        "openai": { "model": "local/qwen/qwen3.5-4b", "thinkingLevel": "medium" },
        "n2n": { "model": "local/qwen/qwen3.5-4b", "thinkingLevel": "medium" },
        "discord": { "model": "local/qwen/qwen3.5-4b", "thinkingLevel": "low" },
        "tui": {},
        "explicit": {}
      }
    }
  }
}
```

**Structure Decision**: This is a library extension — new functionality lives in the existing `src/netclaw_tokens/` package alongside the existing cost calculator and session ledger. No new top-level directories needed.
