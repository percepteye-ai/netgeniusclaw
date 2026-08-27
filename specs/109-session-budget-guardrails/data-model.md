# Data Model: Session Budget Enforcement Guardrails

**Branch**: `109-session-budget-guardrails` | **Date**: 2026-08-14

## §1 BudgetPolicy (New Dataclass)

```python
@dataclass
class BudgetPolicy:
    """Per-session budget enforcement configuration."""
    session_budget_usd: float = 5.0          # Max cost per session before halt
    max_tool_calls_per_turn: int = 20        # Max tool invocations per user message
    context_warning_tokens: int = 100_000    # Warn when context exceeds this
    context_auto_summarize: bool = False     # Auto-summarize old tool results
    allow_override: bool = True              # Whether operator can say "continue"
    override_increment_usd: float = 2.0     # How much budget extends on override
```

**Defaults rationale**: $5.00 session cap × Sonnet 5 pricing = ~1.6M input tokens or ~333K output tokens before halt. For Haiku, it's ~5M input tokens. 20 tool calls per turn is generous for a deliberate investigation but would have stopped the $11 incident at 20 instead of 82.

## §2 SessionLedger Extensions

Existing fields (unchanged):
- `session_id: str`
- `started_at: datetime`
- `total_input_tokens: int`
- `total_output_tokens: int`
- `total_cost: float`
- `total_gcf_savings: int`
- `total_call_count: int`
- `tool_breakdown: Dict[str, ToolUsageRecord]`

New fields:
- `budget: BudgetPolicy` — loaded at session init from config
- `tool_calls_this_turn: int` — resets on each user message
- `budget_halted: bool` — set True when ceiling hit
- `halt_reason: Optional[str]` — "cost_cap" | "tool_limit" | None
- `interface_type: Optional[str]` — "openai" | "tui" | "n2n" | "discord" | etc.

New methods:
- `is_over_budget() -> bool` — returns True if `total_cost >= budget.session_budget_usd`
- `is_over_tool_limit() -> bool` — returns True if `tool_calls_this_turn >= budget.max_tool_calls_per_turn`
- `should_warn_context(context_tokens: int) -> bool` — returns True if context exceeds threshold
- `record_tool_call()` — increments `tool_calls_this_turn` (separate from `record()` which tracks tokens)
- `new_turn()` — resets `tool_calls_this_turn` to 0 (called on each user message)
- `override_budget()` — extends ceiling by `override_increment_usd`, clears `budget_halted`
- `get_halt_message() -> str` — formatted user-facing message with cost breakdown

## §3 InterfaceDefaults (New Config Section)

```json
{
  "interfaceDefaults": {
    "<interface_type>": {
      "model": "<provider>/<model-id>",
      "thinkingLevel": "low|medium|high",
      "budget": { /* BudgetPolicy overrides */ }
    }
  }
}
```

Interface type is derived from the session key pattern:
- `agent:*:openai:*` → `"openai"`
- `agent:*:tui-*` → `"tui"`
- `agent:*:discord:*` → `"discord"`
- `agent:*:n2n` → `"n2n"`
- `agent:*:hook:alert:*` → `"alert"` (unchanged, uses own agent config)
- `agent:*:explicit:*` → `"explicit"`

## §4 Configuration Location

Lives in `openclaw.json` under `agents.defaults.budget` (global default) with
per-agent override possible in `agents.list[].budget`.

Environment variable override: `NETCLAW_SESSION_BUDGET_USD` (float) — takes
precedence over JSON config, useful for quick adjustments without config reload.

## §5 Prometheus Metrics (New)

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `netclaw_session_budget_trips_total` | Counter | `agent`, `reason`, `interface` | Increments on each budget halt |
| `netclaw_session_budget_remaining_usd` | Gauge | `agent`, `session_id` | Current remaining budget (useful for dashboards) |
| `netclaw_session_tool_calls_total` | Counter | `agent`, `interface` | Total tool calls across all sessions |
