#!/usr/bin/env python3
"""Donate capacity: claim rollouts from the control plane and run them here.

    export PERCEPTEYE_CONTROL_PLANE_URL="https://.../api/flywheel/v1"
    export PERCEPTEYE_API_KEY="pek_..."
    ./percepteye/serve.py --agent-id netgeniusclaw-triage --max-rollouts 5

Bounded by default. `serve()` is not a dry run: every rollout is a task the
control plane generated, executed by this agent, with whatever credentials this
environment carries. Point it at the lab, not at production.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent-id", required=True)
    ap.add_argument("--max-rollouts", type=int, default=5,
                    help="bound the first run; None only once you trust it")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--artifacts-dir", default="/var/tmp/percepteye-artifacts",
                    help="deliberately outside any source tree")
    a = ap.parse_args()

    try:
        import percepteye_agent_flywheel as fw
    except ImportError:
        print("percepteye-agent-flywheel is not installed:\n"
              "    pip install -r percepteye/requirements.txt", file=sys.stderr)
        return 3

    return fw.serve(
        [sys.executable, str(HERE / "rollout_runner.py"), fw.TASK],
        agent_id=a.agent_id,
        input_shape="text",
        # ASSERTED, and true only because the MCP shim writes per-call outcomes.
        # Setting this without the shim wired would be the same class of lie the
        # tri-state exists to prevent.
        reports_tool_calls=True,
        # No Python agent object to bind to -- this agent is a process.
        adapters=[],
        concurrency=a.concurrency,
        artifacts_dir=a.artifacts_dir,
        max_rollouts=a.max_rollouts,
        on_event=lambda kind, ev: print(f"[{kind}] {ev.get('rollout_id', '')}"),
    )


if __name__ == "__main__":
    raise SystemExit(main())
