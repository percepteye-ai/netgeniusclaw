#!/usr/bin/env python3
"""Project NetClaw's OpenClaw config onto an open-weights, OpenAI-compatible model.

The customer's agent is NEVER modified. This reads their config and writes a
DERIVED copy elsewhere; the source is opened read-only. That is deliberate --
it is the file-level analogue of the flywheel SDK's ``build_child_env()``, and
this script is the working prototype of the ``JsonConfigHost`` projection the
SDK needs.

Two uses, one transform:

  # 1. run NetClaw on a local open-weights model (LM Studio on a Mac)
  ./project_config.py --server lmstudio --model qwen/qwen3.5-9b -o ~/nc-open.json

  # 2. run ONE rollout against the percepteye per-rollout gateway
  ./project_config.py --server percepteye \
      --base-url "$OPENAI_BASE_URL" --api-key "$OPENAI_API_KEY" \
      --model "$PE_POLICY_MODEL" -o "$PERCEPTEYE_TRAJECTORY_DIR/openclaw.json"

Then point OpenClaw at the result -- it honours both of these
(scripts/in2n-migrate.py:96-104):

  export OPENCLAW_CONFIG_PATH=<out>  OPENCLAW_STATE_DIR=<dir of out>

Schema verified against openclaw 2026.7.1-2's own docs, not assumed:
  docs/providers/{litellm,vllm,lmstudio,sglang,ollama}.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# ── Servers that speak the wire our gateway speaks ────────────────────────
# `api` is OpenClaw's provider discriminator. `openai-completions` is the one
# value that means "an arbitrary OpenAI-compatible /v1 endpoint" -- vLLM,
# LM Studio, SGLang and LiteLLM all declare it, and so does the percepteye
# per-rollout gateway by construction.
#
# OLLAMA IS DELIBERATELY ABSENT. OpenClaw drives Ollama over its NATIVE
# /api/chat (`api: "ollama"`), and its own doc warns that pointing it at
# Ollama's /v1 "breaks tool calling and models can emit raw tool-call JSON as
# plain text". An Ollama-shaped wire is a third shape the gateway cannot serve,
# so choosing it would quietly cost you every rollout. Use LM Studio on a Mac.
SERVERS = {
    "lmstudio":   {"base_url": "http://localhost:1234/v1", "key_env": "LM_API_TOKEN"},
    "vllm":       {"base_url": "http://127.0.0.1:8000/v1", "key_env": "VLLM_API_KEY"},
    "sglang":     {"base_url": "http://127.0.0.1:30000/v1", "key_env": "SGLANG_API_KEY"},
    "percepteye": {"base_url": None, "key_env": "OPENAI_API_KEY"},  # per-rollout, always explicit
}

#: A read-only triage claw. NetClaw registers 104 MCP servers; a small
#: open-weights model handed all of them spends its whole context on a tool
#: catalogue it cannot use. This is the "member claw" scope -- every entry
#: below runs entirely on your own box, with no SaaS credential.
TRIAGE_TOOLS = [
    "multivendor-cli-mcp",  # netmiko/pyATS against the FRR+sshd lab container
    "batfish-mcp",          # offline config analysis; the strongest local verifier
    "suzieq-mcp",           # network state over time
    "protocol-mcp",         # BGP/OSPF participation against the FRR testbed
    "analysis-mcp",
    "packet-buddy-mcp",     # local pcap, no device needed
    "memory-mcp",
    "gait-mcp",             # the audit trail NetClaw's rules require
]


def _wrap_with_shim(entry: dict, *, shim_python: str, shim_path: str,
                    predicates: str | None) -> dict | None:
    """One MCP registration, rewritten to run through the outcome shim.

    Returns None for an entry we cannot wrap, so the caller can COUNT it rather
    than pretend it was covered. A `url:` entry is the common case: an argv
    wrapper cannot wrap a URL.

    `env`, `cwd` and every other key are preserved untouched -- the wrapped
    server must see exactly the environment it saw before, or the shim becomes
    the reason a server that worked stops working. The shim runs under its OWN
    interpreter (the one with the SDK installed); the wrapped server keeps its
    own command, which is frequently node, uvx, npx or docker.
    """
    if "command" not in entry:
        return None
    out = dict(entry)
    inner = [str(entry["command"]), *(str(a) for a in entry.get("args") or [])]
    args = [shim_path]
    if predicates:
        args += ["--predicates", predicates]
    out["command"] = shim_python
    out["args"] = [*args, "--", *inner]
    return out


def _tools_key(cfg: dict) -> tuple[str, dict] | tuple[None, None]:
    """NetClaw's registry lives under one of two keys, and BOTH are valid.

    `config/openclaw.json` in the repo uses flat `mcpServers`; an installed
    `~/.openclaw/openclaw.json` uses nested `mcp.servers`. NetClaw's own
    `scripts/normalize-mcp-cwd.py:61` says it supports both, so a projection
    that handled only one would silently scope nothing on half of all installs.
    """
    if isinstance(cfg.get("mcpServers"), dict):
        return "mcpServers", cfg["mcpServers"]
    nested = cfg.get("mcp")
    if isinstance(nested, dict) and isinstance(nested.get("servers"), dict):
        return "mcp.servers", nested["servers"]
    return None, None


def project(
    cfg: dict, *, provider: str, base_url: str, key: str, model: str,
    ctx: int, max_tokens: int, keep_tools: list[str] | None,
    shim_python: str | None = None, shim_path: str | None = None,
    predicates: str | None = None,
) -> tuple[dict, dict]:
    """Return (derived config, a report of what changed)."""
    report: dict = {}

    # ── 1. register the provider ──────────────────────────────────────────
    cfg.setdefault("models", {}).setdefault("providers", {})[provider] = {
        "baseUrl": base_url,
        "apiKey": key,
        "api": "openai-completions",
        "models": [{
            "id": model, "name": model, "reasoning": False,
            "input": ["text"], "contextWindow": ctx, "maxTokens": max_tokens,
        }],
        # A LAN or Tailscale endpoint sends the API key to a private host, so
        # OpenClaw refuses it unless this is set. Loopback does not need it,
        # but setting it unconditionally is wrong -- it would also permit a
        # private-network endpoint nobody chose.
        **({"request": {"allowPrivateNetwork": True}}
           if not _is_loopback(base_url) else {}),
    }

    ref = f"{provider}/{model}"
    defaults = cfg.setdefault("agents", {}).setdefault("defaults", {})

    # ── 2. route to it, and REMOVE the fallback ───────────────────────────
    # A fallback is an off-gateway escape hatch: under a rollout it would let
    # the agent sample Anthropic live the moment the policy endpoint hiccups,
    # producing a trajectory that cannot back an on-policy objective while
    # looking exactly like one that can.
    prev = defaults.get("model") or {}
    defaults["model"] = {"primary": ref}
    report["model"] = {"was": prev.get("primary"), "now": ref,
                       "fallbacks_dropped": list(prev.get("fallbacks") or [])}

    # ── 3. whitelist it ───────────────────────────────────────────────────
    # NetClaw's own scripts/in2n-member-home.py:74-76: "the agent rejects a
    # --model override that isn't in its allow-list". Skipping this produces a
    # config that looks correct and refuses every turn.
    defaults.setdefault("models", {})[ref] = {"alias": "policy"}

    # ── 4. scope the tool catalogue ───────────────────────────────────────
    key_name, servers = _tools_key(cfg)
    if keep_tools is not None and servers is not None:
        keep = set(keep_tools)
        kept = {k: v for k, v in servers.items() if k in keep}
        missing = sorted(keep - set(servers))
        if key_name == "mcpServers":
            cfg["mcpServers"] = kept
        else:
            cfg["mcp"]["servers"] = kept
        report["tools"] = {"key": key_name, "before": len(servers),
                           "after": len(kept), "requested_but_absent": missing}
    elif servers is not None:
        report["tools"] = {"key": key_name, "before": len(servers), "after": len(servers)}
    else:
        report["tools"] = {"key": None, "note": "no MCP registry found in source"}

    # ── 5. route every stdio tool through the outcome shim ────────────────
    # Without this the shim is registered nowhere and observes nothing. It is
    # safe to leave in a config used outside a rollout: `record_tool_call` is a
    # no-op when PERCEPTEYE_ROLLOUT_ID is unset, so one config serves both.
    key_name, servers = _tools_key(cfg)
    if shim_python and shim_path and servers is not None:
        wrapped, unwrappable = {}, []
        for k, v in servers.items():
            w = _wrap_with_shim(v, shim_python=shim_python, shim_path=shim_path,
                                predicates=predicates) if isinstance(v, dict) else None
            if w is None:
                unwrappable.append(k)
                wrapped[k] = v          # left EXACTLY as it was, never dropped
            else:
                wrapped[k] = w
        if key_name == "mcpServers":
            cfg["mcpServers"] = wrapped
        else:
            cfg["mcp"]["servers"] = wrapped
        report["shimmed"] = len(wrapped) - len(unwrappable)
        report["unshimmable"] = sorted(unwrappable)

    # ── 6. count what a command shim could never observe ──────────────────
    # Reported, never assumed zero: an argv wrapper cannot wrap a `url:` entry.
    if servers is not None:
        remote = sorted(k for k, v in servers.items()
                        if isinstance(v, dict) and "command" not in v)
        in_scope = [k for k in remote if keep_tools is None or k in set(keep_tools)]
        report["unshimmable_remote_in_scope"] = in_scope

    return cfg, report


def _is_loopback(url: str) -> bool:
    return any(h in url for h in ("127.0.0.1", "localhost", "[::1]", "host.docker.internal"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="config/openclaw.json",
                    help="the customer's config. Opened READ-ONLY, never written.")
    ap.add_argument("--server", choices=sorted(SERVERS), default="lmstudio")
    ap.add_argument("--provider-id", default=None, help="defaults to --server")
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--model", required=True)
    ap.add_argument("--context-window", type=int, default=131072)
    ap.add_argument("--max-tokens", type=int, default=16384)
    ap.add_argument("--tools", choices=["all", "triage"], default="triage")
    ap.add_argument("--shim-python", default=None,
                    help="interpreter that has percepteye-agent-flywheel installed. "
                         "Enables outcome capture; without it no tool is wrapped.")
    ap.add_argument("--shim-path", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "mcp_shim.py"))
    ap.add_argument("--predicates", default=None,
                    help="JSON file of per-tool verdict predicates. Absent, every "
                         "transport-clean result is recorded `unknown`.")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()

    spec = SERVERS[a.server]
    base_url = a.base_url or spec["base_url"]
    if not base_url:
        print(f"--base-url is required for --server {a.server} "
              f"(it is per-rollout and cannot have a default)", file=sys.stderr)
        return 2
    key = a.api_key or "${%s}" % spec["key_env"]

    with open(os.path.expanduser(a.source), encoding="utf-8") as fh:
        cfg = json.load(fh)

    cfg, report = project(
        cfg, provider=a.provider_id or a.server, base_url=base_url, key=key,
        model=a.model, ctx=a.context_window, max_tokens=a.max_tokens,
        keep_tools=None if a.tools == "all" else TRIAGE_TOOLS,
        shim_python=a.shim_python, shim_path=a.shim_path,
        predicates=os.path.abspath(os.path.expanduser(a.predicates))
        if a.predicates else None,
    )

    out = os.path.expanduser(a.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    os.chmod(out, 0o600)   # it carries a credential

    print(json.dumps({"source": a.source, "out": out, **report}, indent=2))
    print(f"\n  export OPENCLAW_CONFIG_PATH={out}", file=sys.stderr)
    print(f"  export OPENCLAW_STATE_DIR={os.path.dirname(out)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
