"""Budget enforcement policy for NetClaw sessions.

Provides configurable per-session cost ceilings, tool-call depth limits,
and per-interface model routing. Loads configuration from openclaw.json
with environment variable overrides.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger("netclaw_tokens.budget_policy")

__all__ = ["BudgetPolicy", "load_budget_policy", "resolve_session_config"]

# ---------------------------------------------------------------------------
# Interface detection patterns (from session key)
# ---------------------------------------------------------------------------
_INTERFACE_PATTERNS = [
    (re.compile(r"^agent:[^:]+:openai:"), "openai"),
    (re.compile(r"^agent:[^:]+:tui-"), "tui"),
    (re.compile(r"^agent:[^:]+:discord:"), "discord"),
    (re.compile(r"^agent:[^:]+:n2n"), "n2n"),
    (re.compile(r"^agent:[^:]+:hook:alert:"), "alert"),
    (re.compile(r"^agent:[^:]+:explicit:"), "explicit"),
]


@dataclass
class BudgetPolicy:
    """Per-session budget enforcement configuration.

    Attributes:
        session_budget_usd: Maximum USD cost before the session is halted.
        max_tool_calls_per_turn: Maximum tool invocations per user message
            before the agent pauses and asks whether to continue.
        context_warning_tokens: Emit a warning when session context exceeds
            this many tokens.
        context_auto_summarize: If True, old tool results are summarized
            when context exceeds the warning threshold (future enhancement).
        allow_override: Whether the operator can say "continue" after a halt.
        override_increment_usd: How much budget extends on each override.
        model: Optional model override for this interface/session.
        thinking_level: Optional thinking-level override (low/medium/high).
    """

    session_budget_usd: float = 5.0
    max_tool_calls_per_turn: int = 20
    context_warning_tokens: int = 100_000
    context_auto_summarize: bool = False
    allow_override: bool = True
    override_increment_usd: float = 2.0
    model: Optional[str] = None
    thinking_level: Optional[str] = None


def detect_interface_type(session_key: str) -> Optional[str]:
    """Detect the interface type from a session key string.

    Args:
        session_key: OpenClaw session key (e.g., "agent:main:openai:abc123")

    Returns:
        Interface type string or None if unrecognized.
    """
    for pattern, iface_type in _INTERFACE_PATTERNS:
        if pattern.match(session_key):
            return iface_type
    return None


def load_budget_policy(
    config: Dict,
    interface_type: Optional[str] = None,
) -> BudgetPolicy:
    """Load a BudgetPolicy from openclaw.json config with layered overrides.

    Resolution order (later wins):
    1. BudgetPolicy defaults (hardcoded)
    2. agents.defaults.budget (from config)
    3. interfaceDefaults.<type>.budget (if interface_type provided)
    4. Environment variable NETCLAW_SESSION_BUDGET_USD (cost cap only)

    Args:
        config: Parsed openclaw.json as a dict (or the agents.defaults subtree).
        interface_type: Detected interface type for per-interface overrides.

    Returns:
        Fully resolved BudgetPolicy.
    """
    policy = BudgetPolicy()

    # Layer 1: agents.defaults.budget
    agents_config = config.get("agents", config)
    defaults = agents_config.get("defaults", {})
    budget_config = defaults.get("budget", {})

    if budget_config:
        _apply_budget_dict(policy, budget_config)

    # Layer 2: interfaceDefaults.<type>
    if interface_type:
        iface_defaults = defaults.get("interfaceDefaults", {})
        iface_config = iface_defaults.get(interface_type, {})

        if iface_config:
            # Model/thinking routing
            if "model" in iface_config:
                policy.model = iface_config["model"]
            if "thinkingLevel" in iface_config:
                policy.thinking_level = iface_config["thinkingLevel"]

            # Per-interface budget overrides
            iface_budget = iface_config.get("budget", {})
            if iface_budget:
                _apply_budget_dict(policy, iface_budget)

    # Layer 3: Environment variable override (highest precedence for cost cap)
    env_budget = os.environ.get("NETCLAW_SESSION_BUDGET_USD", "")
    if env_budget:
        try:
            policy.session_budget_usd = float(env_budget)
        except (ValueError, TypeError):
            logger.warning(
                "NETCLAW_SESSION_BUDGET_USD='%s' is not a valid float; ignoring",
                env_budget,
            )

    return policy


def resolve_session_config(config: Dict, session_key: str) -> BudgetPolicy:
    """One-call function: detect interface from session key and load policy.

    This is the primary entry point for the gateway to get a fully resolved
    budget policy for a new session.

    Args:
        config: Parsed openclaw.json dict.
        session_key: Full session key (e.g., "agent:main:openai:abc123").

    Returns:
        BudgetPolicy with all overrides applied.
    """
    interface_type = detect_interface_type(session_key)
    return load_budget_policy(config, interface_type)


def _apply_budget_dict(policy: BudgetPolicy, budget_dict: Dict) -> None:
    """Apply a budget config dict onto an existing BudgetPolicy (mutates in place).

    Handles both camelCase (JSON config) and snake_case (Python) field names.
    """
    field_map = {
        "sessionBudgetUsd": "session_budget_usd",
        "session_budget_usd": "session_budget_usd",
        "maxToolCallsPerTurn": "max_tool_calls_per_turn",
        "max_tool_calls_per_turn": "max_tool_calls_per_turn",
        "contextWarningTokens": "context_warning_tokens",
        "context_warning_tokens": "context_warning_tokens",
        "contextAutoSummarize": "context_auto_summarize",
        "context_auto_summarize": "context_auto_summarize",
        "allowOverride": "allow_override",
        "allow_override": "allow_override",
        "overrideIncrementUsd": "override_increment_usd",
        "override_increment_usd": "override_increment_usd",
    }

    for json_key, attr_name in field_map.items():
        if json_key in budget_dict:
            value = budget_dict[json_key]
            # Type coercion for safety
            current = getattr(policy, attr_name)
            if isinstance(current, float):
                value = float(value)
            elif isinstance(current, int):
                value = int(value)
            elif isinstance(current, bool):
                value = bool(value)
            setattr(policy, attr_name, value)
