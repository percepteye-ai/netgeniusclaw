#!/usr/bin/env python3
"""One rollout: project a scoped config, run the agent, print its answer.

This is the argv handed to ``fw.serve``. The SDK spawns it once per rollout with
that rollout's endpoint in the environment, and everything it needs to do is a
consequence of one fact about this agent: **OpenClaw picks its model from
config, not from the environment.**

So the per-rollout ``OPENAI_BASE_URL`` the SDK sets does not win on its own. Left
alone, the agent would sample whatever its config names, the completions would
never reach the gateway, and the rollout would come back looking exactly like a
good one while backing nothing. That failure is silent, which is why this script
exists rather than a bare ``openclaw`` in the argv.

Each rollout therefore gets its OWN OpenClaw home, written into the rollout's
trajectory directory and thrown away with it. The customer's real config is
opened read-only and never touched.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

from capture import extract_reply          # noqa: E402
from describe_tools import enrich, is_describe_pass  # noqa: E402
from project_config import project         # noqa: E402

from percepteye_agent_flywheel.host_description import (  # noqa: E402
    openclaw_plugin_path,
)

#: Provider credentials removed from the child. The SDK strips the ones it
#: knows; this covers the agent's own config path, which it cannot see. An agent
#: that finds no provider must RAISE, in front of the operator, rather than
#: quietly reach a live endpoint nobody is capturing.
_STRIP = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY_REAL", "GEMINI_API_KEY", "GOOGLE_API_KEY")


def main() -> int:
    task = " ".join(sys.argv[1:]).strip() or os.environ.get("PERCEPTEYE_TURN_INPUT", "")
    if not task:
        task = sys.stdin.read().strip()
    if not task:
        print("no task text on argv, PERCEPTEYE_TURN_INPUT, or stdin", file=sys.stderr)
        return 2

    traj = os.environ.get("PERCEPTEYE_TRAJECTORY_DIR")
    if not traj:
        print("PERCEPTEYE_TRAJECTORY_DIR is unset — refusing to run a rollout whose "
              "outcomes would be written nowhere", file=sys.stderr)
        return 2
    base_url = os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not base_url or not api_key:
        print("OPENAI_BASE_URL / OPENAI_API_KEY are unset. The SDK sets both per "
              "rollout; without them this run would sample off-gateway.", file=sys.stderr)
        return 2

    home = pathlib.Path(traj) / "openclaw-home"
    home.mkdir(parents=True, exist_ok=True)

    with open(REPO / "config" / "openclaw.json", encoding="utf-8") as fh:
        cfg = json.load(fh)
    cfg, report = project(
        cfg,
        provider="percepteye", base_url=base_url, key=api_key,
        model=os.environ.get("PERCEPTEYE_POLICY_MODEL", "policy"),
        ctx=131072, max_tokens=16384,
        keep_tools=_tool_scope(),
        shim_python=sys.executable, shim_path=str(HERE / "mcp_shim.py"),
        predicates=str(HERE / "predicates.json"),
        # Resolved from the SDK rather than hardcoded, so no absolute path
        # off one machine ends up committed to this repo.
        plugin_path=openclaw_plugin_path(),
        # The host spawns MCP servers from its own directory, not this one,
        # so every relative script path needs an explicit cwd or the server
        # dies with only "Connection closed" to show for it.
        repo_root=str(REPO),
    )
    cfg_path = home / "openclaw.json"
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    cfg_path.chmod(0o600)
    # The report is evidence, not chatter: it records how many tools this rollout
    # could actually observe, so a thin trajectory can be explained afterwards.
    (home / "projection.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    env = dict(os.environ)
    for name in _STRIP:
        env.pop(name, None)
    env["OPENCLAW_CONFIG_PATH"] = str(cfg_path)
    env["OPENCLAW_STATE_DIR"] = str(home)

    rollout_id = os.environ.get("PERCEPTEYE_ROLLOUT_ID", "rollout")
    msg = home / "task.txt"
    msg.write_text(task, encoding="utf-8")     # --message-file dodges ARG_MAX

    cmd = [os.environ.get("OPENCLAW_BIN", "openclaw"), "agent", "--local", "--json",
           _session_flag(), rollout_id, "--message-file", str(msg)]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env,
                          cwd=str(REPO), timeout=float(os.environ.get(
                              "PERCEPTEYE_ROLLOUT_TIMEOUT_S", "870")))
    if proc.stderr:
        sys.stderr.write(proc.stderr)

    # On a DESCRIBE pass, add what the host's hook structurally cannot see.
    # `llm_input.tools` carries the built-in tools only -- MCP tools are
    # bridged in after the hook -- so a description left as-is would name a
    # general-purpose coding assistant rather than this agent. See
    # describe_tools.py. Never on a graded rollout: it costs a spawn per
    # server, and the description is already registered by then.
    described = pathlib.Path(traj) / "discovered_agent.json"
    if is_describe_pass() and described.is_file():
        merged = enrich(described, cfg_path)
        if merged is not None:
            n = merged.get("tool_definitions") or []
            print(f"[percepteye] description enriched: {len(n)} tool(s) total",
                  file=sys.stderr)

    reply = extract_reply(proc.stdout)
    if reply is None:
        # Say nothing rather than echo the raw envelope: a report whose final
        # text is a JSON blob grades as if the agent answered in JSON.
        print("", end="")
        return proc.returncode or 1
    print(reply)
    return proc.returncode


def _tool_scope():
    """Which tools this rollout carries. ``None`` means all of them.

    The triage scope is the default because a small open-weights model handed a
    hundred tool schemas spends its context on a catalogue it cannot use. Widen
    it deliberately with PERCEPTEYE_ALL_TOOLS=1, knowing what that costs.
    """
    if os.environ.get("PERCEPTEYE_ALL_TOOLS"):
        return None
    from project_config import TRIAGE_TOOLS
    return TRIAGE_TOOLS


def _session_flag() -> str:
    """Builds differ: --session-id on some, --session-key on others.

    Declared through the environment rather than probed, because probing means
    running the binary twice per rollout and guessing wrong means every rollout
    dies identically at argument parsing.
    """
    return os.environ.get("OPENCLAW_SESSION_FLAG", "--session-id")


if __name__ == "__main__":
    raise SystemExit(main())
