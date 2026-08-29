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
import importlib.util
import json
import os
import pathlib
import re
import sys


def _load_needs_cwd():
    """NetClaw's own cwd predicate, reused rather than restated.

    Two copies of "does this entry need a cwd?" would drift, and the failure
    when they do is silent: a server that will not start is indistinguishable
    from one that has no tools. Loaded by path because the script's filename
    contains hyphens and cannot be imported by name.
    """
    path = (pathlib.Path(__file__).resolve().parent.parent
            / "scripts" / "normalize-mcp-cwd.py")
    spec = importlib.util.spec_from_file_location("_netclaw_mcp_cwd", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.needs_cwd


try:
    needs_cwd = _load_needs_cwd()
except (OSError, AttributeError, ImportError):
    # The projection still works; entries just keep whatever cwd they had,
    # and the report records that the pass did not run.
    needs_cwd = None

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

#: A read-only triage claw. NetClaw registers a hundred-odd MCP servers; a
#: small open-weights model handed all of them spends its whole context on a
#: tool catalogue it cannot use. This is the "member claw" scope.
#:
#: THE RULE FOR THIS LIST: every entry runs entirely on this box and needs no
#: SaaS credential. That was already the stated rule and two entries broke it,
#: which is why each line now says what makes it local. A server that cannot
#: start contributes nothing to the catalogue AND is indistinguishable, in the
#: generated workflows, from a tool the agent simply chose not to call.
#:
#: REMOVED 2026-08-29, both verified by executing them:
#:   suzieq-mcp  refuses to start without SUZIEQ_API_URL and SUZIEQ_API_KEY
#:               ("Missing required environment variables"). It is a client for
#:               a separately-hosted SuzieQ service, not a local tool, and the
#:               placeholders for those keys resolved EMPTY.
#:   gait-mcp    its server package `mcp-servers/gait_mcp/` does not exist in
#:               this fork. `scripts/gait-stdio.py` inserts that directory on
#:               sys.path and imports `gait_mcp` from it, so the server dies
#:               with ModuleNotFoundError no matter how the venv is set up.
#:               Installing the GAIT venv (which this session did) fixes the
#:               `gait` import and gets you exactly one line further.
TRIAGE_TOOLS = [
    "multivendor-cli-mcp",  # netmiko/pyATS against the local FRR+sshd lab container
    "batfish-mcp",          # offline config analysis; the strongest local verifier
    "protocol-mcp",         # BGP/OSPF participation against the local FRR testbed
    "analysis-mcp",         # queries local files only
    "packet-buddy-mcp",     # local pcap, no device and no credential
    "memory-mcp",           # a local SQLite store
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
    command = str(entry["command"])
    # A bare `python3` resolves to whatever is first on PATH -- the SYSTEM
    # interpreter, which has none of this project's dependencies. Every server
    # spelled that way died at import with `No module named 'mcp'` and the
    # host reported only `MCP error -32000: Connection closed`, so the agent
    # came up with the framework's built-in tools alone. That failure is the
    # dangerous shape: a plausible catalogue that is the wrong one, which no
    # downstream gate can tell from a real one.
    #
    # Rewritten here rather than in the repo's config so no absolute path off
    # one machine is committed. A server that names its own interpreter (an
    # explicit venv, node, uvx, docker) is left exactly as it was.
    if command in ("python", "python3"):
        command = shim_python
    inner = [command, *(str(a) for a in entry.get("args") or [])]
    args = [shim_path]
    if predicates:
        args += ["--predicates", predicates]
    out["command"] = shim_python
    out["args"] = [*args, "--", *inner]
    return out


_ENV_PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def _expand_env_value(value: str, source: dict) -> tuple[str, bool]:
    """Expand ``${NAME}`` / ``${NAME:-default}`` and a leading ``~``.

    THE HOST SPAWNS MCP SERVERS DIRECTLY, WITHOUT A SHELL. So a config value
    written in shell syntax arrives at the server VERBATIM, and what happens
    next depends only on what the server does with it:

      * a server that parses it dies -- ``int('${BATFISH_PORT:-9997}')``
        raises, the host reports "MCP error -32000: Connection closed" with no
        cause, and the agent comes up without that tool;
      * a server that does NOT parse it survives and is WORSE, because it
        quietly uses the literal string -- the memory server took
        ``${MEMORY_DATA_DIR:-~/.openclaw/memory}`` as a directory NAME and
        created it.

    Returns the expanded value and whether anything was substituted.
    """
    changed = False

    def _sub(m: "re.Match[str]") -> str:
        nonlocal changed
        changed = True
        name, default = m.group(1), m.group(2)
        return source.get(name) or (default if default is not None else "")

    out = _ENV_PLACEHOLDER.sub(_sub, value)
    if out.startswith("~"):
        expanded = os.path.expanduser(out)
        changed = changed or expanded != out
        out = expanded
    return out, changed


def _expand_server_env(servers: dict) -> dict:
    """Expand every server's ``env`` in place; report what moved."""
    expanded, emptied = [], []
    for name, entry in servers.items():
        env = entry.get("env") if isinstance(entry, dict) else None
        if not isinstance(env, dict):
            continue
        for key, value in list(env.items()):
            if not isinstance(value, str):
                continue
            new, changed = _expand_env_value(value, os.environ)
            if not changed:
                continue
            env[key] = new
            expanded.append(f"{name}.{key}")
            # An empty result is not the same as a successful expansion: it
            # means neither the environment nor a default supplied anything,
            # and the server will see "". Named so a thin trajectory can be
            # explained rather than guessed at.
            if new == "":
                emptied.append(f"{name}.{key}")
    return {"expanded": len(expanded), "resolved_empty": sorted(emptied)}


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
    predicates: str | None = None, plugin_path: str | None = None,
    repo_root: str | None = None,
) -> tuple[dict, dict]:
    """Return (derived config, a report of what changed)."""
    report: dict = {}

    # ── 0. the flywheel plugin ────────────────────────────────────────────
    # This run redirects OPENCLAW_STATE_DIR to its own home, and a redirected
    # state directory stops the host discovering globally installed plugins
    # ("plugin not found … stale config entry ignored"). So the path has to be
    # named here or the plugin is simply absent from every rollout.
    #
    # `allowConversationAccess` is the second half and is just as load-bearing:
    # `llm_input` is a CONVERSATION hook, and the host silently REFUSES to
    # register one for a non-bundled plugin without this opt-in. Without it the
    # plugin loads, the tool-outcome recorder works, and the agent is never
    # described -- a failure that looks exactly like a healthy install.
    if plugin_path:
        plugins = cfg.setdefault("plugins", {})
        paths = plugins.setdefault("load", {}).setdefault("paths", [])
        if plugin_path not in paths:
            paths.append(plugin_path)
        plugins.setdefault("entries", {})["percepteye-agent-flywheel"] = {
            "enabled": True,
            "hooks": {"allowConversationAccess": True},
        }
        report["flywheel_plugin"] = plugin_path
    else:
        # Recorded, never silent: a rollout with no plugin produces no tool
        # outcomes and no description, and the report is where that gets
        # explained afterwards.
        report["flywheel_plugin"] = None

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

    # ── 7. give every relative-path server an explicit cwd ────────────────
    # The host does NOT spawn MCP servers in the directory it was launched
    # from, so an entry whose script path is relative ("mcp-servers/x/y.py")
    # resolves against the wrong directory and dies. The host reports only
    # "MCP error -32000: Connection closed", and the agent then comes up with
    # the framework's BUILT-IN tools alone -- a catalogue that is complete,
    # plausible, and the wrong one.
    #
    # `needs_cwd` is NetClaw's own predicate (scripts/normalize-mcp-cwd.py),
    # reused rather than restated so the two cannot drift. Entries that
    # already declare a cwd, or that name only absolute paths, are untouched.
    key_name, servers = _tools_key(cfg)
    if repo_root and servers is not None and needs_cwd is not None:
        repo = pathlib.Path(repo_root).resolve()
        scoped = []
        for k, v in servers.items():
            if isinstance(v, dict) and needs_cwd(v, repo):
                v["cwd"] = str(repo)
                scoped.append(k)
        report["cwd_scoped"] = sorted(scoped)
    elif repo_root and needs_cwd is None:
        report["cwd_scoped"] = None      # the pass could not run; not "none needed"

    # ── 8. expand shell-style env placeholders ────────────────────────────
    # Done LAST so it covers whatever survived scoping, and after wrapping so
    # the shim's own argv is already settled. See `_expand_env_value` for why
    # leaving these literal is worse than a crash.
    if servers is not None:
        report["env_expansion"] = _expand_server_env(servers)

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
