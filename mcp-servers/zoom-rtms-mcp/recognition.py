"""Orchestrates extractor.py (classification) + zoom_channel_client.py
(submission to Border) + panel_feed.py (live status pushes) for every new
transcript/chat entry. Kept separate from rtms_listener.py's SDK callbacks so
each module has one job (Constitution Principle VII: Skill Modularity).
"""

import asyncio
import logging
import time

import extractor
import panel_feed
import zoom_channel_client
from models import registry

logger = logging.getLogger("zoom_rtms.recognition")

# Mirrors server.py's own _bg_loop pattern. Needed because on_new_entry() is
# called synchronously from rtms_listener.py's SDK callbacks, which — confirmed
# live 2026-08-19 — can run on the SDK's own bare OS thread (its "implicit"
# single-client EventLoop), not necessarily on any asyncio loop at all.
# asyncio.create_task() requires a *running loop in the calling thread*; it
# doesn't have one there, which crashed the process outright (RuntimeError:
# no running event loop). run_coroutine_threadsafe() is the actual
# thread-safe way to schedule work onto a specific loop from any thread,
# which is what this needs regardless of which thread called in.
_bg_loop: asyncio.AbstractEventLoop | None = None


def set_bg_loop(loop: asyncio.AbstractEventLoop):
    global _bg_loop
    _bg_loop = loop

# T024: collapse a speech+chat duplicate of the same utterance, within this
# window, into one request rather than two.
_DEDUP_WINDOW_S = 5.0

# meeting_uuid -> (normalized_text, timestamp) of the most recent submitted request
_recent_submissions: dict[str, tuple] = {}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def on_new_entry(meeting_uuid: str, source: str, text: str):
    """Called synchronously from an RTMS SDK callback — possibly from a bare
    OS thread with no asyncio loop of its own — so scheduling the actual
    (async) recognition work has to be thread-safe, not just non-blocking."""
    if _bg_loop is None:
        logger.error("on_new_entry called before set_bg_loop() — dropping: %r", text)
        return
    future = asyncio.run_coroutine_threadsafe(_process(meeting_uuid, source, text), _bg_loop)

    def _log_if_failed(f):
        exc = f.exception()
        if exc is not None:
            # Without this, an exception here (confirmed live 2026-08-19: a
            # str/bytes TypeError from extractor.classify()) is otherwise
            # silent — a real transcript arrives, nothing happens, and the
            # only trace is asyncio's own lazy "exception was never
            # retrieved" warning at GC time, if that even fires before the
            # process exits.
            logger.error("on_new_entry: _process failed for %r: %r", text, exc)

    future.add_done_callback(_log_if_failed)


async def _process(meeting_uuid: str, source: str, text: str):
    logger.warning("TRACE Meeting %s: _process ENTER text=%r", meeting_uuid, text)
    result = extractor.classify(text)
    logger.warning("TRACE Meeting %s: classify -> %s", meeting_uuid, result)

    if result.kind == "suppressed":
        # FR-009: never even constructs a request. Logged for auditability of
        # the boundary itself, not treated as an event of any kind downstream.
        logger.info("Meeting %s: suppressed (%s): %r", meeting_uuid, result.reason, text)
        return

    if result.kind not in ("investigate", "write_command"):
        return

    # T024: same utterance arriving via both speech and chat within the dedup
    # window collapses to one request.
    normalized = _normalize(text)
    prev = _recent_submissions.get(meeting_uuid)
    if prev and prev[0] == normalized and (time.time() - prev[1]) < _DEDUP_WINDOW_S:
        logger.info("Meeting %s: duplicate of recent request, not resubmitting", meeting_uuid)
        return
    _recent_submissions[meeting_uuid] = (normalized, time.time())

    fields = extractor.extract_fields(text)

    # T022: ambiguous edge case — classified as investigate-worthy but nothing
    # resolvable. Surface plainly rather than guess.
    if result.kind == "investigate" and not (fields.location or fields.technology):
        await panel_feed.push_investigation_result(
            meeting_uuid, request_id="", answer_summary=None, evidence_refs=[])
        session = registry.get(meeting_uuid)
        if session:
            req = session.new_investigation(source=source, raw_text=text,
                                              location=fields.location,
                                              technology=fields.technology,
                                              time_window=fields.time_window)
            req.routing_outcome = "failed_ambiguous"
        logger.info("Meeting %s: ambiguous request, not routed: %r", meeting_uuid, text)
        return

    logger.warning("TRACE Meeting %s: about to push_avatar_state(thinking)", meeting_uuid)
    await panel_feed.push_avatar_state(meeting_uuid, "thinking")
    logger.warning("TRACE Meeting %s: about to push_topic_detected", meeting_uuid)
    await panel_feed.push_topic_detected(meeting_uuid, fields.location, fields.technology,
                                          fields.time_window)
    logger.warning("TRACE Meeting %s: about to submit_investigation", meeting_uuid)

    response = await zoom_channel_client.submit_investigation(
        meeting_uuid, source, text, fields.location, fields.technology, fields.time_window)
    logger.warning("TRACE Meeting %s: submit_investigation -> %s", meeting_uuid, response)

    if not response.get("accepted"):
        # T023: no registered tooling / Border unreachable — surfaced plainly.
        await panel_feed.push_avatar_state(meeting_uuid, "listening")
        await panel_feed.push_investigation_result(
            meeting_uuid, request_id="", answer_summary=None, evidence_refs=[])
        logger.warning("Meeting %s: investigation not accepted: %s", meeting_uuid,
                       response.get("reason"))
        return

    request_id = response.get("request_id")
    session = registry.get(meeting_uuid)
    if session and request_id in session.investigations:
        pass  # already created by submit path in a fuller implementation
    elif session:
        req = session.new_investigation(source=source, raw_text=text, location=fields.location,
                                          technology=fields.technology,
                                          time_window=fields.time_window)
        session.investigations[request_id] = session.investigations.pop(req.request_id)
        session.investigations[request_id].request_id = request_id

    await panel_feed.push_avatar_state(meeting_uuid, "investigating")


def handle_investigate_result(params: dict):
    """Registered as zoom_channel_client.on_investigate_result. Runs the
    panel-facing side of a Border push (research.md R1/R3)."""
    meeting_uuid = None
    for session in registry.list_active():
        if params.get("request_id") in session.investigations:
            meeting_uuid = session.meeting_uuid
            req = session.investigations[params["request_id"]]
            req.routing_outcome = params.get("routing_outcome")
            req.answer_summary = params.get("answer_summary")
            req.evidence_refs = params.get("evidence_refs", [])
            req.write_action_detected = params.get("write_action_detected", False)
            req.approval_ref = params.get("approval_ref")
            break
    if not meeting_uuid:
        logger.warning("investigate_result for unknown request_id %s", params.get("request_id"))
        return
    # The interim "looking into it" ack (routing_outcome="in_progress") reuses
    # this exact push path — must not flip the avatar to "answered" early, or
    # the whole point of showing progress is defeated.
    if params.get("routing_outcome") != "in_progress":
        asyncio.create_task(panel_feed.push_avatar_state(meeting_uuid, "answered"))
    asyncio.create_task(panel_feed.push_investigation_result(
        meeting_uuid, params.get("request_id"), params.get("answer_summary"),
        params.get("evidence_refs")))
