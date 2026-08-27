#!/usr/bin/env python3
"""
Zoom RTMS MCP Server — NetClaw for Zoom Meeting Intelligence (spec 118)

Exposes tools per contracts/zoom-rtms-mcp-tools.md for querying live meeting
context and historical meeting correlation. The autonomous recognition path
(extractor.py -> recognition.py -> zoom_channel_client.py -> Border) runs
independently of any tool call here — these tools are the on-demand query
surface for the agent/operator, per that contract's own framing.

Background services (webhook receiver, panel feed, Border channel client) are
started at import time so they're live for the whole process lifetime,
regardless of which MCP tool (if any) gets called.
"""

import asyncio
import logging
import os
import threading

from mcp.server.fastmcp import FastMCP

import panel_feed
import recognition
import rtms_listener
import webhook
import zoom_channel_client
from models import registry

logging.basicConfig(level=os.environ.get("ZOOM_RTMS_LOG_LEVEL", "INFO"))
logger = logging.getLogger("zoom_rtms.server")

mcp = FastMCP("zoom-rtms")

# ---------------------------------------------------------------------------
# Background services
# ---------------------------------------------------------------------------

_bg_loop: asyncio.AbstractEventLoop | None = None


def _on_meeting_started(meeting_uuid: str, payload: dict):
    if _bg_loop:
        asyncio.run_coroutine_threadsafe(rtms_listener.start_listener(meeting_uuid, payload),
                                          _bg_loop)


def _on_meeting_stopped(meeting_uuid: str):
    if _bg_loop:
        asyncio.run_coroutine_threadsafe(rtms_listener.stop_listener(meeting_uuid), _bg_loop)
        asyncio.run_coroutine_threadsafe(zoom_channel_client.notify_session_closed(meeting_uuid),
                                          _bg_loop)


def _run_background_loop():
    global _bg_loop
    loop = asyncio.new_event_loop()
    _bg_loop = loop
    recognition.set_bg_loop(loop)
    asyncio.set_event_loop(loop)

    async def _startup():
        await panel_feed.start_panel_feed_server()
        await zoom_channel_client.get_client()

    loop.run_until_complete(_startup())
    loop.run_forever()


def _start_background_services():
    webhook.on_meeting_started = _on_meeting_started
    webhook.on_meeting_stopped = _on_meeting_stopped
    zoom_channel_client.on_investigate_result = recognition.handle_investigate_result
    webhook.start_webhook_server()
    thread = threading.Thread(target=_run_background_loop, daemon=True,
                               name="zoom-rtms-bg-loop")
    thread.start()


_start_background_services()

# ---------------------------------------------------------------------------
# MCP tools (contracts/zoom-rtms-mcp-tools.md)
# ---------------------------------------------------------------------------


@mcp.tool()
def zoom_enable_listening(meeting_id: str) -> dict:
    """Enable RTMS listening for a meeting (FR-001/FR-015).

    If Zoom's own auto-start-for-RTMS-apps setting is enabled (confirmed live
    for this feature's own Marketplace app during setup), a MeetingSession is
    typically already created via the rtms_started webhook by the time an
    operator would call this. This tool additionally supports the
    REST-triggered launch path (research.md, RTMS getting-started guide) for
    meetings without auto-start — that REST call requires live Zoom OAuth
    credentials (ZOOM_CLIENT_ID/ZOOM_CLIENT_SECRET/ZOOM_ACCOUNT_ID) not
    available in this environment; if a session doesn't already exist and
    those credentials aren't configured, this returns rtms_unavailable rather
    than silently pretending to succeed.
    """
    session = registry.get(meeting_id)
    if session:
        return {"meeting_uuid": meeting_id, "listening_enabled": True}
    if not (os.environ.get("ZOOM_CLIENT_ID") and os.environ.get("ZOOM_CLIENT_SECRET")):
        return {"error": "rtms_unavailable",
                "reason": "no active session and no Zoom OAuth credentials configured for "
                          "REST-triggered launch"}
    return {"error": "rtms_unavailable",
            "reason": "REST-triggered launch not implemented in this environment — "
                      "rely on auto-start (already enabled for this app) instead"}


@mcp.tool()
def zoom_disable_listening(meeting_uuid: str) -> dict:
    """Disable listening and destroy the live buffer immediately (FR-014)."""
    existed = registry.destroy(meeting_uuid)
    return {"listening_enabled": False, "existed": existed}


@mcp.tool()
def zoom_list_active_meetings() -> dict:
    """FR-015: which meetings currently have listening enabled."""
    return {"meetings": [
        {"meeting_uuid": s.meeting_uuid, "started_at": s.started_at,
         "connection_state": s.connection_state}
        for s in registry.list_active()
    ]}


@mcp.tool()
def zoom_meeting_status(meeting_uuid: str) -> dict:
    session = registry.get(meeting_uuid)
    if not session:
        return {"error": "not_found"}
    return {"connection_state": session.connection_state, "avatar_state": session.avatar_state,
            "participant_count": len(session.viewers)}


@mcp.tool()
def zoom_recent_transcript(meeting_uuid: str, minutes: float = None) -> dict:
    session = registry.get(meeting_uuid)
    if not session:
        return {"error": "not_found"}
    entries = session.buffer.recent(minutes=minutes, kinds={"transcript"})
    return {"entries": [{"timestamp": e.timestamp, "participant_id": e.participant_id,
                          "participant_name": e.participant_name, "text": e.text}
                         for e in entries]}


@mcp.tool()
def zoom_recent_chat(meeting_uuid: str, minutes: float = None) -> dict:
    session = registry.get(meeting_uuid)
    if not session:
        return {"error": "not_found"}
    entries = session.buffer.recent(minutes=minutes, kinds={"chat"})
    return {"entries": [{"timestamp": e.timestamp, "participant_id": e.participant_id,
                          "participant_name": e.participant_name, "text": e.text}
                         for e in entries]}


@mcp.tool()
def zoom_active_speaker(meeting_uuid: str) -> dict:
    session = registry.get(meeting_uuid)
    if not session:
        return {"error": "not_found"}
    speaker_entries = session.buffer.recent(kinds={"speaker_change"})
    return {"participant_id": speaker_entries[-1].participant_id if speaker_entries else None}


@mcp.tool()
def zoom_live_context(meeting_uuid: str) -> dict:
    session = registry.get(meeting_uuid)
    if not session:
        return {"error": "not_found"}
    current = None
    if session.current_investigation_id:
        req = session.investigations.get(session.current_investigation_id)
        if req:
            current = {
                "request_id": req.request_id, "raw_text": req.raw_text,
                "location": req.location, "technology": req.technology,
                "time_window": req.time_window, "routing_outcome": req.routing_outcome,
                "answer_summary": req.answer_summary,
            }
    speaker_entries = session.buffer.recent(kinds={"speaker_change"})
    return {
        "connection_state": session.connection_state,
        "avatar_state": session.avatar_state,
        "recent_transcript": [e.text for e in session.buffer.recent(kinds={"transcript"})],
        "recent_chat": [e.text for e in session.buffer.recent(kinds={"chat"})],
        "active_speaker": speaker_entries[-1].participant_id if speaker_entries else None,
        "current_investigation": current,
    }


@mcp.tool()
def zoom_search_historical_meetings(query: str, time_hint: str = None) -> dict:
    """US2/T031: thin pass-through to the official Zoom Meetings MCP
    (research.md R6). Not implemented against a live Zoom MCP connection in
    this environment — the official Zoom MCP's exact tool name/credential
    shape is still TBD per research.md R6/task T030. Returns explicitly so,
    rather than fabricating a result (spec's own "no matching past meeting"
    requirement extended to "can't search at all yet")."""
    return {"matches": [], "note": "official Zoom Meetings MCP integration pending "
                                    "confirmation of its tool name/credential shape (R6/T030)"}


if __name__ == "__main__":
    mcp.run()
