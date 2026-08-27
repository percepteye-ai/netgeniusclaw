"""Cumulative session-level token tracking with per-tool breakdown and budget enforcement.

Thread-safe accumulator that tracks token usage across all tool calls
in a session, with per-tool granularity for cost optimization analysis.
Includes enforcement hooks for cost ceilings and tool-call depth limits.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from . import CostEstimate, TokenCount, ToolUsageRecord
from .budget_policy import BudgetPolicy

__all__ = ["SessionLedger"]


class SessionLedger:
    """Thread-safe session-level token accumulator with budget enforcement.

    The ledger tracks cumulative costs and provides enforcement methods that
    the gateway checks before each model API call. When a budget is exceeded,
    the ledger signals a halt — it's the caller's responsibility to act on it.
    """

    def __init__(self, budget: Optional[BudgetPolicy] = None) -> None:
        self._lock = threading.Lock()
        self.session_id: str = str(uuid.uuid4())
        self.started_at: datetime = datetime.now(timezone.utc)
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cost: float = 0.0
        self.total_gcf_savings: int = 0
        self.total_call_count: int = 0
        self.tool_breakdown: Dict[str, ToolUsageRecord] = {}

        # Budget enforcement (new in spec 109)
        self.budget: BudgetPolicy = budget if budget is not None else BudgetPolicy()
        self.tool_calls_this_turn: int = 0
        self.budget_halted: bool = False
        self.halt_reason: Optional[str] = None
        self.interface_type: Optional[str] = None

    def record(
        self,
        tool_name: str,
        token_count: TokenCount,
        cost: CostEstimate,
        gcf_savings: int = 0,
    ) -> None:
        """Record a tool call's token usage. Thread-safe.

        Args:
            tool_name: MCP tool identifier.
            token_count: Token count for this call.
            cost: Cost estimate for this call.
            gcf_savings: Tokens saved by GCF serialization.
        """
        with self._lock:
            self.total_input_tokens += token_count.input_tokens
            self.total_output_tokens += token_count.output_tokens
            self.total_cost += cost.total_cost
            self.total_gcf_savings += gcf_savings
            self.total_call_count += 1

            if tool_name not in self.tool_breakdown:
                self.tool_breakdown[tool_name] = ToolUsageRecord(
                    tool_name=tool_name
                )

            record = self.tool_breakdown[tool_name]
            record.call_count += 1
            record.total_input_tokens += token_count.input_tokens
            record.total_output_tokens += token_count.output_tokens
            record.total_cost += cost.total_cost
            record.gcf_savings_tokens += gcf_savings

    # ------------------------------------------------------------------
    # Budget enforcement methods (spec 109)
    # ------------------------------------------------------------------

    def new_turn(self) -> None:
        """Reset per-turn counters. Call this on each new user message."""
        with self._lock:
            self.tool_calls_this_turn = 0

    def record_tool_call(self) -> None:
        """Increment the per-turn tool call counter. Thread-safe."""
        with self._lock:
            self.tool_calls_this_turn += 1

    def is_over_budget(self) -> bool:
        """Check if cumulative session cost exceeds the configured ceiling.

        Returns:
            True if total_cost >= session_budget_usd.
        """
        with self._lock:
            return self.total_cost >= self.budget.session_budget_usd

    def is_over_tool_limit(self) -> bool:
        """Check if tool calls this turn exceed the configured limit.

        Returns:
            True if tool_calls_this_turn >= max_tool_calls_per_turn.
        """
        with self._lock:
            return self.tool_calls_this_turn >= self.budget.max_tool_calls_per_turn

    def check_budget(self) -> Tuple[bool, Optional[str]]:
        """Check all budget constraints and set halt state if exceeded.

        This is the primary method the gateway should call before each
        model API request or tool invocation.

        Returns:
            Tuple of (should_halt, reason). reason is None if not halting,
            "cost_cap" if cost exceeded, "tool_limit" if tool depth exceeded.
        """
        with self._lock:
            if self.budget_halted:
                return (True, self.halt_reason)

            if self.total_cost >= self.budget.session_budget_usd:
                self.budget_halted = True
                self.halt_reason = "cost_cap"
                return (True, "cost_cap")

            if self.tool_calls_this_turn >= self.budget.max_tool_calls_per_turn:
                self.budget_halted = True
                self.halt_reason = "tool_limit"
                return (True, "tool_limit")

            return (False, None)

    def should_warn_context(self, context_tokens: int) -> bool:
        """Check if context size warrants a warning.

        Args:
            context_tokens: Current total context token count.

        Returns:
            True if context exceeds the configured warning threshold.
        """
        return context_tokens >= self.budget.context_warning_tokens

    def override_budget(self) -> None:
        """Extend the budget ceiling and clear the halt state.

        Called when the operator explicitly requests continuation.

        Behavior:
        - If halt_reason is "cost_cap": extends session_budget_usd by
          override_increment_usd AND resets tool_calls_this_turn.
        - If halt_reason is "tool_limit": resets tool_calls_this_turn only
          (allows another batch of N tool calls without extending the dollar cap).

        This distinction prevents "continue" from being ambiguous — tool-limit
        continuation is free (just more calls within existing budget), while
        cost-cap continuation explicitly adds more dollars.

        Raises:
            RuntimeError: If allow_override is False in the policy.
        """
        with self._lock:
            if not self.budget.allow_override:
                raise RuntimeError(
                    "Budget override is disabled for this session policy"
                )
            if self.halt_reason == "cost_cap":
                self.budget.session_budget_usd += self.budget.override_increment_usd
            # Both halt types reset the tool counter (allow another batch)
            self.tool_calls_this_turn = 0
            self.budget_halted = False
            self.halt_reason = None

    def get_halt_message(self) -> str:
        """Format a user-facing budget-exceeded message.

        Always includes a partial summary of what was accomplished before the
        halt — the operator already paid for this work, so they should get value
        from it even when the session stops.

        Returns:
            Formatted string with cost breakdown, top tools, and
            continuation instructions.
        """
        with self._lock:
            lines = []

            if self.halt_reason == "cost_cap":
                lines.append(
                    f"⚠️ Session budget reached "
                    f"(${self.total_cost:.2f} / "
                    f"${self.budget.session_budget_usd:.2f} cap)"
                )
            elif self.halt_reason == "tool_limit":
                lines.append(
                    f"⚠️ Tool call limit reached "
                    f"({self.tool_calls_this_turn}/"
                    f"{self.budget.max_tool_calls_per_turn} this turn)"
                )
            else:
                lines.append("⚠️ Session budget check triggered")

            lines.append("")
            lines.append("What I accomplished before stopping:")
            lines.append(
                f"  • {self.total_call_count} API calls, "
                f"{self.total_input_tokens:,} input tokens, "
                f"{self.total_output_tokens:,} output tokens"
            )
            lines.append(f"  • Total session cost: ${self.total_cost:.2f}")

            # Top 5 tools by cost — shows WHERE the money went
            if self.tool_breakdown:
                sorted_tools = sorted(
                    self.tool_breakdown.values(),
                    key=lambda r: r.total_cost,
                    reverse=True,
                )[:5]
                tool_summary = ", ".join(
                    f"{t.tool_name} ({t.call_count} calls, ${t.total_cost:.2f})"
                    for t in sorted_tools
                    if t.total_cost > 0
                )
                if tool_summary:
                    lines.append(f"  • Tools used: {tool_summary}")

            # Duration
            elapsed = datetime.now(timezone.utc) - self.started_at
            minutes = int(elapsed.total_seconds() / 60)
            if minutes > 0:
                lines.append(f"  • Session duration: {minutes} minutes")

            lines.append("")

            # Continuation instructions — different for each halt type
            if self.halt_reason == "tool_limit":
                lines.append(
                    'Say "continue" to allow another '
                    f"{self.budget.max_tool_calls_per_turn} tool calls "
                    f"(no additional cost cap increase)."
                )
            elif self.halt_reason == "cost_cap" and self.budget.allow_override:
                lines.append(
                    f'Say "continue" to add '
                    f"${self.budget.override_increment_usd:.2f} to the budget "
                    f"and resume."
                )

            lines.append("Or start a new session to reset from scratch.")

            return "\n".join(lines)

    def get_context_warning(self, context_tokens: int, model: str = "") -> str:
        """Format a context-size warning message.

        Args:
            context_tokens: Current context size in tokens.
            model: Current model name (for cost-per-turn estimate).

        Returns:
            Formatted warning string.
        """
        from .cost_calculator import get_pricing

        pricing = get_pricing(model) if model else None
        cost_per_turn = ""
        if pricing:
            # Approximate cost for one turn at current context size
            input_cost = (context_tokens / 1_000_000) * pricing.input_price_per_1m
            cost_per_turn = f" (~${input_cost:.2f} per additional turn)"

        return (
            f"⚠️ Context size: {context_tokens:,} tokens{cost_per_turn}. "
            f"Consider starting a new session to reduce costs."
        )

    # ------------------------------------------------------------------
    # Existing reporting methods (unchanged)
    # ------------------------------------------------------------------

    def get_summary(self) -> dict:
        """Return session totals as a dictionary.

        Returns:
            Dict with total_input_tokens, total_output_tokens, total_tokens,
            total_cost_usd, total_gcf_savings, tool_count, call_count,
            budget_halted, halt_reason.
        """
        with self._lock:
            return {
                "session_id": self.session_id,
                "started_at": self.started_at.isoformat(),
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_tokens": self.total_input_tokens + self.total_output_tokens,
                "total_cost_usd": round(self.total_cost, 6),
                "total_gcf_savings": self.total_gcf_savings,
                "tool_count": len(self.tool_breakdown),
                "call_count": self.total_call_count,
                "budget_halted": self.budget_halted,
                "halt_reason": self.halt_reason,
            }

    def get_per_tool_breakdown(self) -> List[dict]:
        """Return ranked list of tool usage records, sorted by total tokens desc.

        Each entry contains: tool_name, call_count, input_tokens, output_tokens,
        total_tokens, cost, gcf_savings, avg_tokens_per_call.
        """
        with self._lock:
            records = []
            for record in self.tool_breakdown.values():
                records.append({
                    "tool_name": record.tool_name,
                    "call_count": record.call_count,
                    "input_tokens": record.total_input_tokens,
                    "output_tokens": record.total_output_tokens,
                    "total_tokens": record.total_tokens,
                    "cost": round(record.total_cost, 6),
                    "gcf_savings": record.gcf_savings_tokens,
                    "avg_tokens_per_call": round(record.avg_tokens_per_call, 1),
                })

            # Sort by total tokens descending
            records.sort(key=lambda r: r["total_tokens"], reverse=True)
            return records

    def get_gait_summary(self) -> dict:
        """Return summary formatted for GAIT session log inclusion.

        Includes session totals and per-tool breakdown for audit trail.
        """
        summary = self.get_summary()
        summary["per_tool_breakdown"] = self.get_per_tool_breakdown()
        return summary

    def reset(self) -> None:
        """Reset all counters. Used at session start."""
        with self._lock:
            self.session_id = str(uuid.uuid4())
            self.started_at = datetime.now(timezone.utc)
            self.total_input_tokens = 0
            self.total_output_tokens = 0
            self.total_cost = 0.0
            self.total_gcf_savings = 0
            self.total_call_count = 0
            self.tool_breakdown.clear()
            self.tool_calls_this_turn = 0
            self.budget_halted = False
            self.halt_reason = None
