"""Receives Zoom's meeting.rtms_started / meeting.rtms_stopped webhook events
(research.md R5) and drives MeetingSession lifecycle. Also implements Zoom's
standard webhook URL-validation handshake (endpoint.url_validation), proven
against a real Zoom Marketplace app during this feature's own setup session.

Runs a small stdlib http.server in a background thread — no new HTTP
dependency beyond what's already vendored elsewhere in this repo.
"""

import hashlib
import hmac
import http.server
import json
import logging
import os
import threading

from models import registry

logger = logging.getLogger("zoom_rtms.webhook")

SECRET_TOKEN = os.environ.get("ZOOM_RTMS_WEBHOOK_SECRET", "")
PORT = int(os.environ.get("ZOOM_RTMS_WEBHOOK_PORT", "8899"))

# Set by server.py at startup; kept as plain module-level callables so
# webhook.py has no import-time dependency on rtms_listener/zoom_channel_client
# (avoids a circular import — both of those import `models`, not `webhook`).
on_meeting_started = None  # callable(meeting_uuid: str, payload: dict)
on_meeting_stopped = None  # callable(meeting_uuid: str)


def _validate_signature(payload: dict) -> dict:
    """Zoom's endpoint.url_validation handshake: HMAC-SHA256(secret, plainToken)."""
    plain_token = payload.get("payload", {}).get("plainToken", "")
    encrypted = hmac.new(SECRET_TOKEN.encode(), plain_token.encode(), hashlib.sha256).hexdigest()
    return {"plainToken": plain_token, "encryptedToken": encrypted}


def process_webhook_event(data: dict) -> dict:
    """Core event handling, factored out of _Handler so it's unit-testable
    without spinning up a real HTTP server (T013)."""
    event = data.get("event")
    if event == "endpoint.url_validation":
        return _validate_signature(data)

    payload = data.get("payload", {}) or {}
    meeting_uuid = payload.get("meeting_uuid") or payload.get("object", {}).get("uuid", "")

    if event == "meeting.rtms_started":
        session = registry.get(meeting_uuid) or registry.create(meeting_uuid)
        session.connection_state = "connecting"
        logger.info("RTMS started for meeting %s", meeting_uuid)
        if on_meeting_started:
            try:
                on_meeting_started(meeting_uuid, payload)
            except Exception as e:
                logger.error("on_meeting_started failed: %s", e)
    elif event == "meeting.rtms_stopped":
        logger.info("RTMS stopped for meeting %s", meeting_uuid)
        if on_meeting_stopped:
            try:
                on_meeting_stopped(meeting_uuid)
            except Exception as e:
                logger.error("on_meeting_stopped failed: %s", e)
        # FR-014/SC-006: destroy, not merely flag ended.
        registry.destroy(meeting_uuid)

    return {}


class _Handler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, code: int, body: dict):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if not self.path.startswith("/webhooks/zoom/rtms"):
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw)
        except Exception:
            self._send_json(400, {"error": "invalid JSON"})
            return
        self._send_json(200, process_webhook_event(data))

    def log_message(self, fmt, *args):
        logger.debug("%s - %s", self.address_string(), fmt % args)


def start_webhook_server() -> threading.Thread:
    if not SECRET_TOKEN:
        logger.warning("ZOOM_RTMS_WEBHOOK_SECRET not set — URL validation handshake will fail")
    server = http.server.HTTPServer(("0.0.0.0", PORT), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name="zoom-rtms-webhook")
    thread.start()
    logger.info("RTMS webhook server listening on 0.0.0.0:%d", PORT)
    return thread
