#!/usr/bin/env python3
"""Phase 1: run a task list through the agent and grade its DECISIONS.

No control plane, no gateway, no GPU. Sets the two environment variables the
SDK's recorder reads, runs the agent once per task, then grades the trajectory
the shim wrote.

    ./capture.py --tasks tasks.json --out runs/2026-08-27 \
        --config ../percepteye/openclaw.open-weights.json

What comes out is a decision-regression suite: per task, which of NetClaw's own
safety rules its tool-call sequence honoured. That is worth having on its own,
and every later phase reads it as the baseline.

The agent command is a PARAMETER, not a constant. The default is NetClaw's
verified headless invocation, but a stub can be substituted, which is what
makes this testable without the real binary installed.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from decisions import FAIL, N_A, PASS, ToolRoles, grade  # noqa: E402

#: NetClaw's headless invocation, verified at
#: mcp-servers/protocol-mcp/bgp/federation/gateway.py:355-390. `{task}` and
#: `{session}` are substituted. Note the session flag differs by build
#: (--session-id vs --session-key); openclaw probes its own, so confirm yours.
DEFAULT_AGENT = ["openclaw", "agent", "--local", "--json",
                 "--session-id", "{session}", "-m", "{task}"]


def extract_reply(stdout: str) -> str | None:
    """The agent's answer out of an OpenClaw `--json` envelope.

    Mirrors NetClaw's own `_extract_reply`: the envelope is preceded by banner
    noise and may be followed by log lines, so every complete JSON object in
    the stream is collected and the NEWEST one carrying real reply text wins.
    Plugin JSON earlier in the stream must never masquerade as the answer.
    """
    objs, dec, i = [], json.JSONDecoder(), 0
    while i < len(stdout):
        j = stdout.find("{", i)
        if j < 0:
            break
        try:
            obj, end = dec.raw_decode(stdout, j)
            objs.append(obj)
            i = end
        except ValueError:
            i = j + 1
    for obj in reversed(objs):
        if not isinstance(obj, dict):
            continue
        for k in ("finalAssistantVisibleText", "finalAssistantRawText"):
            if isinstance(obj.get(k), str) and obj[k].strip():
                return obj[k]
        result = obj.get("result") if isinstance(obj.get("result"), dict) else obj
        parts = [p["text"] for p in (result.get("payloads") or [])
                 if isinstance(p, dict) and isinstance(p.get("text"), str)]
        if any(p.strip() for p in parts):
            return "\n".join(parts)
    return None


def read_trajectory(d: pathlib.Path) -> list[dict] | None:
    """``None`` when nothing was recorded — which is not a claim of zero calls."""
    f = d / "tool_calls.jsonl"
    if not f.exists():
        return None
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue          # one truncated line costs that line only
    return out


def run_task(task: dict, out_dir: pathlib.Path, roles: ToolRoles, *,
             agent: list[str], config: str | None, timeout: float) -> dict:
    tid = str(task["id"])
    traj = out_dir / tid
    traj.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["PERCEPTEYE_ROLLOUT_ID"] = tid
    env["PERCEPTEYE_TRAJECTORY_DIR"] = str(traj)
    if config:
        env["OPENCLAW_CONFIG_PATH"] = os.path.abspath(config)
        env["OPENCLAW_STATE_DIR"] = os.path.dirname(os.path.abspath(config))
    # An agent that finds no provider must RAISE rather than reach a live one.
    env.pop("ANTHROPIC_API_KEY", None)

    cmd = [a.replace("{task}", task["prompt"]).replace("{session}", tid)
           for a in agent]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, env=env,
                           timeout=timeout)
        stdout, code, timed_out = p.stdout, p.returncode, False
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or "") if isinstance(e.stdout, str) else ""
        code, timed_out = None, True

    calls = read_trajectory(traj)
    g = grade(calls, roles)
    return {
        "id": tid,
        "exit_code": code,
        "timed_out": timed_out,
        "reply": extract_reply(stdout),
        # Absence survives: None means nothing was recorded, which is a
        # different fact from an observed zero.
        "tool_calls": None if calls is None else len(calls),
        "unknown_calls": None if calls is None
        else sum(1 for c in calls if c.get("outcome") == "unknown"),
        "score": g.score,
        "verdicts": [{"rule": v.rule, "outcome": v.outcome, "detail": v.detail,
                      "at": list(v.at)} for v in g.verdicts],
    }


def _load_roles(path: str | None) -> ToolRoles:
    """ToolRoles from JSON, ignoring `_`-prefixed provenance keys.

    A roles file people are meant to edit needs room for comments explaining
    what each role means; JSON has none, so `_README` carries them and is
    skipped here rather than exploding on an unexpected keyword.
    """
    if not path:
        return ToolRoles()
    raw = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    return ToolRoles(**{k: tuple(v) for k, v in raw.items() if not k.startswith("_")})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=None, help="projected OpenClaw config")
    ap.add_argument("--roles", default=None, help="JSON ToolRoles for grading")
    ap.add_argument("--agent", default=None,
                    help="JSON list overriding the agent argv, for testing")
    ap.add_argument("--timeout", type=float, default=900.0)
    a = ap.parse_args(argv)

    spec = json.loads(pathlib.Path(a.tasks).read_text())
    roles = _load_roles(a.roles)
    agent = json.loads(a.agent) if a.agent else DEFAULT_AGENT
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    results = [run_task(t, out, roles, agent=agent, config=a.config,
                        timeout=a.timeout) for t in spec["tasks"]]
    (out / "report.json").write_text(json.dumps({"results": results}, indent=2))

    print(f"{'task':<26}{'calls':>7}{'unk':>5}{'score':>8}  failing rules")
    for r in results:
        failed = [v["rule"] for v in r["verdicts"] if v["outcome"] == FAIL]
        score = "—" if r["score"] is None else f"{r['score']:.2f}"
        calls = "—" if r["tool_calls"] is None else r["tool_calls"]
        unk = "—" if r["unknown_calls"] is None else r["unknown_calls"]
        print(f"{r['id']:<26}{calls:>7}{unk:>5}{score:>8}  {', '.join(failed) or '-'}")

    graded = [r for r in results if r["score"] is not None]
    print(f"\n{len(graded)}/{len(results)} gradable"
          + (f" · mean {sum(r['score'] for r in graded)/len(graded):.2f}"
             if graded else " · nothing gradable"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
