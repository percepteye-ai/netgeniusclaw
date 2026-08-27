"""Tests for BudgetPolicy loading and resolution (spec 109)."""

import os
import sys

import pytest

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from netclaw_tokens.budget_policy import (
    BudgetPolicy,
    detect_interface_type,
    load_budget_policy,
    resolve_session_config,
)


class TestBudgetPolicyDefaults:
    """Verify default construction produces safe values."""

    def test_default_session_budget(self):
        policy = BudgetPolicy()
        assert policy.session_budget_usd == 5.0

    def test_default_tool_call_limit(self):
        policy = BudgetPolicy()
        assert policy.max_tool_calls_per_turn == 20

    def test_default_context_warning(self):
        policy = BudgetPolicy()
        assert policy.context_warning_tokens == 100_000

    def test_default_override_allowed(self):
        policy = BudgetPolicy()
        assert policy.allow_override is True

    def test_default_model_is_none(self):
        policy = BudgetPolicy()
        assert policy.model is None


class TestInterfaceDetection:
    """Verify session key → interface type mapping."""

    def test_openai_interface(self):
        assert detect_interface_type("agent:main:openai:abc-123") == "openai"

    def test_tui_interface(self):
        assert detect_interface_type("agent:main:tui-6861a019-21a7") == "tui"

    def test_discord_interface(self):
        assert detect_interface_type("agent:main:discord:channel:123") == "discord"

    def test_n2n_interface(self):
        assert detect_interface_type("agent:main:n2n") == "n2n"

    def test_alert_interface(self):
        assert detect_interface_type("agent:main:hook:alert:abc123") == "alert"

    def test_explicit_interface(self):
        assert detect_interface_type("agent:main:explicit:n2n-edge-risk") == "explicit"

    def test_unknown_returns_none(self):
        assert detect_interface_type("something:completely:different") is None


class TestLoadBudgetPolicy:
    """Verify config loading with layered overrides."""

    def test_empty_config_returns_defaults(self):
        policy = load_budget_policy({})
        assert policy.session_budget_usd == 5.0
        assert policy.max_tool_calls_per_turn == 20

    def test_agents_defaults_budget_override(self):
        config = {
            "agents": {
                "defaults": {
                    "budget": {
                        "sessionBudgetUsd": 10.0,
                        "maxToolCallsPerTurn": 30,
                    }
                }
            }
        }
        policy = load_budget_policy(config)
        assert policy.session_budget_usd == 10.0
        assert policy.max_tool_calls_per_turn == 30

    def test_interface_defaults_model_routing(self):
        config = {
            "agents": {
                "defaults": {
                    "interfaceDefaults": {
                        "openai": {
                            "model": "anthropic/claude-haiku-4-5",
                            "thinkingLevel": "medium",
                        }
                    }
                }
            }
        }
        policy = load_budget_policy(config, interface_type="openai")
        assert policy.model == "anthropic/claude-haiku-4-5"
        assert policy.thinking_level == "medium"

    def test_interface_budget_override(self):
        config = {
            "agents": {
                "defaults": {
                    "budget": {"sessionBudgetUsd": 10.0},
                    "interfaceDefaults": {
                        "n2n": {
                            "budget": {"sessionBudgetUsd": 2.0}
                        }
                    },
                }
            }
        }
        # Global default
        policy_global = load_budget_policy(config)
        assert policy_global.session_budget_usd == 10.0

        # N2N-specific override
        policy_n2n = load_budget_policy(config, interface_type="n2n")
        assert policy_n2n.session_budget_usd == 2.0

    def test_tui_with_no_interface_config_uses_defaults(self):
        config = {
            "agents": {
                "defaults": {
                    "budget": {"sessionBudgetUsd": 7.0},
                    "interfaceDefaults": {
                        "openai": {"model": "anthropic/claude-haiku-4-5"}
                    },
                }
            }
        }
        policy = load_budget_policy(config, interface_type="tui")
        assert policy.session_budget_usd == 7.0
        assert policy.model is None  # No TUI-specific model override

    def test_env_var_overrides_config(self, monkeypatch):
        config = {
            "agents": {
                "defaults": {
                    "budget": {"sessionBudgetUsd": 10.0}
                }
            }
        }
        monkeypatch.setenv("NETCLAW_SESSION_BUDGET_USD", "1.5")
        policy = load_budget_policy(config)
        assert policy.session_budget_usd == 1.5

    def test_invalid_env_var_ignored(self, monkeypatch):
        monkeypatch.setenv("NETCLAW_SESSION_BUDGET_USD", "not_a_number")
        policy = load_budget_policy({})
        assert policy.session_budget_usd == 5.0  # Falls back to default


class TestResolveSessionConfig:
    """Verify the one-call session config resolver."""

    def test_openai_session_gets_mobile_routing(self):
        config = {
            "agents": {
                "defaults": {
                    "interfaceDefaults": {
                        "openai": {
                            "model": "anthropic/claude-haiku-4-5",
                            "budget": {"sessionBudgetUsd": 2.0},
                        }
                    }
                }
            }
        }
        policy = resolve_session_config(config, "agent:main:openai:e5b7e8f1-uuid")
        assert policy.model == "anthropic/claude-haiku-4-5"
        assert policy.session_budget_usd == 2.0

    def test_unknown_session_key_uses_global_defaults(self):
        config = {
            "agents": {
                "defaults": {
                    "budget": {"sessionBudgetUsd": 5.0}
                }
            }
        }
        policy = resolve_session_config(config, "something:unknown:pattern")
        assert policy.session_budget_usd == 5.0
        assert policy.model is None
