"""Loopback client side of bgp/federation/zoom_channel.py (research.md R1).
Connects to the Border daemon's local Zoom channel, authenticates with the
shared secret, and submits recognized investigation requests / session-closed
notifications. Also dispatches Border-pushed investigate_result messages back
into this process's MeetingSession state.
"""

import asyncio
import json
import logging
import os
import struct
import uuid
from typing import Optional

logger = logging.getLogger("zoom_rtms.channel_client")

_MAX_FRAME = 1 * 1024 * 1024
BORDER_HOST = os.environ.get("N2N_ZOOM_CHANNEL_HOST", "127.0.0.1")
BORDER_PORT = int(os.environ.get("N2N_ZOOM_CHANNEL_PORT", "0") or 0)
SHARED_SECRET = os.environ.get("N2N_ZOOM_CHANNEL_SECRET", "")

# Set by server.py: callable(dict) invoked when investigate_result arrives.
on_investigate_result = None


class RpcError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class ZoomChannelClient:
    def __init__(self):
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._next_id = 0
        self._pending: dict = {}
        self._read_task: Optional[asyncio.Task] = None
        self.connected = False

    async def connect(self):
        if not BORDER_PORT:
            logger.warning("N2N_ZOOM_CHANNEL_PORT not set — cannot reach Border")
            return False
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(BORDER_HOST, BORDER_PORT), timeout=5.0)
        except (OSError, asyncio.TimeoutError) as e:
            # Deliberately non-fatal: zoom-rtms-mcp's webhook/panel-feed/MCP-tool
            # surface must keep working even if the Border isn't up yet (or at
            # all) — only the autonomous investigate path needs this channel.
            # Without this timeout, a Border that's down/unreachable hung the
            # entire background-services startup indefinitely (discovered
            # live 2026-08-17 testing against a real Zoom meeting — panel_feed
            # never got a chance to start because this ran before it and never
            # returned).
            logger.warning("Could not connect to Border zoom channel (%s:%s): %s",
                            BORDER_HOST, BORDER_PORT, e)
            return False
        self._read_task = asyncio.create_task(self._read_loop())
        try:
            resp = await self.call("n2n/zoom/hello", {"secret": SHARED_SECRET})
            self.connected = bool(resp.get("trusted"))
        except Exception as e:
            logger.warning("Zoom channel handshake failed: %s", e)
            self.connected = False
        return self.connected

    async def _read_loop(self):
        try:
            while True:
                header = await self.reader.readexactly(4)
                (length,) = struct.unpack("!I", header)
                if length > _MAX_FRAME:
                    break
                raw = await self.reader.readexactly(length)
                await self._dispatch(raw)
        except (asyncio.IncompleteReadError, ConnectionResetError, asyncio.CancelledError):
            pass
        except Exception as e:
            logger.info("Zoom channel client read loop ended: %s", e)
        finally:
            self.connected = False

    async def _dispatch(self, raw: bytes):
        msg = json.loads(raw)
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
        if method == "n2n/zoom/investigate_result":
            if on_investigate_result:
                try:
                    on_investigate_result(params)
                except Exception as e:
                    logger.error("on_investigate_result handler failed: %s", e)
            if req_id is not None:
                await self._send({"jsonrpc": "2.0", "id": req_id, "result": {}})
        elif req_id is not None:
            await self._send({"jsonrpc": "2.0", "id": req_id,
                               "error": {"code": -32601, "message": f"unknown method {method}"}})

    async def _send(self, message: dict):
        payload = json.dumps(message, separators=(",", ":")).encode()
        self.writer.write(struct.pack("!I", len(payload)) + payload)
        await self.writer.drain()

    async def call(self, method: str, params: dict, timeout: float = 30.0) -> dict:
        self._next_id += 1
        req_id = f"zoom-rtms-mcp:{self._next_id}"
        fut = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut
        await self._send({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params})
        resp = await asyncio.wait_for(fut, timeout=timeout)
        if "error" in resp:
            raise RpcError(resp["error"]["code"], resp["error"]["message"])
        return resp.get("result", {})

    async def notify(self, method: str, params: dict):
        await self._send({"jsonrpc": "2.0", "method": method, "params": params})


_client: Optional[ZoomChannelClient] = None


async def get_client() -> ZoomChannelClient:
    global _client
    if _client is None or not _client.connected:
        _client = ZoomChannelClient()
        await _client.connect()
    return _client


async def submit_investigation(meeting_uuid: str, source: str, raw_text: str,
                                location: Optional[str], technology: Optional[str],
                                time_window: Optional[str]) -> dict:
    client = await get_client()
    if not client.connected:
        return {"accepted": False, "reason": "not connected to Border"}
    request_id = str(uuid.uuid4())
    return await client.call("n2n/zoom/investigate", {
        "request_id": request_id, "meeting_uuid": meeting_uuid, "source": source,
        "raw_text": raw_text, "location": location, "technology": technology,
        "time_window": time_window,
    })


async def notify_session_closed(meeting_uuid: str):
    client = await get_client()
    if client.connected:
        await client.notify("n2n/zoom/session_closed", {"meeting_uuid": meeting_uuid})
