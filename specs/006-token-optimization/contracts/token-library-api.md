# Contract: netclaw_tokens Library API

**Feature**: 006-token-optimization
**Date**: 2026-03-26

## Module: counter.py

```python
def count_tokens(text: str, model: str = "claude-opus-4-6") -> TokenCount:
    """
    Count tokens using Anthropic API with local fallback.

    Args:
        text: The text to count tokens for.
        model: The model identifier for tokenizer selection.

    Returns:
        TokenCount with input_tokens populated.
        If API unavailable, estimated=True and uses len(text)/4.

    Raises:
        Never raises — always returns a result (exact or estimated).
    """

def count_message_tokens(
    messages: list[dict],
    model: str = "claude-opus-4-6",
    system: str | None = None
) -> TokenCount:
    """
    Count tokens for a full message array (input context).

    Args:
        messages: List of message dicts with role/content.
        model: Model identifier.
        system: Optional system prompt.

    Returns:
        TokenCount with input_tokens from API or estimation.
    """
```

## Module: toon_serializer.py

```python
def serialize_response(data: Any) -> TOONResponse:
    """
    Serialize data to TOON format with JSON fallback.

    Args:
        data: Any JSON-serializable data structure.

    Returns:
        TOONResponse with toon_data (TOON string or JSON string),
        token counts for both formats, savings calculation,
        and fallback_used flag.

    Behavior:
        - If data is bytes or non-UTF-8: returns JSON, fallback_used=True
        - If toon.dumps() fails: returns JSON, fallback_used=True, logs warning
        - Otherwise: returns TOON, fallback_used=False
    """
```

## Module: cost_calculator.py

```python
def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-opus-4-6",
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0
) -> CostEstimate:
    """
    Calculate USD cost for token usage.

    Args:
        input_tokens: Number of input tokens (non-cached).
        output_tokens: Number of output tokens.
        model: Model identifier for pricing lookup.
        cache_creation_tokens: Tokens used to create cache entry.
        cache_read_tokens: Tokens read from cache (90% discount).

    Returns:
        CostEstimate with itemized costs.

    Environment:
        NETCLAW_TOKEN_PRICING_OVERRIDE: Optional JSON string overriding
        default pricing. Format: {"model_name": {"input": float, "output": float}}
    """

def get_pricing(model: str) -> ModelPricing:
    """Return pricing for the given model, with env var override support."""
```

## Module: session_ledger.py

```python
class SessionLedger:
    """Thread-safe session-level token accumulator."""

    def record(
        self,
        tool_name: str,
        token_count: TokenCount,
        cost: CostEstimate,
        toon_savings: int = 0
    ) -> None:
        """Record a tool call's token usage. Thread-safe."""

    def get_summary(self) -> dict:
        """
        Return session totals:
        {
            "total_input_tokens": int,
            "total_output_tokens": int,
            "total_tokens": int,
            "total_cost_usd": float,
            "total_toon_savings": int,
            "tool_count": int,
            "call_count": int
        }
        """

    def get_per_tool_breakdown(self) -> list[dict]:
        """
        Return ranked list of tool usage records, sorted by total tokens desc.
        Each entry: {tool_name, call_count, input_tokens, output_tokens,
                     total_tokens, cost, toon_savings, avg_tokens_per_call}
        """

    def get_gait_summary(self) -> dict:
        """Return summary formatted for GAIT session log inclusion."""

    def reset(self) -> None:
        """Reset all counters. Used at session start."""
```

## Module: footer.py

```python
def format_footer(
    token_count: TokenCount,
    cost: CostEstimate,
    toon_savings: int = 0,
    session_summary: dict | None = None
) -> str:
    """
    Format the mandatory token footer for display.

    Returns string like:
    📊 Tokens: 1,245 in / 382 out / 1,627 total | Cost: $0.0158 | TOON saved: 412 tokens ($0.0041) | Session: 15,832 tokens ($0.14)

    Args:
        token_count: Current interaction's token count.
        cost: Current interaction's cost estimate.
        toon_savings: Tokens saved by TOON in this interaction.
        session_summary: Optional session totals to append.
    """
```

## Integration Contract: MCP Server Update

Each bundled MCP server MUST add the following to its response path:

```python
from netclaw_tokens.toon_serializer import serialize_response

# In each tool function, before returning:
result = serialize_response(original_data)
return result.toon_data  # Returns TOON string (or JSON on fallback)
```

This is a non-breaking change: the return type remains `str`, but the content format changes from JSON to TOON (which Claude can parse equivalently).
