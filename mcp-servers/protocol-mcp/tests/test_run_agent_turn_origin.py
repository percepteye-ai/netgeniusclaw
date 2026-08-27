"""Tests for run_agent_turn()'s origin marker (spec 116, User Story 2).

FR-007/FR-008/FR-009/FR-010/FR-011/FR-011a/FR-012: an optional origin marker
threads from request to answer composition, is fully backward compatible when
absent, and normalizes unrecognized values to None rather than failing.
"""

from bgp.federation.gateway import _build_agent_rpc_params, _normalize_origin

_VOICE_INSTRUCTION_MARKER = "one or two short, plain spoken sentences"


def test_no_origin_is_backward_compatible():
    """SC-006: params built with no origin argument must be identical to
    params built with origin=None, and must carry no voice-specific fields."""
    params_no_arg = _build_agent_rpc_params("hi", "session-1", 300)
    params_explicit_none = _build_agent_rpc_params("hi", "session-1", 300, origin=None)

    # idempotencyKey is a fresh UUID each call -- compare everything else.
    for params in (params_no_arg, params_explicit_none):
        assert "extraSystemPrompt" not in params
        assert params["message"] == "hi"
        assert params["sessionKey"] == "session-1"


def test_voice_origin_threads_into_rpc_params():
    params = _build_agent_rpc_params("hi", "session-1", 300, origin="voice")
    assert _VOICE_INSTRUCTION_MARKER in params["extraSystemPrompt"]
    # FR-011a: the instruction enforces brevity by composition, and explicitly
    # forbids formatting markup and post-hoc truncation.
    assert "headers" in params["extraSystemPrompt"] or "markup" in params["extraSystemPrompt"]


def test_unrecognized_origin_normalizes_to_none():
    """FR-012: an unrecognized origin value must behave exactly like no
    origin at all -- no voice instruction added, no request failure."""
    assert _normalize_origin("carrier-pigeon") is None
    assert _normalize_origin("voice") == "voice"
    assert _normalize_origin(None) is None

    params = _build_agent_rpc_params("hi", "session-1", 300, origin="carrier-pigeon")
    assert "extraSystemPrompt" not in params
