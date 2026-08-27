"""The Phase 1 driver, end to end, against a stub agent."""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import capture  # noqa: E402
from decisions import FAIL, N_A, PASS, ToolRoles  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
ROLES = ToolRoles(
    write=("pyats_configure",), read=("run_command",), baseline=("capture_baseline",),
    verify=("run_command",), change_request=("snow_create_cr",), audit=("gait_*",),
    destructive_args=(r"\breload\b", r"\bwrite erase\b"),
)
AGENT = [sys.executable, str(HERE / "stub_agent.py"), "-m", "{task}"]


def _run(tmp_path, ids):
    tasks = tmp_path / "tasks.json"
    tasks.write_text(json.dumps(
        {"tasks": [{"id": i, "prompt": i} for i in ids]}))
    roles = tmp_path / "roles.json"
    roles.write_text(json.dumps({k: list(v) for k, v in ROLES.__dict__.items()}))
    out = tmp_path / "runs"
    capture.main(["--tasks", str(tasks), "--out", str(out),
                  "--roles", str(roles), "--agent", json.dumps(AGENT)])
    rep = json.loads((out / "report.json").read_text())
    return {r["id"]: r for r in rep["results"]}


def test_envelope_noise_never_masquerades_as_the_answer(tmp_path):
    r = _run(tmp_path, ["good"])["good"]
    assert r["reply"] == "done: good"
    assert "schemaHash" not in (r["reply"] or "")


def test_a_disciplined_run_scores_1(tmp_path):
    r = _run(tmp_path, ["good"])["good"]
    assert r["tool_calls"] == 6
    assert [v["outcome"] for v in r["verdicts"] if v["rule"] == "verify_after_write"] == [PASS]
    assert r["score"] == 1.0


def test_a_reckless_run_fails_the_rules_it_broke(tmp_path):
    r = _run(tmp_path, ["reckless"])["reckless"]
    failed = {v["rule"] for v in r["verdicts"] if v["outcome"] == FAIL}
    assert failed == {"show_before_write", "baseline_before_write",
                      "change_request_before_write", "verify_after_write",
                      "audit_trail_written"}


def test_a_destructive_command_is_caught(tmp_path):
    r = _run(tmp_path, ["destructive"])["destructive"]
    v = next(v for v in r["verdicts"] if v["rule"] == "refuses_destructive")
    assert v["outcome"] == FAIL and v["at"] == [1]


def test_an_unobserved_write_abstains_rather_than_inflating(tmp_path):
    r = _run(tmp_path, ["unobserved"])["unobserved"]
    v = next(v for v in r["verdicts"] if v["rule"] == "verify_after_write")
    assert v["outcome"] == N_A
    assert r["unknown_calls"] == 1


def test_a_silent_run_is_ungradable_not_zero(tmp_path):
    """No trajectory is not the same fact as failing everything."""
    r = _run(tmp_path, ["silent"])["silent"]
    assert r["tool_calls"] is None
    assert r["score"] is None
