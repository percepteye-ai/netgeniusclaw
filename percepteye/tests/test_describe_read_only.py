"""The describe pass carries each server's read/write declaration.

`annotations.readOnlyHint` never reaches OpenClaw's `llm_input` hook -- by the
time tools are handed to a model they are in the provider's function-call shape,
which has no field for it. `describe_tools` already asks every server for
`tools/list` itself (that is why it exists: the hook reports 38 built-ins and
misses the 47 MCP tools that ARE this agent), so the declaration is read there,
on the response that already carries it.

Undeclared must stay undeclared. Downstream, a tool with no declaration is
treated as a possible write and kept out of the held-out yardstick; defaulting
it to False here would assert something about somebody's tool that nobody
checked.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from describe_tools import _ask_server, _read_only_of  # noqa: E402


class TestHint:
    def test_only_a_real_bool_is_a_declaration(self):
        assert _read_only_of({"annotations": {"readOnlyHint": True}}) == {"read_only": True}
        assert _read_only_of({"annotations": {"readOnlyHint": False}}) == {"read_only": False}
        for undeclared in ({}, {"annotations": {}},
                           {"annotations": {"readOnlyHint": None}},
                           {"annotations": {"readOnlyHint": "yes"}},
                           {"annotations": "not-a-dict"}):
            assert _read_only_of(undeclared) == {}, undeclared


class TestAgainstARealServer:
    def test_declarations_survive_tools_list(self):
        """Drive an actual stdio MCP server and read what comes back."""
        entry = {"command": sys.executable,
                 "args": [os.path.join(HERE, "fake_mcp_server.py")]}
        tools = _ask_server("srv", entry, timeout_s=20.0)
        got = {t["name"]: t.get("read_only", "UNDECLARED") for t in tools}
        assert got["srv__tool_ok"] is True
        assert got["srv__tool_error"] is False
        # The server said nothing about these, and neither do we.
        assert got["srv__tool_silent_fail"] == "UNDECLARED"
        assert got["srv__tool_no_verdict"] == "UNDECLARED"

    def test_the_key_is_absent_not_null_when_undeclared(self):
        entry = {"command": sys.executable,
                 "args": [os.path.join(HERE, "fake_mcp_server.py")]}
        tools = {t["name"]: t for t in _ask_server("srv", entry, timeout_s=20.0)}
        assert "read_only" not in tools["srv__tool_no_verdict"]
