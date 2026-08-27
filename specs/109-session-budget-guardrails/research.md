# Research: Session Budget Enforcement Guardrails

**Branch**: `109-session-budget-guardrails` | **Date**: 2026-08-14

## R0: Confirmed Live Incident (Primary Input)

On 2026-08-14, a 7-message iPhone session via the N2N/OpenAI-compat interface
burned $11.13 in 2 hours. Prometheus metrics confirm:

| Hour (UTC) | API Calls | Output Tokens | Est. Input Tokens | Cost |
|------------|-----------|---------------|-------------------|------|
| 04:00–05:00 | 25 | 25,216 | ~1.3M | $4.36 |
| 05:00–06:00 | 29 | 35,026 | ~1.5M | $4.93 |
| 13:00–14:00 | 5 | 5,576 | ~200K | $1.83 |

Root causes:
1. **No cost enforcement** — SessionLedger tracks but never halts.
2. **Sonnet 5 + high thinking** for a casual phone question — no interface-based routing.
3. **82 tool calls** across 59 assistant turns — no depth limit.
4. **Context balloon** — tool results (including a 55KB GitHub file read) accumulated in context, causing ~53K tokens per API call average.

## R1: Existing Enforcement Pattern (Alert Agent)

The alert-receiver (`scripts/alert-receiver/`) already implements budget
enforcement for the alert agent:

- `netclaw_investigation_budget_trips_total{budget="hourly"}` — tracks cap hits
- `netclaw_investigation_budget_trips_total{budget="concurrent"}` — concurrency gate
- Alert agent config forces `qwen/qwen3.5-4b` model
- Alert agent has a restricted tool allowlist

This pattern is correct and proven. It just wasn't extended to conversational
sessions.

## R2: SessionLedger Architecture (Current State)

`src/netclaw_tokens/session_ledger.py` provides:
- Thread-safe accumulator (`threading.Lock`)
- Per-session UUID tracking
- `total_cost`, `total_input_tokens`, `total_output_tokens`
- Per-tool breakdown
- `get_summary()` / `get_gait_summary()` for reporting

What's missing:
- No `budget_usd` field or `is_over_budget()` check
- No `tool_calls_this_turn` counter
- No method to signal "halt" to the caller
- No configuration loading (budget values are not read from anywhere)

## R3: Gateway Turn-Dispatch Integration Point

The OpenClaw gateway (`openclaw` npm package, running as PID 1483246) dispatches
model API calls. The `netclaw_tokens` library is invoked as a Python module via
the gateway's plugin system. The enforcement hook needs to:

1. Be called BEFORE each model API request
2. Have authority to prevent the request from executing
3. Return a structured "budget exceeded" response the gateway can surface to the user

The `tokenOptimization` config block in `openclaw.json` is already read by the
gateway to enable/disable token tracking. Budget config can live alongside it or
in the agent definition.

## R4: Interface Detection

Sessions arrive via different interfaces, identifiable by session key prefix:
- `agent:main:openai:*` — OpenAI-compat gateway (iPhone, mobile apps)
- `agent:main:tui-*` — Terminal UI (desktop)
- `agent:main:discord:*` — Discord bot
- `agent:main:n2n` — N2N federation
- `agent:main:hook:alert:*` — Alert webhooks (already has own agent/budget)
- `agent:main:explicit:*` — Explicit skill invocations

The interface type is known at session creation time and can be used to select
model defaults and budget policies.

## R5: Cost Model (Sonnet 5 vs Haiku)

At current pricing:
- **Sonnet 5**: $3/M input, $15/M output — the $11 session
- **Haiku 4.5**: $1/M input, $5/M output — would have been ~$3.70 for same tokens
- **Ollama/local**: $0 — but quality tradeoff for complex reasoning

A mobile-default of Haiku + a $2 session cap would have limited this incident to
~$2 total (Haiku pricing × 20-tool-call limit before first pause).

## R6: Industry Patterns

- **OpenAI API usage caps**: Hard monthly limits, no per-session granularity
- **the model endpoint**: Rate limits but no cost caps (that's the client's job)
- **LangChain callbacks**: `max_iterations` on agent loops, `max_execution_time`
- **AutoGPT budget**: `--budget` flag that halts at a dollar amount
- **OpenClaw alert-receiver**: Hourly + concurrent caps (already in this codebase)

The AutoGPT pattern (budget flag → halt + report) is closest to what we need.
The LangChain `max_iterations` pattern maps to our tool-call-depth limit.
