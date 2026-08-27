"""In-memory data model for NetClaw for Zoom — Meeting Intelligence (spec 118).

Everything here lives only in this process's memory. Nothing is persisted to
disk or a database (data-model.md) — a MeetingSession and its LiveContextBuffer
are destroyed, not soft-deleted, when a meeting ends (FR-014).
"""

import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

# Buffer bound pinned at /speckit.analyze remediation time (2026-08-17,
# H2): the last 15 minutes of activity, capped at 500 entries, whichever
# limit is reached first. Both bounds enforced together (data-model.md).
BUFFER_MAX_AGE_S = 15 * 60
BUFFER_MAX_ENTRIES = 500

CONNECTION_STATES = ("connecting", "live", "degraded", "closed")
AVATAR_STATES = ("listening", "thinking", "investigating", "answered")


def _now() -> float:
    return time.time()


@dataclass
class TranscriptEntry:
    timestamp: float
    participant_id: str
    participant_name: str
    text: str
    kind: str = "transcript"  # or "chat"


@dataclass
class SpeakerChangeEntry:
    timestamp: float
    participant_id: str
    kind: str = "speaker_change"


@dataclass
class ContentEntry:
    timestamp: float
    kind: str  # "screen_share_started" | "screen_share_ended"
    participant_id: str


@dataclass
class LiveContextBuffer:
    """Bounded ring buffer of recent transcript/chat/speaker/content entries."""

    entries: deque = field(default_factory=lambda: deque(maxlen=BUFFER_MAX_ENTRIES))

    def append(self, entry):
        self._evict_stale()
        self.entries.append(entry)

    def _evict_stale(self):
        cutoff = _now() - BUFFER_MAX_AGE_S
        while self.entries and getattr(self.entries[0], "timestamp", cutoff) < cutoff:
            self.entries.popleft()

    def recent(self, minutes: Optional[float] = None, kinds=None):
        self._evict_stale()
        cutoff = _now() - (minutes * 60) if minutes else 0
        out = [e for e in self.entries if e.timestamp >= cutoff]
        if kinds:
            out = [e for e in out if getattr(e, "kind", None) in kinds]
        return out


@dataclass
class InvestigationRequest:
    request_id: str
    meeting_uuid: str
    source: str  # "speech" | "chat"
    raw_text: str
    location: Optional[str] = None
    technology: Optional[str] = None
    time_window: Optional[str] = None
    session_key: str = ""
    routing_outcome: Optional[str] = None  # answered|failed_no_tooling|failed_ambiguous
    answer_summary: Optional[str] = None
    evidence_refs: list = field(default_factory=list)
    write_action_detected: bool = False
    approval_ref: Optional[str] = None
    created_at: float = field(default_factory=_now)


@dataclass
class MeetingSession:
    meeting_uuid: str
    listening_enabled: bool = True
    started_at: float = field(default_factory=_now)
    # Bumped on every real transcript/chat/event arrival — confirmed live
    # 2026-08-19: Zoom can fire TWO separate meeting.rtms_started webhooks
    # with two different meeting_uuids for what is, from the operator's
    # side, one physical meeting (likely an RTMS-level reconnect). Picking
    # "most recently started" for the panel's identify_by_active_meeting
    # fallback landed on the newer-but-silent session while all the real
    # transcript kept flowing through the older one — the panel connected
    # to an empty room and every subsequent push vanished with no error.
    # "Most recently active" is the far more reliable signal of which
    # session is actually the live one right now.
    last_activity: float = field(default_factory=_now)
    ended_at: Optional[float] = None
    connection_state: str = "connecting"
    avatar_state: str = "listening"
    viewers: set = field(default_factory=set)
    camera_overlay_enrollments: set = field(default_factory=set)
    buffer: LiveContextBuffer = field(default_factory=LiveContextBuffer)
    investigations: dict = field(default_factory=dict)  # request_id -> InvestigationRequest
    current_investigation_id: Optional[str] = None

    def new_investigation(self, **kwargs) -> InvestigationRequest:
        req_id = str(uuid.uuid4())
        req = InvestigationRequest(request_id=req_id, meeting_uuid=self.meeting_uuid, **kwargs)
        self.investigations[req_id] = req
        self.current_investigation_id = req_id
        return req


class MeetingSessionRegistry:
    """Process-wide registry of active MeetingSessions, keyed by meeting_uuid."""

    def __init__(self):
        self._sessions: dict[str, MeetingSession] = {}

    def create(self, meeting_uuid: str) -> MeetingSession:
        session = MeetingSession(meeting_uuid=meeting_uuid)
        self._sessions[meeting_uuid] = session
        return session

    def get(self, meeting_uuid: str) -> Optional[MeetingSession]:
        return self._sessions.get(meeting_uuid)

    def destroy(self, meeting_uuid: str) -> bool:
        """FR-014: destroy, not merely flag ended. Returns True if a session existed."""
        return self._sessions.pop(meeting_uuid, None) is not None

    def list_active(self) -> list[MeetingSession]:
        return list(self._sessions.values())


registry = MeetingSessionRegistry()
