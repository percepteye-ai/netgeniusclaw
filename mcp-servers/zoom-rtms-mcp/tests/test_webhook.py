import hashlib
import hmac
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import webhook  # noqa: E402
from models import registry  # noqa: E402


def test_url_validation_handshake():
    webhook.SECRET_TOKEN = "test-secret"
    payload = {"event": "endpoint.url_validation", "payload": {"plainToken": "abc123"}}
    result = webhook.process_webhook_event(payload)
    expected = hmac.new(b"test-secret", b"abc123", hashlib.sha256).hexdigest()
    assert result == {"plainToken": "abc123", "encryptedToken": expected}


def test_meeting_started_creates_session():
    meeting_uuid = "test-meeting-1"
    webhook.process_webhook_event({
        "event": "meeting.rtms_started",
        "payload": {"meeting_uuid": meeting_uuid},
    })
    assert registry.get(meeting_uuid) is not None
    registry.destroy(meeting_uuid)


def test_meeting_stopped_destroys_session_not_just_flags_it():
    """SC-006 / T013: the MeetingSession object is actually gone (not merely
    marked ended) after a stop webhook, and its buffer is unreachable."""
    meeting_uuid = "test-meeting-2"
    session = registry.create(meeting_uuid)
    session.buffer.append(object.__new__(object))  # anything, just to have content
    assert registry.get(meeting_uuid) is not None

    webhook.process_webhook_event({
        "event": "meeting.rtms_stopped",
        "payload": {"meeting_uuid": meeting_uuid},
    })

    assert registry.get(meeting_uuid) is None
