"""The shim's verdict table, and that capture never costs the call."""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import mcp_shim  # noqa: E402

SERVER = [sys.executable, str(HERE / "fake_mcp_server.py")]
SHIM = [sys.executable, str(HERE.parent / "mcp_shim.py")]

PREDICATES = {
    "tool_silent_fail": {"fail": [re.compile(r"% Invalid input")], "ok_if_no_fail": True},
    "tool_ok": {"fail": [], "ok_if_no_fail": True},
}


# ── the verdict table, as a pure function ─────────────────────────────────
@pytest.mark.parametrize("resp,tool,expected", [
    ({"result": {"isError": True, "content": [{"type": "text", "text": "x"}]}},
     "tool_error", "failed"),
    ({"error": {"code": -32000, "message": "boom"}}, "anything", "failed"),
    ({"result": {"isError": False, "content": [{"type": "text", "text": "done"}]}},
     "tool_ok", "ok"),
    # transport-clean, operation refused -> the whole point of the module
    ({"result": {"isError": False,
                 "content": [{"type": "text", "text": "% Invalid input detected"}]}},
     "tool_silent_fail", "failed"),
    # declared tool, no fail pattern hit -> ok
    ({"result": {"isError": False, "content": [{"type": "text", "text": "fine"}]}},
     "tool_silent_fail", "ok"),
    # UNDECLARED tool -> unknown, never ok
    ({"result": {"isError": False, "content": [{"type": "text", "text": "42 routes"}]}},
     "tool_no_verdict", "unknown"),
])
def test_verdict_table(resp, tool, expected):
    outcome, _, _ = mcp_shim.verdict_for(resp, tool, PREDICATES)
    assert outcome == expected


def test_isError_false_is_never_rounded_up_without_a_declaration():
    """`the tool ran` and `the operation succeeded` are different claims."""
    resp = {"result": {"isError": False, "content": [{"type": "text", "text": "ok!"}]}}
    assert mcp_shim.verdict_for(resp, "undeclared", {})[0] == "unknown"


def test_fail_pattern_beats_ok_if_no_fail():
    spec = {"x": {"fail": [re.compile("nope")], "ok_if_no_fail": True}}
    resp = {"result": {"isError": False, "content": [{"type": "text", "text": "nope"}]}}
    assert mcp_shim.verdict_for(resp, "x", spec)[0] == "failed"


def test_glob_predicates_match_but_exact_wins():
    spec = {
        "bf_*": {"fail": [re.compile("Traceback")], "ok_if_no_fail": True},
        "bf_exact": {"fail": [], "ok_if_no_fail": False},
    }
    body = {"result": {"isError": False, "content": [{"type": "text", "text": "fine"}]}}
    assert mcp_shim.verdict_for(body, "bf_other", spec)[0] == "ok"
    assert mcp_shim.verdict_for(body, "bf_exact", spec)[0] == "unknown"


# ── end to end, through a real subprocess pair ────────────────────────────
def _run(frames, tmp_path, *, rollout="r_test", predicates=None):
    env = dict(os.environ)
    env["PERCEPTEYE_TRAJECTORY_DIR"] = str(tmp_path)
    if rollout:
        env["PERCEPTEYE_ROLLOUT_ID"] = rollout
    else:
        env.pop("PERCEPTEYE_ROLLOUT_ID", None)

    cmd = list(SHIM)
    if predicates:
        p = tmp_path / "preds.json"
        p.write_text(json.dumps(predicates))
        cmd += ["--predicates", str(p)]
    cmd += ["--"] + SERVER

    proc = subprocess.run(
        cmd, input="".join(json.dumps(f) + "\n" for f in frames),
        capture_output=True, text=True, env=env, timeout=30,
    )
    traj = tmp_path / "tool_calls.jsonl"
    records = ([json.loads(x) for x in traj.read_text().splitlines() if x.strip()]
               if traj.exists() else None)
    return proc, records


def _call(i, name, args=None):
    return {"jsonrpc": "2.0", "id": i, "method": "tools/call",
            "params": {"name": name, "arguments": args or {}}}


def test_e2e_records_the_verdict_table(tmp_path):
    preds = {"tool_silent_fail": {"fail": ["% Invalid input"], "ok_if_no_fail": True},
             "tool_ok": {"ok_if_no_fail": True}}
    _, recs = _run([_call(1, "tool_ok"), _call(2, "tool_error"),
                    _call(3, "tool_silent_fail"), _call(4, "tool_no_verdict"),
                    _call(5, "tool_jsonrpc_error")],
                   tmp_path, predicates=preds)
    assert [r["name"] for r in recs] == [
        "tool_ok", "tool_error", "tool_silent_fail", "tool_no_verdict",
        "tool_jsonrpc_error"]
    assert [r["outcome"] for r in recs] == [
        "ok", "failed", "failed", "unknown", "failed"]
    # MCP is not HTTP: a status is never manufactured.
    assert all(r["status_code"] is None for r in recs)
    # and the id the MODEL assigned is absent, not guessed from the JSON-RPC id
    assert all("tool_call_id" not in r for r in recs)


def test_arguments_are_preserved_for_the_join(tmp_path):
    _, recs = _run([_call(1, "tool_ok", {"device": "R1", "cmd": "show ip bgp"})],
                   tmp_path, predicates={"tool_ok": {"ok_if_no_fail": True}})
    assert recs[0]["arguments"] == {"device": "R1", "cmd": "show ip bgp"}


def test_responses_reach_the_host_unmodified(tmp_path):
    """Capture must be invisible to the agent. Byte-for-byte passthrough."""
    frames = [{"jsonrpc": "2.0", "id": 0, "method": "initialize"},
              {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
              _call(2, "tool_ok")]
    proc, _ = _run(frames, tmp_path)
    direct = subprocess.run(
        SERVER, input="".join(json.dumps(f) + "\n" for f in frames),
        capture_output=True, text=True, timeout=30)
    assert proc.stdout == direct.stdout


def test_non_tools_call_frames_are_not_recorded(tmp_path):
    _, recs = _run([{"jsonrpc": "2.0", "id": 0, "method": "initialize"},
                    {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}], tmp_path)
    # None, not [] -- nothing was observed, which is not a claim of zero calls.
    assert recs is None


def test_transport_death_records_failed_not_lost(tmp_path):
    proc, recs = _run([_call(1, "tool_crash")], tmp_path)
    assert proc.returncode == 7                       # exit code propagates
    assert len(recs) == 1
    assert recs[0]["outcome"] == "failed"
    assert recs[0]["error_class"] == "mcp_transport_closed"


def test_outside_a_rollout_it_is_a_no_op(tmp_path):
    """Safe to leave registered permanently in a projected config."""
    proc, recs = _run([_call(1, "tool_ok")], tmp_path, rollout=None)
    assert recs is None
    assert proc.returncode == 0


def test_unparseable_server_output_costs_that_line_only(tmp_path):
    """A server that interleaves logging must not lose the outcomes around it."""
    import textwrap
    noisy = tmp_path / "noisy.py"
    noisy.write_text(textwrap.dedent("""
        import json, sys
        for line in sys.stdin:
            if not line.strip():
                continue
            rid = json.loads(line).get("id")
            sys.stdout.write("starting up, not json\\n")
            sys.stdout.write("{ this is not json either\\n")
            sys.stdout.write(json.dumps({"jsonrpc":"2.0","id":rid,
                "result":{"isError":False,"content":[{"type":"text","text":"ok"}]}})+"\\n")
            sys.stdout.flush()
    """))
    env = dict(os.environ, PERCEPTEYE_TRAJECTORY_DIR=str(tmp_path),
               PERCEPTEYE_ROLLOUT_ID="r_noise")
    p = tmp_path / "preds.json"
    p.write_text(json.dumps({"tool_ok": {"ok_if_no_fail": True}}))
    subprocess.run(SHIM + ["--predicates", str(p), "--", sys.executable, str(noisy)],
                   input=json.dumps(_call(1, "tool_ok")) + "\n",
                   capture_output=True, text=True, env=env, timeout=30)
    recs = [json.loads(x) for x in
            (tmp_path / "tool_calls.jsonl").read_text().splitlines() if x.strip()]
    assert [r["outcome"] for r in recs] == ["ok"]
