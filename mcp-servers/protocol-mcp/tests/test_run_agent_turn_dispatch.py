"""Tests for run_agent_turn()'s dispatch mechanism (spec 116, User Story 1).

These encode the actual root-cause fix from specs/116-border-turn-latency/research.md:
the CLI dispatch path unconditionally sent `cleanupBundleMcpOnRunEnd: true`, which
tore down the gateway's session-scoped MCP runtime cache after every turn. The fix
routes through GatewayWsClient instead, which must never send that flag.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from bgp.federation import gateway

pytestmark = pytest.mark.asyncio


async def test_no_cleanup_flag_sent():
    """The single assertion that directly encodes research.md's Finding 2/3 fix:
    the RPC params built for the 'agent' method must never contain
    cleanupBundleMcpOnRunEnd, regardless of value."""
    fake_client = AsyncMock()
    fake_client.call.return_value = {"result": {"payloads": [{"text": "OK"}]}}

    with patch("bgp.federation.gateway_ws.get_gateway_ws_client", AsyncMock(return_value=fake_client)):
        await gateway.run_agent_turn("hi", session_key="test-session")

    assert fake_client.call.called
    method, params = fake_client.call.call_args.args[0], fake_client.call.call_args.args[1]
    assert method == "agent"
    assert "cleanupBundleMcpOnRunEnd" not in params


async def test_reply_extraction_from_ws_response():
    """The WS response payload's result.payloads[*].text shape must parse to the
    same (reply_text, tokens_used) shape the existing CLI-stdout path already
    returns for an equivalent JSON envelope -- proving contracts/run-agent-turn.md's
    'Reused unchanged' claim about the extraction logic."""
    payload = {
        "result": {
            "payloads": [{"text": "The Border is healthy."}],
            "meta": {"usage": {"total_tokens": 42}},
        }
    }
    reply, tokens = gateway._extract_reply_from_ws_payload(payload)
    assert reply == "The Border is healthy."
    assert tokens == 42

    # Equivalent CLI-stdout envelope must parse to the identical shape.
    stdout_equivalent = (
        '{"result": {"payloads": [{"text": "The Border is healthy."}], '
        '"meta": {"usage": {"total_tokens": 42}}}}'
    )
    stdout_reply, stdout_tokens = gateway._extract_reply(stdout_equivalent)
    assert stdout_reply == reply
    assert stdout_tokens == tokens


async def test_stall_and_timeout_semantics_preserved():
    """A call that doesn't respond within stall_after_s must still invoke
    on_stall; a call that never responds must still raise TimeoutError at
    timeout_s -- contracts/run-agent-turn.md's 'Timeout semantics unchanged'."""
    fake_client = AsyncMock()

    async def never_responds(method, params, timeout_s):
        await asyncio.sleep(timeout_s + 10)  # never actually completes in time

    fake_client.call.side_effect = never_responds

    stall_calls = []

    def on_stall(waited_s):
        stall_calls.append(waited_s)
        return 0  # do not extend further

    with patch("bgp.federation.gateway_ws.get_gateway_ws_client", AsyncMock(return_value=fake_client)):
        with pytest.raises(asyncio.TimeoutError):
            await gateway.run_agent_turn(
                "hi", session_key="test-session",
                timeout_s=1, stall_after_s=0.3, on_stall=on_stall,
            )

    assert stall_calls == [0.3]
