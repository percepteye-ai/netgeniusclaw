# Data Model: Token Optimization (Count + TOON)

**Feature**: 006-token-optimization
**Date**: 2026-03-26

## Entities

### TokenCount

A record of token usage for a single LLM interaction or tool call.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| input_tokens | int | Number of input tokens consumed | >= 0 |
| output_tokens | int | Number of output tokens generated | >= 0 |
| model | str | Model identifier (e.g., "claude-opus-4-6") | Must be in PRICING dict |
| timestamp | datetime | When the count was recorded | Auto-set to now() |
| estimated | bool | True if count is approximate (API unavailable) | Default: False |
| cache_creation_input_tokens | int | Tokens used to create cache | >= 0, default 0 |
| cache_read_input_tokens | int | Tokens read from cache | >= 0, default 0 |

### CostEstimate

Calculated USD cost for a TokenCount.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| input_cost | float | Cost of input tokens in USD | >= 0.0 |
| output_cost | float | Cost of output tokens in USD | >= 0.0 |
| cache_discount | float | Savings from prompt caching in USD | >= 0.0 |
| total_cost | float | input_cost + output_cost - cache_discount | >= 0.0 |
| model | str | Model used for pricing lookup | Must be in PRICING dict |

### TOONResponse

An MCP tool response serialized in TOON format.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| toon_data | str | TOON-serialized response string | Non-empty |
| json_token_count | int | Token count of equivalent JSON | >= 0 |
| toon_token_count | int | Token count of TOON version | >= 0 |
| savings_tokens | int | json_token_count - toon_token_count | >= 0 |
| savings_pct | float | Percentage tokens saved | 0.0 - 100.0 |
| fallback_used | bool | True if JSON fallback was used | Default: False |

### ToolUsageRecord

Per-tool tracking entry in the session ledger.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| tool_name | str | MCP tool identifier | Non-empty |
| call_count | int | Number of times tool was called | >= 1 |
| total_input_tokens | int | Cumulative input tokens | >= 0 |
| total_output_tokens | int | Cumulative output tokens | >= 0 |
| total_cost | float | Cumulative cost in USD | >= 0.0 |
| toon_savings_tokens | int | Cumulative TOON savings | >= 0 |
| avg_tokens_per_call | float | Computed: total / call_count | >= 0.0 |

### SessionLedger

Cumulative session-level accumulator.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| session_id | str | Unique session identifier | Auto-generated |
| started_at | datetime | Session start time | Auto-set |
| total_input_tokens | int | Session cumulative input tokens | >= 0 |
| total_output_tokens | int | Session cumulative output tokens | >= 0 |
| total_cost | float | Session cumulative cost in USD | >= 0.0 |
| total_toon_savings | int | Session cumulative TOON savings | >= 0 |
| tool_breakdown | dict[str, ToolUsageRecord] | Per-tool tracking | Keys are tool names |

### ModelPricing

Pricing configuration for a specific model.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| model_name | str | Model identifier | Non-empty |
| input_price_per_1m | float | USD per 1M input tokens | > 0.0 |
| output_price_per_1m | float | USD per 1M output tokens | > 0.0 |
| cache_discount_pct | float | Percentage discount for cached tokens | 0.0 - 100.0, default 90.0 |

## Relationships

```
SessionLedger 1──* ToolUsageRecord  (one session has many tool records)
TokenCount    1──1 CostEstimate     (each count has one cost calculation)
TokenCount    *──1 ModelPricing     (many counts reference one pricing model)
TOONResponse  *──1 ToolUsageRecord  (TOON savings accumulate into tool record)
```

## State Transitions

### SessionLedger Lifecycle

```
CREATED → ACTIVE → SUMMARIZED
```

- **CREATED**: Session ledger initialized, counters at zero
- **ACTIVE**: Accumulating token counts from tool calls
- **SUMMARIZED**: Session ended, final summary generated for GAIT log
