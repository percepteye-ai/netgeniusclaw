# Requirements Checklist: 109-session-budget-guardrails

## Functional Requirements

- [ ] FR-001: SessionLedger exposes `is_over_budget()` method
- [ ] FR-002: Gateway turn-dispatch checks budget before each model API call
- [ ] FR-003: Budget halt produces user-visible message with cost breakdown
- [ ] FR-004: SessionLedger exposes `tool_calls_this_turn` counter
- [ ] FR-005: Budget config expressible in `openclaw.json` under `agents.defaults`
- [ ] FR-006: Interface-based model routing via `interfaceDefaults` map
- [ ] FR-007: Budget enforcement emits `netclaw_session_budget_trips_total` Prometheus counter
- [ ] FR-008: Context warning calculates tokens without API call
- [ ] FR-009: Budget override requires explicit user action
- [ ] FR-010: All settings have documented safe defaults

## Success Criteria

- [ ] SC-001: Session halts at/below configured ceiling (±10% for in-flight)
- [ ] SC-002: No more than `maxToolCallsPerTurn` tool calls without confirmation
- [ ] SC-003: Mobile/N2N defaults to model ≤$1/M input
- [ ] SC-004: `netclaw_session_budget_trips_total` increments on halt
- [ ] SC-005: Zero regression for alert-agent behavior
- [ ] SC-006: Repeat of $11 scenario results in ≤$2 with defaults

## User Stories Acceptance

### US1 — Cost Cap (P1)
- [ ] Halts at configured ceiling
- [ ] Uses sensible default ($5) when unconfigured
- [ ] Override/continue works on explicit request
- [ ] Partial summary provided on halt

### US2 — Tool-Call Depth (P2)
- [ ] Pauses at configured limit
- [ ] Summarizes findings before pausing
- [ ] Continuation resets counter
- [ ] Default limit (20) applies when unconfigured

### US3 — Interface Routing (P3)
- [ ] Mobile/N2N defaults to cheap model
- [ ] Explicit model request overrides default
- [ ] TUI/desktop inherits agent primary (no regression)
- [ ] Interface detection works for all known key patterns

### US4 — Context Warning (P4)
- [ ] Warning emitted at threshold
- [ ] Warning includes cost-per-turn estimate
- [ ] No warning below threshold
