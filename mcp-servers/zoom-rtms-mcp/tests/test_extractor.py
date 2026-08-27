import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from extractor import classify, extract_fields  # noqa: E402


# ---- T015 (US1): happy-path recognition/extraction ------------------------

def test_spec_example_is_recognized_as_investigate():
    text = "It looks like Toronto lost its BGP sessions about ten minutes ago."
    assert classify(text).kind == "investigate"


def test_extracts_location_technology_time_window():
    text = "Toronto lost its BGP sessions about 10 minutes ago"
    fields = extract_fields(text)
    assert fields.location == "Toronto"
    assert fields.technology == "BGP"
    assert fields.time_window == "~10 minutes"


def test_direct_investigative_question_recognized():
    text = "NetClaw, can you check whether the Ottawa firewall is down?"
    assert classify(text).kind == "investigate"


def test_unrelated_chit_chat_not_recognized():
    text = "Good morning everyone, hope you all had a nice weekend."
    assert classify(text).kind == "none"


# ---- T026 (US4): safety-boundary classification ----------------------------

def test_hypothetical_suggestion_is_suppressed():
    text = "Maybe we should just shut that interface I guess"
    result = classify(text)
    assert result.kind == "suppressed"


def test_past_tense_third_party_is_suppressed():
    text = "They shut the interface down last time this happened"
    result = classify(text)
    assert result.kind == "suppressed"


def test_direct_write_command_is_write_command_not_suppressed():
    text = "shut interface Gi0/1 on EDGE-TOR-01"
    result = classify(text)
    assert result.kind == "write_command"


def test_direct_read_request_is_investigate_not_write():
    text = "can you check the BGP state on the Toronto router"
    result = classify(text)
    assert result.kind == "investigate"
