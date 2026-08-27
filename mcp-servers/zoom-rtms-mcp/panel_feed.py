"""Companion WebSocket server (research.md R3): a presentation-layer-only feed
from zoom-rtms-mcp to the browser-embedded Zoom App panel. Deliberately
separate from NCFED/GAIT/peer-trust — see contracts/zoom-app-panel-feed.md.

Handles:
  - avatar_state / topic_detected / investigation_result / connection_state
    pushes (US1/US3), broadcast to every viewer of a meeting_uuid at once
    (FR-011, SC-004) within 2 seconds of the underlying change (SC-009).
  - viewer_joined tracking (MeetingSession.viewers, SC-004 verification).
  - camera_overlay_enable/disable (US5), restricted to the sending
    participant's own participant_id (FR-019).
"""

import asyncio
import json
import logging
import mimetypes
import os

import websockets
from websockets.datastructures import Headers
from websockets.http11 import Response

from models import registry

logger = logging.getLogger("zoom_rtms.panel_feed")

PORT = int(os.environ.get("ZOOM_PANEL_FEED_PORT", "8900"))

# The Zoom App's Home URL points at /panel/ on this same port (single ngrok
# tunnel / single production host, per quickstart.md) — panel.js then opens
# its WebSocket to "/" on that same host (see panel.js's wsUrl). This module
# therefore serves both: plain HTTP GET for anything under /panel, and the
# actual WebSocket upgrade for everything else (in practice, "/").
_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "ui", "netclaw-zoom-app")
_STATIC_FILES = {
    "/panel/": "panel.html",
    "/panel": "panel.html",
    "/panel/panel.js": "panel.js",
    "/panel/panel.css": "panel.css",
    "/panel/overlay.js": "overlay.js",
}


_OAUTH_CALLBACK_BODY = (
    b"<html><body><p>NetClaw authorized. You can close this window and "
    b"return to your meeting.</p></body></html>"
)


async def _serve_static(connection, request):
    path = request.path.split("?", 1)[0]
    upgrade_hdr = request.headers.get("Upgrade", "")
    origin_hdr = request.headers.get("Origin", "")
    ua_hdr = request.headers.get("User-Agent", "")
    logger.info("panel_feed request: path=%r upgrade=%r origin=%r user-agent=%r",
                request.path, upgrade_hdr, origin_hdr, ua_hdr)
    if path == "/oauth/callback":
        # Zoom's install/consent flow redirects the browser here after the
        # user authorizes. This app's data access is scoped per-meeting via
        # the Zoom Apps SDK session (zoomapp:inmeeting), not a stored OAuth
        # token, so there is no code-exchange step to perform — this only
        # needs to give the browser a clean landing page instead of a 404/
        # connection error (discovered live 2026-08-17: nothing served this
        # path at all before, breaking the consent flow's final step).
        headers = Headers([
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(_OAUTH_CALLBACK_BODY))),
            ("Strict-Transport-Security", "max-age=63072000; includeSubDomains"),
            ("X-Content-Type-Options", "nosniff"),
            ("Referrer-Policy", "strict-origin-when-cross-origin"),
        ])
        return Response(200, "OK", headers, _OAUTH_CALLBACK_BODY)
    filename = _STATIC_FILES.get(path)
    if filename is None:
        # Not a recognized static path — let it fall through to the
        # WebSocket handshake (the "/" case panel.js actually connects to).
        return None
    file_path = os.path.join(_STATIC_DIR, filename)
    try:
        with open(file_path, "rb") as f:
            body = f.read()
    except OSError:
        return Response(404, "Not Found", Headers([("Content-Type", "text/plain")]), b"not found")
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    headers = Headers([
        ("Content-Type", content_type),
        ("Content-Length", str(len(body))),
        # Every edit to panel.js during live debugging needs the very next
        # load to actually be the new file, not whatever Zoom's client
        # webview (or an intermediate proxy) decided to cache with no
        # explicit cache headers to go on.
        ("Cache-Control", "no-store"),
        ("Strict-Transport-Security", "max-age=63072000; includeSubDomains"),
        # No frame-ancestors directive: Zoom's desktop client embeds this
        # page from an origin that does not reliably match a zoom.us-style
        # HTTPS pattern (confirmed live 2026-08-19 — panel.html fetched fine,
        # 200 OK, but panel.js was never once requested by the real Zoom
        # client, only by manual curl checks; Zoom's own devforum reports the
        # same "ancestor violates frame-ancestors" failure mode and recommends
        # dropping the restriction rather than guessing at the client's
        # embedding origin). Zoom's own app-review process is the actual
        # control on who can embed this Home URL, not this header.
        ("Content-Security-Policy", "default-src 'self' https://appssdk.zoom.us; script-src 'self' https://appssdk.zoom.us"),
        # Zoom's own client-side app-launch validator checks the Home URL
        # response for a specific OWASP header set and silently aborts the
        # app load (generic client error, no page-visible signal) if any are
        # missing — confirmed live 2026-08-19 via Zoom's own webview console:
        # "Missing OWASP Secure Headers: [X-Content-Type-Options,
        # Referrer-Policy]". HSTS/CSP alone were not sufficient.
        ("X-Content-Type-Options", "nosniff"),
        ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ])
    return Response(200, "OK", headers, body)

# meeting_uuid -> set of websocket connections currently viewing that meeting
_connections: dict[str, set] = {}
# meeting_uuid -> participant_id -> websocket, for camera-overlay's "only own
# feed" restriction (FR-019)
_participant_sockets: dict[str, dict] = {}


async def _broadcast(meeting_uuid: str, message: dict):
    conns = _connections.get(meeting_uuid, set())
    dead = set()
    payload = json.dumps(message)
    for ws in conns:
        try:
            await ws.send(payload)
        except Exception:
            dead.add(ws)
    conns -= dead


async def push_avatar_state(meeting_uuid: str, state: str):
    session = registry.get(meeting_uuid)
    if session:
        session.avatar_state = state
    await _broadcast(meeting_uuid, {"type": "avatar_state", "meeting_uuid": meeting_uuid,
                                     "state": state})


async def push_topic_detected(meeting_uuid: str, location, technology, time_window):
    await _broadcast(meeting_uuid, {"type": "topic_detected", "meeting_uuid": meeting_uuid,
                                     "location": location, "technology": technology,
                                     "time_window": time_window})


async def push_investigation_result(meeting_uuid: str, request_id: str, answer_summary,
                                     evidence_refs):
    await _broadcast(meeting_uuid, {"type": "investigation_result", "meeting_uuid": meeting_uuid,
                                     "request_id": request_id, "answer_summary": answer_summary,
                                     "evidence_refs": evidence_refs or []})


async def push_connection_state(meeting_uuid: str, state: str):
    await _broadcast(meeting_uuid, {"type": "connection_state", "meeting_uuid": meeting_uuid,
                                     "state": state})


async def _handle_client_message(ws, meeting_uuid: str, msg: dict):
    kind = msg.get("type")
    participant_id = msg.get("participant_id")

    if kind == "viewer_joined":
        session = registry.get(meeting_uuid)
        if session and participant_id:
            session.viewers.add(participant_id)
        _participant_sockets.setdefault(meeting_uuid, {})[participant_id] = ws

    elif kind == "camera_overlay_enable":
        # FR-019: only ever applies to the sending participant's own feed —
        # the server never accepts a participant_id other than the one this
        # connection already identified itself as via viewer_joined.
        known = _participant_sockets.get(meeting_uuid, {}).get(participant_id)
        if known is ws:
            session = registry.get(meeting_uuid)
            if session:
                session.camera_overlay_enrollments.add(participant_id)
            logger.info("Camera overlay enabled for %s in %s", participant_id, meeting_uuid)

    elif kind == "camera_overlay_disable":
        known = _participant_sockets.get(meeting_uuid, {}).get(participant_id)
        if known is ws:
            session = registry.get(meeting_uuid)
            if session:
                session.camera_overlay_enrollments.discard(participant_id)
            logger.info("Camera overlay disabled for %s in %s", participant_id, meeting_uuid)


async def _handler(ws):
    logger.warning("TRACE: new panel WS connection opened")
    # First message on a connection must carry meeting_uuid to route it.
    meeting_uuid = None
    try:
        async for raw in ws:
            logger.warning("TRACE: panel WS raw message received: %r", raw[:500])
            try:
                msg = json.loads(raw)
            except Exception as e:
                logger.warning("TRACE: panel WS message JSON parse failed: %s", e)
                continue

            if msg.get("type") == "identify_by_active_meeting":
                # Fallback for when Zoom's own getMeetingContext()/
                # getUserContext() reject the panel with "No Permission for
                # this API [code:80004, reason:app_not_support]" (confirmed
                # live 2026-08-19 — a Marketplace-side app configuration gap,
                # not something client code can route around directly). This
                # server already knows the true meeting_uuid authoritatively
                # from the RTMS webhook, independent of the Zoom SDK — so a
                # panel that can't self-identify asks us instead. Picks the
                # most-recently-started active session; fine for this
                # feature's single-operator, single-live-meeting usage today,
                # not a multi-tenant routing solution.
                # last_activity, not started_at: confirmed live 2026-08-19 —
                # Zoom fired two separate meeting.rtms_started webhooks with
                # two different meeting_uuids for what was one physical
                # meeting (an RTMS-level reconnect). Picking "most recently
                # started" landed on the newer-but-silent session while all
                # the real transcript kept flowing through the older one —
                # the panel connected to an empty room, no error anywhere.
                active = sorted(registry.list_active(), key=lambda s: s.last_activity, reverse=True)
                if active:
                    meeting_uuid = active[0].meeting_uuid
                    _connections.setdefault(meeting_uuid, set()).add(ws)
                    await ws.send(json.dumps({"type": "identified", "meeting_uuid": meeting_uuid}))
                    logger.warning("TRACE: identified connection to active meeting_uuid=%r",
                                   meeting_uuid)
                else:
                    logger.warning("TRACE: identify_by_active_meeting — no active meetings")
                continue

            meeting_uuid = msg.get("meeting_uuid", meeting_uuid)
            if not meeting_uuid:
                logger.warning("TRACE: panel WS message has no meeting_uuid, dropping: %r", msg)
                continue
            _connections.setdefault(meeting_uuid, set()).add(ws)
            logger.warning("TRACE: registered connection for meeting_uuid=%r (now %d conns)",
                           meeting_uuid, len(_connections[meeting_uuid]))
            await _handle_client_message(ws, meeting_uuid, msg)
    except Exception as e:
        logger.warning("TRACE: panel WS connection closed: %s", e)
    finally:
        if meeting_uuid:
            _connections.get(meeting_uuid, set()).discard(ws)


async def start_panel_feed_server():
    server = await websockets.serve(
        _handler, "0.0.0.0", PORT, process_request=_serve_static)
    logger.info(
        "Panel feed WebSocket + static panel (%s) listening on 0.0.0.0:%d",
        _STATIC_DIR, PORT)
    return server
