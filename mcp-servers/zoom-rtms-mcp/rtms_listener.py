"""Per-meeting Zoom RTMS SDK session (research.md R4): consumes transcript,
chat, active-speaker, and screen-share-start/stop signals only — no raw
audio/video (FR-016). Appends entries to the MeetingSession's
LiveContextBuffer and drives connection_state transitions.

Uses Zoom's official RTMS SDK, not a hand-rolled implementation of the RTMS
wire protocol (research.md R4). The SDK (PyPI package "rtms") ships only a
cp313 wheel as of v1.1.0 — this server therefore runs from its own .venv
built with python3.13, not the system python3 (see requirements.txt and
config/openclaw.json's zoom-rtms-mcp entry). The import below still degrades
to a clearly-logged no-op if the SDK is somehow missing at runtime (e.g. the
venv wasn't set up), so the rest of zoom-rtms-mcp (webhook receipt, extractor,
panel feed, MCP tools) still imports and runs without it — but a correctly
set-up install always has it available.
"""

import asyncio
import json
import logging
import time

import recognition
from models import SpeakerChangeEntry, TranscriptEntry, registry

logger = logging.getLogger("zoom_rtms.listener")

try:
    import rtms as _rtms_sdk  # Zoom's official RTMS Python SDK (package name per Zoom's distribution)
    _SDK_AVAILABLE = True
except ImportError:
    _rtms_sdk = None
    _SDK_AVAILABLE = False
    logger.warning(
        "Zoom RTMS SDK not installed — rtms_listener will not receive live "
        "meeting signals. See requirements.txt. All other zoom-rtms-mcp "
        "functionality is unaffected."
    )

_active_listeners: dict[str, "MeetingRtmsListener"] = {}

# The SDK's Client.join() without an explicit EventLoop routes to its shared
# default loop, which only actually gets pumped by rtms.run_async() — this
# has to be running exactly once for the whole process, not per-meeting.
# Started lazily on the first real listener rather than at import time so a
# degraded (SDK-unavailable) install never touches it.
_default_loop_task: "asyncio.Task | None" = None


async def _ensure_default_loop_running():
    global _default_loop_task
    if _default_loop_task is None or _default_loop_task.done():
        _default_loop_task = asyncio.create_task(_rtms_sdk.run_async())
        # create_task() only schedules it — it doesn't actually start running
        # until this coroutine yields. Without this yield, a join() called
        # immediately after would still see the SDK's shared default loop as
        # not-yet-registered and silently fall back to spinning up its own
        # bare-OS-thread "implicit" loop instead — confirmed live 2026-08-19
        # as the actual root cause of a callback crashing with "no running
        # event loop" (that implicit loop's thread has none).
        await asyncio.sleep(0)


class MeetingRtmsListener:
    """Wraps one RTMS SDK session for one meeting_uuid."""

    def __init__(self, meeting_uuid: str, payload: dict):
        self.meeting_uuid = meeting_uuid
        self.payload = payload
        self._sdk_session = None
        self._task: asyncio.Task | None = None

    async def start(self):
        session = registry.get(self.meeting_uuid)
        if not session:
            logger.warning("start() called for unknown meeting %s", self.meeting_uuid)
            return
        if not _SDK_AVAILABLE:
            # Degraded mode: session exists (created by webhook.py), but no
            # live signals will ever arrive. connection_state reflects this
            # honestly rather than pretending to be "live".
            session.connection_state = "degraded"
            logger.warning(
                "Meeting %s: RTMS SDK unavailable, listener running in degraded "
                "(no-op) mode", self.meeting_uuid)
            return
        try:
            await _ensure_default_loop_running()
            client = _rtms_sdk.Client()
            # Only the signals FR-016 actually wants (transcript + chat, via
            # the raw-event hook below) — audio/video/deskshare are left
            # disabled, matching the least-privilege Marketplace scopes this
            # feature deliberately did not request.
            client.on_transcript_data(self._on_transcript_data)
            client.on_event_ex(self._on_event_ex)
            client.on_active_speaker_event(self._on_active_speaker_event)
            # Screen-share (on_sharing_event) deliberately not wired: it
            # requires DESKSHARE scope, which this feature's Marketplace app
            # never requested (least-privilege — transcript/chat text only,
            # no screen content). Not a gap; a scope choice.
            client.on_media_connection_interrupted(
                lambda ts: self._on_disconnect("media_connection_interrupted"))
            client.on_leave(lambda reason="": self._on_disconnect(reason or "left"))
            # join()'s own synchronous True/False only means "accepted onto an
            # EventLoop" — the actual alloc+join (and, per confirmed live
            # behaviour 2026-08-19, its Client-ID/secret validation) happens
            # later on that loop's own thread. Trusting the synchronous True
            # as "live" self-reported success it had not actually confirmed yet
            # — connection_state now only becomes "live" from the real
            # on_join_confirm callback.
            client.on_join_confirm(self._on_join_confirm)
            client.enable_transcript(True)
            # enable_transcript(True) alone leaves srcLanguage at its default
            # TranscriptLanguage.NONE (confirmed live 2026-08-19: transcript
            # enabled, Zoom's own Live Transcript on in the meeting, zero
            # transcript callbacks ever fired) — enableLid (auto-detect) is on
            # by default, but an explicit source language is the documented,
            # supported way to actually get output rather than relying on
            # auto-detection alone.
            transcript_params = _rtms_sdk.TranscriptParams()
            transcript_params.src_language = _rtms_sdk.TranscriptLanguage.ENGLISH
            client.set_transcript_params(transcript_params)
            # join() takes the raw webhook payload dict directly (meeting_uuid/
            # rtms_stream_id/server_urls all live in it already) — confirmed
            # against the SDK's own documented rtms.run() example. client/
            # secret are NOT merged in here because join() replaces its whole
            # params dict with this one when a dict is passed positionally
            # (confirmed by reading the SDK source) — they come from the
            # ZM_RTMS_CLIENT/ZM_RTMS_SECRET env vars instead (SDK's own
            # documented fallback).
            queued = client.join(self.payload)
            if not queued:
                raise RuntimeError("client.join() returned False")
            self._sdk_session = client
            session.connection_state = "connecting"
            logger.info("Meeting %s: RTMS join queued, awaiting confirmation", self.meeting_uuid)
        except Exception as e:
            session.connection_state = "degraded"
            logger.error("Meeting %s: RTMS connect failed: %s", self.meeting_uuid, e)

    async def stop(self):
        if self._sdk_session:
            try:
                self._sdk_session.leave()  # sync, safe from any thread per SDK docs
            except Exception:
                pass
        _active_listeners.pop(self.meeting_uuid, None)

    # ---- SDK callbacks ----------------------------------------------------

    def _session(self):
        return registry.get(self.meeting_uuid)

    def _on_transcript_data(self, data, stream_id, timestamp, metadata):
        # Callback shape confirmed against the SDK's own documented example:
        # on_transcript_data(lambda d,s,t,m: print(m.userName, d)). `data`
        # arrives as raw bytes (confirmed live 2026-08-19) — extractor.classify()
        # does `text.lower()` then `"marker" in lowered`, which raises TypeError
        # comparing str against bytes. That exception died silently inside the
        # scheduled coroutine, which is why real transcript arrived but nothing
        # downstream ever ran.
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        logger.warning("Meeting %s: transcript_data fired: data=%r stream_id=%r ts=%r",
                       self.meeting_uuid, data, stream_id, timestamp)
        s = self._session()
        if not s:
            return
        participant_id = getattr(metadata, "userId", "") or ""
        participant_name = getattr(metadata, "userName", "") or ""
        s.buffer.append(TranscriptEntry(time.time(), participant_id, participant_name,
                                         data, kind="transcript"))
        s.last_activity = time.time()
        recognition.on_new_entry(self.meeting_uuid, "speech", data)

    def _on_event_ex(self, raw_json: str):
        # KNOWN GAP (honest, not hidden): this SDK version has no dedicated
        # typed chat callback (only transcript/audio/video/deskshare do,
        # confirmed via introspection) — chat (MediaDataType.CHAT) has to be
        # picked out of the raw event stream here instead. Exact raw schema
        # isn't documented; this is deliberately defensive so a shape this
        # doesn't recognize is dropped (logged at debug), never crashes the
        # listener, and never gets misread as something it isn't.
        logger.warning("Meeting %s: raw event: %s", self.meeting_uuid, raw_json[:500])
        try:
            evt = json.loads(raw_json)
        except Exception:
            return
        content = evt.get("content") or {}
        if content.get("data_type") != "CHAT" and evt.get("event") != "chat":
            return
        s = self._session()
        if not s:
            return
        text = content.get("data") or evt.get("data") or ""
        if not text:
            return
        participant_id = str(content.get("user_id") or evt.get("user_id") or "")
        participant_name = str(content.get("user_name") or evt.get("user_name") or "")
        s.buffer.append(TranscriptEntry(time.time(), participant_id, participant_name,
                                         text, kind="chat"))
        s.last_activity = time.time()
        recognition.on_new_entry(self.meeting_uuid, "chat", text)

    def _on_join_confirm(self, *args):
        # Undocumented exact arg shape (native-extension callback, no Python
        # source to read) — accepted defensively rather than assumed. The
        # only thing that matters here is that the join actually completed;
        # a rejected/failed join reaches us via on_leave instead.
        s = self._session()
        if s:
            s.connection_state = "live"
            logger.info("Meeting %s: RTMS join confirmed, session live", self.meeting_uuid)

    def _on_active_speaker_event(self, timestamp, user_id, user_name):
        logger.warning("Meeting %s: active_speaker_event fired: user_id=%r user_name=%r",
                       self.meeting_uuid, user_id, user_name)
        s = self._session()
        if s:
            s.buffer.append(SpeakerChangeEntry(time.time(), str(user_id or "")))
        s.last_activity = time.time()

    def _on_disconnect(self, reason: str = ""):
        s = self._session()
        if s:
            s.connection_state = "degraded"
            logger.warning("Meeting %s: RTMS disconnected (%s)", self.meeting_uuid, reason)


async def start_listener(meeting_uuid: str, payload: dict):
    listener = MeetingRtmsListener(meeting_uuid, payload)
    _active_listeners[meeting_uuid] = listener
    await listener.start()


async def stop_listener(meeting_uuid: str):
    listener = _active_listeners.get(meeting_uuid)
    if listener:
        await listener.stop()
