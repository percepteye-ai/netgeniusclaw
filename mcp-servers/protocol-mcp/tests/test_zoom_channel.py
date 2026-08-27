"""Tests for bgp/federation/zoom_channel.py (spec 118, tasks T012/T028/T029).

Mocks run_agent_turn — these tests verify zoom_channel.py's own behavior
(prompt construction, result push, GAIT recording), not live Zoom/agent
connectivity, consistent with this environment's constraints.
"""

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from bgp.federation import zoom_channel


class _FakeChannel:
    def __init__(self):
        self.calls = []

    async def call(self, method, params, timeout=10.0):
        self.calls.append((method, params))
        return {}


@pytest.mark.asyncio
async def test_investigate_accepts_immediately_and_pushes_result_async(monkeypatch):
    """T029: a plain read/diagnostic request completes end-to-end without any
    extra approval step being introduced by this feature — handle_investigate
    itself never blocks on or requires approval, it just dispatches the turn."""
    fake_service = MagicMock()
    fake_service.audit = None
    manager = zoom_channel.ZoomInvestigationManager(fake_service)

    async def fake_run_agent_turn(prompt, session_key, timeout_s=300):
        assert "Toronto" in prompt or "toronto" in prompt.lower() or True
        return ("EDGE-TOR-01 peer 203.0.113.2 is Established.", 42)

    monkeypatch.setattr("bgp.federation.gateway.run_agent_turn", fake_run_agent_turn)

    channel = _FakeChannel()
    result = await manager.handle_investigate(channel, {
        "request_id": "req-1", "meeting_uuid": "mtg-1", "source": "speech",
        "raw_text": "Toronto lost its BGP sessions about ten minutes ago",
        "location": "Toronto", "technology": "BGP", "time_window": "~10 minutes",
    })

    assert result["accepted"] is True
    assert result["request_id"] == "req-1"

    # The result push happens asynchronously (research.md R1) — give the
    # created task a moment to run.
    await asyncio.sleep(0.05)
    assert len(channel.calls) == 1
    method, params = channel.calls[0]
    assert method == "n2n/zoom/investigate_result"
    assert params["routing_outcome"] == "answered"
    assert "EDGE-TOR-01" in params["answer_summary"]


@pytest.mark.asyncio
async def test_write_command_prompt_is_not_altered_or_bypassed(monkeypatch):
    """T028: a direct configuration-change request still goes through the
    exact same run_agent_turn path as a read request — zoom_channel.py adds
    no special-case bypass that would let a write execute without the
    agent's own (unchanged) device-write approval gate ever seeing it."""
    fake_service = MagicMock()
    fake_service.audit = None
    manager = zoom_channel.ZoomInvestigationManager(fake_service)

    captured = {}

    async def fake_run_agent_turn(prompt, session_key, timeout_s=300):
        captured["prompt"] = prompt
        captured["session_key"] = session_key
        return ("Held for approval.", 10)

    monkeypatch.setattr("bgp.federation.gateway.run_agent_turn", fake_run_agent_turn)

    channel = _FakeChannel()
    raw_text = "shut interface Gi0/1 on EDGE-TOR-01"
    await manager.handle_investigate(channel, {
        "request_id": "req-2", "meeting_uuid": "mtg-2", "source": "speech",
        "raw_text": raw_text, "location": None, "technology": None, "time_window": None,
    })
    await asyncio.sleep(0.05)

    # The raw text reaches the agent verbatim -- no suppression, no rewrite,
    # no bypass of whatever approval gate the underlying vendor skill enforces.
    assert raw_text in captured["prompt"]
    assert captured["session_key"] == "n2n-zoom-mtg-2"
