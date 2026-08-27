"""Tests for SessionLedger budget enforcement (spec 109)."""

import os
import sys

import pytest

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from netclaw_tokens import CostEstimate, TokenCount
from netclaw_tokens.budget_policy import BudgetPolicy
from netclaw_tokens.session_ledger import SessionLedger


class TestCostCapEnforcement:
    """US1: Session cost cap halts runaway spending."""

    def test_is_over_budget_false_below_cap(self):
        policy = BudgetPolicy(session_budget_usd=5.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 4.99
        assert ledger.is_over_budget() is False

    def test_is_over_budget_true_at_cap(self):
        policy = BudgetPolicy(session_budget_usd=5.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 5.0
        assert ledger.is_over_budget() is True

    def test_is_over_budget_true_above_cap(self):
        policy = BudgetPolicy(session_budget_usd=5.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 11.13  # The real incident amount
        assert ledger.is_over_budget() is True

    def test_check_budget_sets_halt_state_on_cost(self):
        policy = BudgetPolicy(session_budget_usd=2.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 2.50

        should_halt, reason = ledger.check_budget()
        assert should_halt is True
        assert reason == "cost_cap"
        assert ledger.budget_halted is True
        assert ledger.halt_reason == "cost_cap"

    def test_check_budget_returns_false_when_ok(self):
        policy = BudgetPolicy(session_budget_usd=10.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 1.0

        should_halt, reason = ledger.check_budget()
        assert should_halt is False
        assert reason is None
        assert ledger.budget_halted is False

    def test_check_budget_stays_halted_after_first_trip(self):
        policy = BudgetPolicy(session_budget_usd=2.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 3.0

        ledger.check_budget()
        # Second call still returns halted
        should_halt, reason = ledger.check_budget()
        assert should_halt is True
        assert reason == "cost_cap"

    def test_default_budget_is_sensible(self):
        ledger = SessionLedger()  # No explicit budget
        assert ledger.budget.session_budget_usd == 5.0


class TestOverrideBudget:
    """US1: Budget override/continuation."""

    def test_override_cost_cap_extends_ceiling(self):
        policy = BudgetPolicy(session_budget_usd=2.0, override_increment_usd=3.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 2.50
        ledger.check_budget()

        assert ledger.budget_halted is True
        assert ledger.halt_reason == "cost_cap"
        ledger.override_budget()

        assert ledger.budget_halted is False
        assert ledger.halt_reason is None
        assert ledger.budget.session_budget_usd == 5.0  # 2.0 + 3.0
        assert ledger.tool_calls_this_turn == 0  # Also resets tool counter

    def test_override_tool_limit_does_not_extend_dollar_cap(self):
        """Tool-limit continuation resets call counter without adding dollars."""
        policy = BudgetPolicy(session_budget_usd=10.0, max_tool_calls_per_turn=5)
        ledger = SessionLedger(budget=policy)
        for _ in range(5):
            ledger.record_tool_call()
        ledger.check_budget()

        assert ledger.halt_reason == "tool_limit"
        original_budget = ledger.budget.session_budget_usd

        ledger.override_budget()

        assert ledger.budget.session_budget_usd == original_budget  # Unchanged
        assert ledger.tool_calls_this_turn == 0  # Reset for next batch
        assert ledger.budget_halted is False

    def test_override_disabled_raises(self):
        policy = BudgetPolicy(session_budget_usd=2.0, allow_override=False)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 3.0
        ledger.check_budget()

        with pytest.raises(RuntimeError, match="override is disabled"):
            ledger.override_budget()

    def test_after_override_session_can_continue(self):
        policy = BudgetPolicy(session_budget_usd=2.0, override_increment_usd=2.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 2.50
        ledger.check_budget()
        ledger.override_budget()

        # Now budget is 4.0, cost is 2.50 — should be OK
        should_halt, reason = ledger.check_budget()
        assert should_halt is False


class TestToolCallLimit:
    """US2: Tool-call depth limit per user message."""

    def test_is_over_tool_limit_false_below(self):
        policy = BudgetPolicy(max_tool_calls_per_turn=15)
        ledger = SessionLedger(budget=policy)
        for _ in range(14):
            ledger.record_tool_call()
        assert ledger.is_over_tool_limit() is False

    def test_is_over_tool_limit_true_at_limit(self):
        policy = BudgetPolicy(max_tool_calls_per_turn=15)
        ledger = SessionLedger(budget=policy)
        for _ in range(15):
            ledger.record_tool_call()
        assert ledger.is_over_tool_limit() is True

    def test_new_turn_resets_counter(self):
        policy = BudgetPolicy(max_tool_calls_per_turn=5)
        ledger = SessionLedger(budget=policy)
        for _ in range(5):
            ledger.record_tool_call()
        assert ledger.is_over_tool_limit() is True

        ledger.new_turn()
        assert ledger.tool_calls_this_turn == 0
        assert ledger.is_over_tool_limit() is False

    def test_check_budget_catches_tool_limit(self):
        policy = BudgetPolicy(max_tool_calls_per_turn=3)
        ledger = SessionLedger(budget=policy)
        for _ in range(3):
            ledger.record_tool_call()

        should_halt, reason = ledger.check_budget()
        assert should_halt is True
        assert reason == "tool_limit"

    def test_cost_cap_takes_priority_over_tool_limit(self):
        """When both limits are exceeded, cost_cap is reported first."""
        policy = BudgetPolicy(session_budget_usd=1.0, max_tool_calls_per_turn=5)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 2.0
        for _ in range(5):
            ledger.record_tool_call()

        should_halt, reason = ledger.check_budget()
        assert should_halt is True
        assert reason == "cost_cap"  # Cost checked first


class TestHaltMessage:
    """US1: Formatted halt message."""

    def test_halt_message_includes_cost(self):
        policy = BudgetPolicy(session_budget_usd=5.0, override_increment_usd=2.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 5.50
        ledger.total_input_tokens = 500_000
        ledger.total_output_tokens = 10_000
        ledger.total_call_count = 25
        ledger.budget_halted = True
        ledger.halt_reason = "cost_cap"

        msg = ledger.get_halt_message()
        assert "$5.50" in msg
        assert "$5.00 cap" in msg
        assert "25 API calls" in msg
        assert "continue" in msg.lower()
        assert "$2.00" in msg  # Shows the override increment amount
        assert "What I accomplished" in msg  # Partial summary present

    def test_halt_message_tool_limit(self):
        policy = BudgetPolicy(max_tool_calls_per_turn=20)
        ledger = SessionLedger(budget=policy)
        ledger.tool_calls_this_turn = 20
        ledger.budget_halted = True
        ledger.halt_reason = "tool_limit"

        msg = ledger.get_halt_message()
        assert "20/20" in msg
        assert "Tool call limit" in msg
        assert "no additional cost cap" in msg.lower()  # Makes clear it's free to continue


class TestContextWarning:
    """US4: Context growth awareness."""

    def test_should_warn_below_threshold(self):
        policy = BudgetPolicy(context_warning_tokens=100_000)
        ledger = SessionLedger(budget=policy)
        assert ledger.should_warn_context(50_000) is False

    def test_should_warn_at_threshold(self):
        policy = BudgetPolicy(context_warning_tokens=100_000)
        ledger = SessionLedger(budget=policy)
        assert ledger.should_warn_context(100_000) is True

    def test_context_warning_message_includes_cost(self):
        ledger = SessionLedger()
        msg = ledger.get_context_warning(200_000, model="qwen/qwen3.5-4b")
        assert "200,000 tokens" in msg
        assert "$" in msg  # Should include cost estimate


class TestRecordIntegration:
    """Verify record() still works correctly with budget-extended ledger."""

    def test_record_accumulates_cost(self):
        ledger = SessionLedger()
        token_count = TokenCount(input_tokens=1000, output_tokens=500)
        cost = CostEstimate(total_cost=0.05)

        ledger.record("exec", token_count, cost)
        ledger.record("exec", token_count, cost)

        assert ledger.total_cost == 0.10
        assert ledger.total_call_count == 2

    def test_reset_clears_budget_state(self):
        policy = BudgetPolicy(session_budget_usd=1.0)
        ledger = SessionLedger(budget=policy)
        ledger.total_cost = 2.0
        ledger.tool_calls_this_turn = 10
        ledger.budget_halted = True
        ledger.halt_reason = "cost_cap"

        ledger.reset()

        assert ledger.total_cost == 0.0
        assert ledger.tool_calls_this_turn == 0
        assert ledger.budget_halted is False
        assert ledger.halt_reason is None
