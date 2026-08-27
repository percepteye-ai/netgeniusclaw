"""PendingApprovalsIntent's live count (spec 111, US2)."""

import asyncio
import json

import pytest
import websockets

from bgp.federation.manager import FederationManager
from bgp.federation.service import FederationService
from bgp.federation.risk import RiskManager
from bgp.federation import certs


def _border(base):
    mgr = FederationManager(base_dir=str(base))
    svc = FederationService(local_as=65001, router_id="4.4.4.4", display_name="Border",
                            manager=mgr)
    svc.risk.set_role("border", risk_name="risk", enabled_stacks="in2n")
    return svc


class _FakePhone:
    def __init__(self, ws, handlers=None):
        self.ws = ws
        self.handlers = handlers or {}
        self._next_id = 0
        self._pending: dict = {}
        self._task = asyncio.create_task(self._loop())

    async def _loop(self):
        try:
            async for raw in self.ws:
                msg = json.loads(raw)
                if "method" in msg:
                    handler = self.handlers.get(msg["method"])
                    result = handler(msg.get("params") or {}) if handler else {}
                    if msg.get("id") is not None:
                        await self.ws.send(json.dumps(
                            {"jsonrpc": "2.0", "id": msg["id"], "result": result}))
                elif "id" in msg:
                    fut = self._pending.pop(msg["id"], None)
                    if fut and not fut.done():
                        fut.set_result(msg)
        except websockets.exceptions.ConnectionClosed:
            pass

    async def call(self, method, params, timeout=5.0):
        self._next_id += 1
        req_id = f"phone:{self._next_id}"
        fut = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut
        await self.ws.send(json.dumps(
            {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}))
        msg = await asyncio.wait_for(fut, timeout=timeout)
        if "error" in msg:
            raise RuntimeError(msg["error"])
        return msg.get("result", {})

    async def close(self):
        self._task.cancel()


async def _serve(border):
    async def on_conn(ws):
        await border.accept_edge_ws(ws)
    server = await websockets.serve(on_conn, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


async def _enroll(border, port, member_id="risk/phone1"):
    token = border.risk.issue_token(label="phone1")["token"]
    ws = await websockets.connect(f"ws://127.0.0.1:{port}")
    challenge = asyncio.get_event_loop().create_future()

    def _on_challenge(params):
        if not challenge.done():
            challenge.set_result(bytes.fromhex(params["nonce"]))
        return {}

    phone = _FakePhone(ws, handlers={
        "n2n/edge/challenge": _on_challenge,
        "n2n/edge/heartbeat": lambda p: {},
    })
    nonce = await asyncio.wait_for(challenge, timeout=5.0)
    cert_pem, key_pem = certs.create_self_signed(member_id)
    signature = RiskManager.sign_challenge(key_pem, nonce).hex()
    resp = await phone.call("in2n/enroll", {
        "token": token, "member_id": member_id, "cert_pem": cert_pem,
        "signature": signature, "runtime_kind": "mobile"})
    assert resp["pinned"] is True
    return phone


def _make_pending_approval(border, peer="risk/somepeer"):
    inv_id = border.manager._conn.execute(
        "INSERT INTO remote_invocation_record (direction, peer_identity, target_type, "
        "target_name, decision, outcome) VALUES ('inbound', ?, 'skill', 'reboot-router', "
        "'approval_required', 'pending')", (peer,)).lastrowid
    border.manager._conn.commit()
    appr = border.authz.create_approval(inv_id)
    return inv_id, appr["approval_id"]


def test_approvals_list_returns_the_live_count(tmp_path):
    """Closes US2/FR-006: n2n/edge/approvals_list returns a count matching
    Authorizer.pending_approvals() -- not a stale/cached value."""
    asyncio.run(_approvals_list_live_count(tmp_path))


async def _approvals_list_live_count(tmp_path):
    border = _border(tmp_path / "border")
    server, port = await _serve(border)
    try:
        phone = await _enroll(border, port)

        resp = await phone.call("n2n/edge/approvals_list", {})
        assert resp["count"] == 0

        _make_pending_approval(border, peer="risk/peer-a")
        _make_pending_approval(border, peer="risk/peer-b")

        resp = await phone.call("n2n/edge/approvals_list", {})
        assert resp["count"] == 2
        assert resp["count"] == len(border.authz.pending_approvals())

        await phone.close()
    finally:
        server.close()
    border.manager.close()


def test_approvals_list_count_changes_after_resolution(tmp_path):
    """The count must be live: resolving an approval must be reflected on
    the very next call, not require a fresh connection."""
    asyncio.run(_approvals_list_after_resolution(tmp_path))


async def _approvals_list_after_resolution(tmp_path):
    border = _border(tmp_path / "border")
    server, port = await _serve(border)
    try:
        phone = await _enroll(border, port)
        _, approval_id = _make_pending_approval(border)

        resp = await phone.call("n2n/edge/approvals_list", {})
        assert resp["count"] == 1

        border.authz.resolve_approval(approval_id, "approve", via="cli")

        resp = await phone.call("n2n/edge/approvals_list", {})
        assert resp["count"] == 0

        await phone.close()
    finally:
        server.close()
    border.manager.close()


def test_approvals_list_requires_authentication(tmp_path):
    """An unauthenticated channel (never completed in2n/enroll or in2n/hello)
    must be refused, matching every other edge method's auth gate."""
    asyncio.run(_approvals_list_requires_auth(tmp_path))


async def _approvals_list_requires_auth(tmp_path):
    border = _border(tmp_path / "border")
    server, port = await _serve(border)
    try:
        ws = await websockets.connect(f"ws://127.0.0.1:{port}")
        # The Border sends its own n2n/edge/challenge notification unprompted
        # as soon as the socket connects -- discard it, this test never
        # completes the handshake it starts.
        await asyncio.wait_for(ws.recv(), timeout=5.0)
        req_id = "unauth:1"
        await ws.send(json.dumps(
            {"jsonrpc": "2.0", "id": req_id, "method": "n2n/edge/approvals_list", "params": {}}))
        raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        msg = json.loads(raw)
        assert "error" in msg
        await ws.close()
    finally:
        server.close()
    border.manager.close()
