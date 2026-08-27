# Feature Specification: Session Budget Enforcement Guardrails

**Feature Branch**: `109-session-budget-guardrails`
**Created**: 2026-08-14
**Status**: Draft
**Input**: Live operational incident — a 7-question conversational session from a mobile (iPhone/N2N) interface generated 59 assistant turns, 82 tool calls, ~3M input tokens, and $11.13 USD in API costs over 2 hours using claude-sonnet-5 with `thinkingLevel: high`. The existing `netclaw_tokens` library tracks and displays costs (observability-only) but never enforces any ceiling. The alert agent has budget guardrails (hourly caps, concurrency limits, cheap model default) but the main agent — which handles all conversational/N2N/phone sessions — has zero cost controls.

## Problem Statement

The `netclaw_tokens` library (`src/netclaw_tokens/`) provides:
- Token counting per interaction
- Model-aware cost calculation
- Session-level cumulative tracking (SessionLedger)
- GCF serialization for token savings
- Footer display showing costs to the operator

What it does NOT provide:
- **Enforcement** — no mechanism halts or downgrades a session when costs exceed a threshold
- **Per-interface routing** — mobile/N2N sessions inherit the same expensive model as desktop
- **Tool-call depth limits** — an agentic chain can run unlimited tool calls per user message
- **Context growth control** — tool results accumulate in context forever, causing input tokens to balloon quadratically across turns

The alert agent (`agents.list[1]`) demonstrates the correct pattern: it uses `claude-haiku-4-5`, has a restricted tool allowlist, and the alert-receiver enforces hourly/concurrent budget caps via `netclaw_investigation_budget_trips_total`. This feature extends that pattern to ALL agent sessions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Session cost cap halts runaway spending (Priority: P1)

As a NetGeniusClaw operator, I want a configurable per-session cost ceiling so that when cumulative spending in a single session exceeds my threshold (e.g., $2.00), the agent stops tool-calling and informs me it has hit the budget — rather than silently burning $11+ on a casual phone question.

**Why this priority**: This is the exact failure that occurred. A cost cap alone would have limited the damage from $11 to $2 without any other changes.

**Independent Test**: Start a session, configure a $0.50 budget cap, issue a question that would normally trigger expensive multi-tool chains. Verify the agent halts after reaching the cap and returns a budget-exceeded message with the accumulated cost summary.

**Acceptance Scenarios**:

1. **Given** a session with `session_budget_usd: 2.0` configured, **When** cumulative cost (tracked by SessionLedger) exceeds $2.00, **Then** the agent stops making further API calls and returns a message indicating the budget was reached, including the cost breakdown.
2. **Given** a session with no explicit budget configured, **When** costs accumulate, **Then** the system uses a sensible default ceiling (e.g., $5.00) rather than unlimited.
3. **Given** a session that has been budget-halted, **When** the operator explicitly requests continuation (e.g., "continue" or "override budget"), **Then** the budget resets or extends by the configured increment, allowing the session to proceed.
4. **Given** a budget halt occurs mid-tool-chain, **When** the agent stops, **Then** it provides a partial summary of what it accomplished before the halt, not a raw error.

---

### User Story 2 - Tool-call depth limit per user message (Priority: P2)

As a NetGeniusClaw operator, I want a configurable maximum number of tool calls per user message so that a single question cannot trigger a 59-turn, 82-tool-call exploration — the agent must summarize its findings and ask for direction after N tool calls instead of running indefinitely.

**Why this priority**: Even with a cost cap, unbounded tool chains waste tokens on low-value exploration. A depth limit forces the agent to be deliberate about which tools it invokes.

**Independent Test**: Configure `max_tool_calls_per_turn: 15`. Issue a question that would normally generate 50+ tool calls. Verify the agent stops after 15 tool calls, summarizes findings so far, and asks whether to continue.

**Acceptance Scenarios**:

1. **Given** `max_tool_calls_per_turn: 15` configured, **When** a user message triggers tool use, **Then** the agent executes at most 15 tool calls before pausing and presenting intermediate results.
2. **Given** the tool-call limit is reached, **When** the agent pauses, **Then** it summarizes what was found so far and asks "Should I continue investigating?" rather than silently stopping.
3. **Given** the operator says "yes, continue", **When** the agent resumes, **Then** the tool-call counter resets for the next batch of N calls.
4. **Given** no explicit tool-call limit is configured, **Then** a sensible default applies (e.g., 20 tool calls per user message).

---

### User Story 3 - Per-interface model routing (Priority: P3)

As a NetGeniusClaw operator, I want different model defaults based on the session interface (mobile/N2N vs. desktop/TUI vs. alert) so that casual phone questions use a cheaper model by default while I can still explicitly request an expensive model when needed.

**Why this priority**: Model routing prevents the problem at the source — if mobile sessions default to Haiku ($1/M in, $5/M out) instead of Sonnet 5 ($3/$15), the same 59-turn session would have cost ~$2 instead of $11. But it's P3 because cost caps (P1) and tool limits (P2) provide protection regardless of model choice.

**Independent Test**: Send a message via the OpenAI-compat/N2N interface without an explicit model override. Verify it routes to the configured mobile-default model (e.g., haiku). Then send a message with an explicit "use sonnet" prefix and verify it upgrades.

**Acceptance Scenarios**:

1. **Given** `interface_defaults.mobile.model: "anthropic/claude-haiku-4-5"` configured, **When** a session arrives via the OpenAI-compat gateway (N2N/mobile), **Then** it uses Haiku unless the user explicitly requests a different model.
2. **Given** a mobile session using Haiku, **When** the user says "use sonnet for this" or equivalent escalation command, **Then** the model upgrades for that session only.
3. **Given** a TUI/desktop session, **When** no interface default is configured for that interface, **Then** it falls back to the agent's `model.primary` setting (existing behavior, no regression).
4. **Given** an explicit model override in the message, **Then** it always takes precedence over interface defaults.

---

### User Story 4 - Context growth awareness (Priority: P4)

As a NetGeniusClaw operator, I want the session to emit a warning (and optionally auto-summarize) when accumulated context size exceeds a threshold, so I'm aware that continued conversation will be expensive and can choose to start fresh.

**Why this priority**: This is a UX improvement that helps operators make informed decisions. The cost cap (P1) provides hard protection; this provides soft awareness before the cap is hit.

**Independent Test**: Configure `context_warning_tokens: 100000`. Have a multi-turn session that accumulates large tool results. Verify a warning is emitted when context crosses 100K tokens, showing the approximate cost-per-turn going forward.

**Acceptance Scenarios**:

1. **Given** `context_warning_tokens: 100000` configured, **When** cumulative session context exceeds 100K tokens, **Then** the agent emits an inline warning showing current context size and approximate cost-per-additional-turn.
2. **Given** the warning has been shown, **When** context doubles again (200K), **Then** a stronger warning suggests starting a new session or summarizing.
3. **Given** `context_auto_summarize: true` configured, **When** context exceeds the threshold, **Then** old tool results are summarized into a compact form before being re-sent as context.

---

### Edge Cases

- What happens when the cost cap is hit mid-sentence (during streaming)? → The current turn completes, but no further turns are initiated.
- What happens if the Prometheus metrics exporter is down and cost tracking fails? → SessionLedger is in-process (thread-safe Python); it doesn't depend on Prometheus. Enforcement works regardless of metrics export.
- What happens if multiple sessions run concurrently against the same API key? → Each session has its own SessionLedger instance. Budgets are per-session, not global (global daily caps are a future enhancement, not in scope here).
- What happens if the model price changes between config reload and enforcement? → The cost calculator re-reads pricing on each call; enforcement uses real-time cost, not stale values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: SessionLedger MUST expose an `is_over_budget()` method that returns True when `total_cost` exceeds the configured session ceiling.
- **FR-002**: The gateway's turn-dispatch loop MUST check `is_over_budget()` before sending a new request to the model API and halt gracefully if True.
- **FR-003**: A budget halt MUST produce a user-visible message including: accumulated cost, token counts, top tools by cost, and whether continuation is available.
- **FR-004**: SessionLedger MUST expose a `tool_calls_this_turn` counter that resets on each user message and is checked before each tool invocation.
- **FR-005**: Budget configuration MUST be expressible in `openclaw.json` under `agents.defaults` and overridable per-agent in `agents.list[]`.
- **FR-006**: Interface-based model routing MUST be configurable via a new `agents.defaults.interfaceDefaults` map keyed by interface type (e.g., `openai`, `tui`, `n2n`, `discord`).
- **FR-007**: Budget enforcement MUST emit a Prometheus counter (`netclaw_session_budget_trips_total`) with labels `{agent, reason}` where reason is `cost_cap` or `tool_limit`, consistent with the existing `netclaw_investigation_budget_trips_total` pattern.
- **FR-008**: The context warning system MUST calculate approximate tokens from the session message history without requiring an API call (use the existing `count_tokens` estimator).
- **FR-009**: Budget override/continuation MUST require an explicit user action (not automatic) — the agent must not silently resume spending.
- **FR-010**: All budget settings MUST have documented defaults that are safe for a hobbyist/personal deployment (e.g., $5 session cap, 20 tool calls per turn).

### Key Entities

- **BudgetPolicy**: Configuration object holding `session_budget_usd`, `max_tool_calls_per_turn`, `context_warning_tokens`, `context_auto_summarize`. Lives in `openclaw.json`.
- **SessionLedger** (existing): Extended with budget-checking methods and turn-level tool-call tracking.
- **InterfaceDefaults**: Map of interface type → model/thinkingLevel/budgetPolicy overrides.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A session that would previously accumulate >$5 in costs is halted at or below the configured ceiling (±10% tolerance for in-flight completion).
- **SC-002**: No session can execute more than `max_tool_calls_per_turn` tool calls without operator confirmation, default 20.
- **SC-003**: Mobile/N2N sessions default to a model costing ≤$1/M input tokens unless explicitly overridden.
- **SC-004**: The `netclaw_session_budget_trips_total` counter increments on every halt, enabling Prometheus-based alerting on runaway sessions.
- **SC-005**: Zero regression for existing alert-agent behavior — its existing budget enforcement (via alert-receiver) continues unchanged.
- **SC-006**: A repeat of the $11 incident scenario (7 phone questions, agentic tool chains) results in ≤$2 total cost with default settings.

---

### User Story 5 - Budget protection works out of the box (Priority: P1-B)

As a new NetGeniusClaw operator installing the system for the first time, I want budget enforcement to be active by default with safe limits — so that I never get a surprise API bill before I even know the budget feature exists.

**Why this priority**: Equal to P1. If the feature exists but requires manual setup, most operators will discover it AFTER the surprise bill, which defeats the purpose entirely.

**Independent Test**: Fresh install of NetGeniusClaw with no budget-related configuration in openclaw.json. Send 30+ messages via the OpenAI-compat interface. Verify that budget enforcement activates at the default $5 ceiling without any operator action.

**Acceptance Scenarios**:

1. **Given** a fresh NetGeniusClaw installation with no `budget` section in openclaw.json, **When** a session accumulates costs, **Then** the default $5 cap is enforced automatically.
2. **Given** the `token-tracker` skill is loaded (which it is by default), **When** the session starts, **Then** `BudgetPolicy` is initialized from defaults without requiring any explicit configuration.
3. **Given** an operator upgrades NetGeniusClaw to a version containing this feature, **When** they restart the gateway, **Then** budget enforcement is active on the next session with no migration step required.

---

### User Story 6 - Operator sees budget status in the HUD (Priority: P2-B)

As a NetGeniusClaw operator, I want to see my session's spending status in real time in the HUD footer — remaining budget, cost-per-turn, and a visual indicator when approaching the cap — so I can make informed decisions without waiting for a hard stop.

**Why this priority**: The HUD is the operator's primary interface. Budget status that's invisible until it halts is a jarring experience. Seeing "Budget: $2.10 / $5.00" in the footer gives the operator agency.

**Independent Test**: Open the HUD while a session is active. Verify the footer shows current session cost, budget ceiling, and a color indicator (green → yellow → red as cost approaches ceiling).

**Acceptance Scenarios**:

1. **Given** a session is active, **When** the operator views the HUD, **Then** the footer shows `Budget: $X.XX / $Y.YY` with the current session cost and ceiling.
2. **Given** the session cost exceeds 70% of the budget, **When** the HUD refreshes, **Then** the budget indicator turns yellow/amber.
3. **Given** the session has been halted by a budget trip, **When** the HUD refreshes, **Then** a clear "BUDGET PAUSED" indicator is shown with the halt reason.
4. **Given** the operator wants to adjust the budget, **When** they click the budget indicator in the HUD, **Then** they can set a new ceiling for the current session (or globally) without editing JSON.

---

### User Story 7 - Budget configuration via HUD (Priority: P3-B)

As a NetGeniusClaw operator, I want to configure my budget caps and model routing through the HUD settings panel — so I never have to SSH into a box and edit openclaw.json by hand to adjust spending limits.

**Why this priority**: Configuration through the UI is the "reality wrapper" that makes this feature accessible. Without it, only operators comfortable with JSON config files benefit.

**Independent Test**: Open the HUD settings. Adjust the session budget from $5 to $10. Start a new session and verify the new budget applies.

**Acceptance Scenarios**:

1. **Given** the HUD is open, **When** the operator navigates to settings/budget, **Then** they see current budget policy values (session cap, tool-call limit, interface defaults) in editable fields.
2. **Given** the operator changes the session budget in the HUD, **When** they save, **Then** the value is persisted to openclaw.json and applies to the next session.
3. **Given** the operator wants per-interface routing, **When** they configure "Mobile model: Haiku" in the HUD, **Then** subsequent openai/n2n sessions use Haiku.

---

## Integration Architecture

### How enforcement actually works (gateway integration)

The OpenClaw gateway is a Node.js process. The `netclaw_tokens` Python library is consumed via the **token-tracker skill** — the gateway's agent runtime loads the skill which imports and uses the library. The enforcement flow:

```
User message arrives
  → Gateway identifies session key → resolve_session_config() → BudgetPolicy
  → SessionLedger initialized (or resumed) with BudgetPolicy
  → new_turn() called (resets tool-call counter)
  → For each model API call or tool invocation:
      → check_budget() → (should_halt, reason)
      → If should_halt: return halt message to user, emit Prometheus metric, stop
      → If OK: proceed with call, record tokens/cost, record_tool_call()
```

The skill (not the gateway binary) is the enforcement point. This means:
- No changes to the OpenClaw npm package required
- Enforcement is opt-out (remove the skill) rather than requiring opt-in
- The skill ships with the `workspace/skills/` directory on install

### HUD integration

The HUD server (`ui/netclaw-visual/server.js`) already serves `/api/gateway/status` and `/api/sessions`. Budget status is exposed via:
- New endpoint: `GET /api/budget/status` — returns current session cost, ceiling, halt state
- New endpoint: `PUT /api/budget/config` — updates budget policy in openclaw.json
- Footer element: `<span>Budget <strong id="footer-budget">--</strong></span>`
- WebSocket event: budget status pushed on each model call completion

### Install story

On fresh install or upgrade:
1. The `token-tracker` skill (already default) is extended to include budget enforcement
2. `BudgetPolicy()` with no args produces safe defaults ($5 cap, 20 tool calls)
3. No openclaw.json section needed — absence of config = defaults apply
4. The env var `NETCLAW_SESSION_BUDGET_USD` works immediately for quick overrides
5. The HUD shows budget status as soon as the gateway is running

**Zero configuration required. Safe by default. Configurable via UI.**

## Assumptions

- The token-tracker skill is the correct enforcement integration point (it already wraps every model API call for token counting — budget checking is a single additional function call at the same site).
- SessionLedger is instantiated per-session and persists for the session lifetime (confirmed by code review — it's a class instance, not a global singleton).
- The `openclaw.json` config is the appropriate place for budget settings (it already holds model config, agent definitions, and the tokenOptimization block).
- Prompt caching is already active and will continue to reduce costs for repeated context — budget enforcement accounts for actual cost (post-cache-discount), not theoretical worst-case.
- The HUD server already reads/writes openclaw.json (confirmed — `/api/env` endpoint pattern) and can extend to budget config.
- The token-tracker skill is loaded by default on new installs (confirmed — it's in `workspace/skills/`).
