#!/usr/bin/env python3
"""The last mile: point this agent at what training produced.

    ./percepteye/apply_policy.py --agent-id netgeniusclaw-triage
    openclaw gateway restart

`apply_current_policy` returns kwargs shaped for an OpenAI client, which is
useless to an agent that reads its model from a config FILE. So this writes the
provider block instead -- the same projection a rollout uses, pointed at the
deployed policy rather than a per-rollout gateway.

Two rules it will not break:

* An empty answer means KEEP YOUR CURRENT CONFIGURATION. The control plane
  having nothing deployed, or being unreachable, must never leave this agent
  pointed at something guessed.
* It writes only where told, and prints a diff first unless `--write` is given.
  Editing the config an agent is serving from is not a side effect to take
  quietly.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from project_config import project  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent-id", required=True)
    ap.add_argument("--config", default=str(HERE.parent / "config" / "openclaw.json"))
    ap.add_argument("--write", action="store_true", help="apply; otherwise print what would change")
    a = ap.parse_args()

    try:
        import percepteye_agent_flywheel as fw
    except ImportError:
        print("percepteye-agent-flywheel is not installed:\n"
              "    pip install -r percepteye/requirements.txt", file=sys.stderr)
        return 3

    kw = fw.apply_current_policy(agent_id=a.agent_id)
    if not kw:
        print("Nothing deployed, or the control plane could not answer. "
              "Keeping the current configuration.")
        return 0

    path = pathlib.Path(a.config)
    cfg = json.loads(path.read_text(encoding="utf-8"))
    before = (cfg.get("agents", {}).get("defaults", {}).get("model", {}) or {}).get("primary")

    cfg, _ = project(
        cfg, provider="percepteye", base_url=kw["base_url"], key=kw["api_key"],
        model=kw["model"] or "policy", ctx=131072, max_tokens=16384,
        keep_tools=None,          # the last mile changes the MODEL, never the tool set
        shim_python=None, shim_path=None,   # and never the shim wiring
    )
    after = cfg["agents"]["defaults"]["model"]["primary"]

    print(f"  model:   {before}  ->  {after}")
    print(f"  endpoint: {kw['base_url']}")
    if not a.write:
        print("\nDry run. Re-run with --write to apply, then: openclaw gateway restart")
        return 0
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {path}. Now restart the gateway:  openclaw gateway restart")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
