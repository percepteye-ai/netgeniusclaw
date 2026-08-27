"""Border-side Zoom channel (spec 118, research.md R1): a loopback-only,
restricted-method channel between the `zoom-rtms-mcp` MCP server and this
federation daemon, modeled on edge.py's EdgeChannel/EDGE_METHODS pattern
(feature 066) but scoped down — zoom-rtms-mcp runs on the SAME host as this
daemon (not a remote, independently-enrolled device), so none of EdgeChannel's
remote-enrollment/pinned-key trust machinery applies (research.md R1
"Alternatives considered"). Binds 127.0.0.1 only; a shared local secret
(N2N_ZOOM_CHANNEL_SECRET) gates the handshake for defense-in-depth even though
the socket itself never leaves the host.

Framing: 4-byte big-endian length prefix + UTF-8 JSON-RPC 2.0 payload — the
same shape as channel.py's NCFED framing, minus the mesh-discrimination magic
bytes and multi-frame continuation (not needed for this small, local surface).

Contract: specs/118-zoom-meeting-intelligence/contracts/zoom-channel-internal.md
"""

import asyncio
import json
import logging
import os
import struct
import time
import uuid
from typing import Awaitable, Callable, Optional

logger = logging.getLogger("n2n.zoom")

ERR_METHOD_NOT_FOUND = -32601
ERR_NOT_TRUSTED = -32023
ERR_EXECUTION_TIMEOUT = -32006

_MAX_FRAME = 1 * 1024 * 1024  # 1 MB — generous for this feature's message sizes

# The complete set of methods this channel will ever dispatch
# (contracts/zoom-channel-internal.md) — mirrors EDGE_METHODS' explicit-
# allowlist shape (feature 066 precedent).
ZOOM_METHODS = (
    "n2n/zoom/hello",              # handshake: shared-secret possession proof
    "n2n/zoom/investigate",        # zoom-rtms-mcp -> Border, request
    "n2n/zoom/investigate_result",  # Border -> zoom-rtms-mcp, push (best-effort)
    "n2n/zoom/session_closed",     # zoom-rtms-mcp -> Border, notify (fire-and-forget)
)

_PRE_TRUST_METHODS = ("n2n/zoom/hello",)

Handler = Callable[["ZoomChannel", dict], Awaitable[Optional[dict]]]


class RpcError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


async def _read_frame(reader: asyncio.StreamReader) -> Optional[bytes]:
    header = await reader.readexactly(4)
    (length,) = struct.unpack("!I", header)
    if length > _MAX_FRAME:
        raise RpcError(-32000, f"frame too large ({length} bytes)")
    return await reader.readexactly(length)


async def _write_frame(writer: asyncio.StreamWriter, payload: bytes):
    writer.write(struct.pack("!I", len(payload)) + payload)
    await writer.drain()


class ZoomChannel:
    """One TCP connection from the local zoom-rtms-mcp process."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
                 handlers: dict = None):
        self.reader = reader
        self.writer = writer
        self.trusted = False
        self._next_id = 0
        self._pending: dict = {}
        self._closed = False
        self._read_task: Optional[asyncio.Task] = None
        self.handlers: dict = {k: v for k, v in dict(handlers or {}).items()
                                if k in ZOOM_METHODS}

    def register(self, method: str, handler: Handler):
        if method not in ZOOM_METHODS:
            raise ValueError(f"{method} is not a zoom-channel method")
        self.handlers[method] = handler

    async def start(self):
        self._read_task = asyncio.create_task(self._read_loop())

    async def close(self):
        if self._closed:
            return
        self._closed = True
        if self._read_task:
            self._read_task.cancel()
        try:
            self.writer.close()
        except Exception:
            pass
        for _, fut in list(self._pending.items()):
            if not fut.done():
                fut.cancel()
        self._pending.clear()

    async def _read_loop(self):
        try:
            while True:
                raw = await _read_frame(self.reader)
                if raw is None:
                    break
                await self._dispatch(raw)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.info("Zoom channel closed: %s", e)
        finally:
            await self.close()

    async def _send(self, message: dict):
        await _write_frame(self.writer, json.dumps(message, separators=(",", ":")).encode())

    async def _dispatch(self, raw: bytes):
        try:
            msg = json.loads(raw)
        except Exception as e:
            logger.warning("Bad JSON on zoom channel: %s", e)
            return
        if "method" in msg:
            await self._handle_request(msg)
        elif "id" in msg:
            fut = self._pending.pop(msg["id"], None)
            if fut and not fut.done():
                fut.set_result(msg)

    async def _handle_request(self, msg: dict):
        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "n2n/zoom/hello":
            secret = os.environ.get("N2N_ZOOM_CHANNEL_SECRET", "")
            self.trusted = bool(secret) and params.get("secret") == secret
            if req_id is not None:
                await self._send({"jsonrpc": "2.0", "id": req_id,
                                   "result": {"trusted": self.trusted}})
            return
        if not self.trusted:
            if req_id is not None:
                await self._send(self._err(req_id, ERR_NOT_TRUSTED,
                                            "zoom channel not authenticated"))
            return
        handler = self.handlers.get(method)
        if not handler:
            if req_id is not None:
                await self._send(self._err(req_id, ERR_METHOD_NOT_FOUND,
                                            f"unknown method {method}"))
            return
        try:
            result = await handler(self, params)
            if req_id is not None:
                await self._send({"jsonrpc": "2.0", "id": req_id, "result": result or {}})
        except RpcError as e:
            if req_id is not None:
                await self._send(self._err(req_id, e.code, e.message))
        except Exception as e:
            logger.error("Zoom handler %s failed: %s", method, e)
            if req_id is not None:
                await self._send(self._err(req_id, -32000, str(e)))

    def _err(self, req_id, code, message):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    async def call(self, method: str, params: dict, timeout: float = 30.0) -> dict:
        self._next_id += 1
        req_id = f"border-zoom:{self._next_id}"
        fut = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut
        await self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        try:
            resp = await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise RpcError(ERR_EXECUTION_TIMEOUT, f"{method} timed out")
        if "error" in resp:
            raise RpcError(resp["error"]["code"], resp["error"]["message"])
        return resp.get("result", {})


# ---------------------------------------------------------------------------
# Investigation handlers (US1/US4) — see contracts/zoom-channel-internal.md
# ---------------------------------------------------------------------------

def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class ZoomInvestigationManager:
    """Owns the `n2n/zoom/investigate` handler: constructs a prompt from the
    extractor's already-classified fields, runs one autonomous agent turn
    (mirroring chat.py's `_ask_gateway` pattern — an inbound external event
    triggering `run_agent_turn` on this daemon's own initiative), records an
    InvestigationRequest, and emits it to GAIT. Pushes the result back over
    the same channel via `n2n/zoom/investigate_result` (best-effort, mirrors
    `n2n/edge/task_progress`)."""

    def __init__(self, service):
        self.service = service
        self.audit = getattr(service, "audit", None)
        # request_id -> the ZoomChannel that submitted it, so the async result
        # push (research.md R1) reaches the right connection.
        self._channels_by_request: dict[str, ZoomChannel] = {}

    async def handle_investigate(self, channel: ZoomChannel, params: dict) -> dict:
        request_id = params.get("request_id") or str(uuid.uuid4())
        meeting_uuid = params.get("meeting_uuid", "")
        session_key = f"n2n-zoom-{meeting_uuid}"
        self._channels_by_request[request_id] = channel

        prompt = self._build_prompt(params)

        asyncio.create_task(self._run_investigation(request_id, meeting_uuid, session_key,
                                                      params, prompt, channel))
        return {"accepted": True, "request_id": request_id}

    def _build_prompt(self, params: dict) -> str:
        parts = ["[A NetClaw Zoom meeting participant just asked this — investigate and answer "
                 "with evidence, do not fabricate]", params.get("raw_text", "")]
        extra = []
        if params.get("location"):
            extra.append(f"location: {params['location']}")
        if params.get("technology"):
            extra.append(f"technology: {params['technology']}")
        if params.get("time_window"):
            extra.append(f"time window: {params['time_window']}")
        if extra:
            parts.append("(" + ", ".join(extra) + ")")
        return "\n".join(parts)

    async def _run_investigation(self, request_id, meeting_uuid, session_key, params,
                                  prompt, channel: ZoomChannel):
        from .gateway import run_agent_turn

        # Immediate acknowledgment, before the real agent turn even starts.
        # run_agent_turn can take 1-3 minutes (multiple tool-call round trips
        # through the full MCP server set) — confirmed live 2026-08-19, this
        # was the actual reason every prior test looked like nothing happened:
        # the meeting/panel connection was gone before the real answer was
        # ever ready to push. Reuses the exact same push mechanism as the
        # final result (same channel, same method) — panel.js already just
        # overwrites the result text on the next push, no client change needed.
        try:
            await channel.call("n2n/zoom/investigate_result", {
                "request_id": request_id,
                "routing_outcome": "in_progress",
                "answer_summary": "Looking into it — this can take a minute or two…",
                "evidence_refs": [],
                "write_action_detected": False,
                "approval_ref": None,
            }, timeout=10.0)
        except Exception as e:
            logger.info("Could not push interim ack for %s (best-effort): %s", request_id, e)

        # KNOWN GAP (honest limitation, not a placeholder pretending to work):
        # device-write approval (Constitution Principles I-III: ServiceNow
        # CR-gated changes) happens INSIDE the agent turn itself, at whichever
        # vendor MCP tool the agent decides to call — the same way it already
        # works for every other channel (CLI, chat, mobile, voice). Unlike
        # NCFED's own Authorizer.create_approval()/resolve_approval() (which
        # governs peer-to-peer task-delegation grants, a different axis per
        # research.md R7 and not on this local, non-peer call path at all —
        # chat.py's `_ask_gateway` bypasses it for the same reason), there is
        # no signal surfaced back to run_agent_turn's caller today indicating
        # "this turn is holding on a pending device-write approval" versus
        # "still thinking." write_action_detected/approval_ref are therefore
        # always False/None here until a real signal exists to set them from
        # — the fields exist in InvestigationRequest (data-model.md) so the
        # audit correlation (FR-013) is ready the moment such a signal is
        # added, but nothing here should be read as already wired end-to-end.
        write_action_detected = False
        approval_ref = None
        try:
            reply, tokens = await run_agent_turn(prompt, session_key=session_key, timeout_s=300)
            routing_outcome = "answered"
            answer_summary = reply
            evidence_refs = []
        except Exception as e:
            logger.error("Zoom investigate %s failed: %s", request_id, e)
            routing_outcome = "failed_no_tooling"
            answer_summary = None
            evidence_refs = []

        if self.audit:
            try:
                self.audit.record(
                    direction="inbound", peer_identity="zoom-meeting", target_type="zoom_investigate",
                    target_name=meeting_uuid, request_id=request_id, decision="allowlisted",
                    outcome=routing_outcome, channel_kind="zoom")
            except Exception as e:
                logger.warning("GAIT record failed for zoom investigate %s: %s", request_id, e)

        result_params = {
            "request_id": request_id,
            "routing_outcome": routing_outcome,
            "answer_summary": answer_summary,
            "evidence_refs": evidence_refs,
            "write_action_detected": write_action_detected,
            "approval_ref": approval_ref,
        }
        ch = self._channels_by_request.pop(request_id, channel)
        try:
            await ch.call("n2n/zoom/investigate_result", result_params, timeout=10.0)
        except Exception as e:
            # Best-effort, matches n2n/edge/task_progress precedent (research.md):
            # a zoom-rtms-mcp that restarted mid-flight simply never gets the push.
            logger.info("Could not push investigate_result for %s (best-effort): %s",
                        request_id, e)

    async def handle_session_closed(self, channel: ZoomChannel, params: dict) -> dict:
        meeting_uuid = params.get("meeting_uuid", "")
        logger.info("Zoom meeting %s closed (buffer already discarded client-side)", meeting_uuid)
        return {}


async def start_server(service, port: int) -> asyncio.AbstractServer:
    """Starts the loopback-only listener. Call from the daemon's main() after
    the FederationService is constructed, mirroring _start_edge()'s shape in
    bgp-daemon-v2.py."""
    manager = ZoomInvestigationManager(service)

    async def _on_conn(reader, writer):
        channel = ZoomChannel(reader, writer, handlers={
            "n2n/zoom/investigate": manager.handle_investigate,
            "n2n/zoom/session_closed": manager.handle_session_closed,
        })
        await channel.start()

    server = await asyncio.start_server(_on_conn, "127.0.0.1", port)
    logger.info("Zoom channel listening on 127.0.0.1:%d", port)
    return server
