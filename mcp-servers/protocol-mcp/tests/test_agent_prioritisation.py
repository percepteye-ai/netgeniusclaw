"""Tests for run_agent_turn()'s concurrency/prioritisation behavior (spec 116,
User Story 3, FR-014/FR-015).

research.md's "T032 finding": there is no gateway-native priority lane, and no
NetClaw-authored scheduled/background call site to prioritize an interactive
request against today. FR-014/FR-015 are satisfied by User Story 1's fix
(no forced teardown -> warm turns are fast) plus the gateway's existing,
already-unbounded cross-session concurrency (agents.defaults.maxConcurrent is
unset). These tests guard that existing-and-sufficient behavior, not a new
scheduling mechanism.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, patch

import pytest
import websockets

from bgp.federation import gateway
from bgp.federation.gateway_ws import GatewayWsClient

pytestmark = pytest.mark.asyncio


async def test_no_overhead_when_idle():
    """FR-015: with no competing work, an interactive call must not carry any
    measurable added latency versus the bare dispatch cost. Regression guard
    for User Story 1's fix (T016) -- not a new mechanism."""
    fake_client = AsyncMock()
    fake_client.call.return_value = {"result": {"payloads": [{"text": "OK"}]}}

    with patch("bgp.federation.gateway_ws.get_gateway_ws_client", AsyncMock(return_value=fake_client)):
        t0 = time.monotonic()
        await gateway.run_agent_turn("hi", session_key="idle-test")
        elapsed = time.monotonic() - t0

    # No prioritisation machinery exists to add overhead; this call should be
    # bounded by the mock's near-instant return, not by any queueing logic.
    assert elapsed < 1.0


async def test_concurrent_sessions_do_not_serialize():
    """Two different session keys dispatched through the SAME GatewayWsClient
    must not serialize on each other -- proving the client's request-id
    multiplexing doesn't itself introduce contention, regardless of what
    background work either session's turn happens to represent. Mirrors the
    live verification already performed manually against the real gateway
    (research.md T021: two session keys completed in ~33s total, not ~66s)."""

    call_delay_s = 0.3

    async def handler(ws):
        await ws.send(json.dumps({
            "type": "event", "event": "connect.challenge",
            "payload": {"nonce": "test-nonce", "ts": 0},
        }))

        async def respond_to_agent_call(frame):
            # Simulate a slow turn without blocking the read loop below from
            # picking up the SECOND concurrent request while this one sleeps
            # -- a real gateway handles multiple in-flight agent turns
            # concurrently, not one-at-a-time per connection.
            await asyncio.sleep(call_delay_s)
            await ws.send(json.dumps({
                "type": "res", "id": frame["id"], "ok": True,
                "payload": {"result": {"payloads": [{"text": "OK"}]}},
            }))

        async for raw in ws:
            frame = json.loads(raw)
            if frame["method"] == "connect":
                await ws.send(json.dumps({
                    "type": "res", "id": frame["id"], "ok": True, "payload": {},
                }))
                continue
            if frame["method"] == "agent":
                asyncio.ensure_future(respond_to_agent_call(frame))

    async with websockets.serve(handler, "127.0.0.1", 0) as server:
        port = server.sockets[0].getsockname()[1]
        client = GatewayWsClient(f"ws://127.0.0.1:{port}", "test-token")

        t0 = time.monotonic()
        results = await asyncio.gather(
            client.call("agent", {"message": "a"}, timeout_s=5),
            client.call("agent", {"message": "b"}, timeout_s=5),
        )
        elapsed = time.monotonic() - t0

        assert all(r["result"]["payloads"][0]["text"] == "OK" for r in results)
        # If calls serialized, elapsed would be ~2 * call_delay_s. Assert it's
        # much closer to a single call_delay_s (allow generous slack for CI).
        assert elapsed < call_delay_s * 1.8

        await client.close()
