"""Enrich the host's agent description with the MCP tool catalogue.

WHY THIS IS NEEDED, AND WHY IT IS NOT IN THE PLUGIN
---------------------------------------------------
The flywheel plugin describes the agent from OpenClaw's ``llm_input`` hook,
which carries the assembled system prompt, the model config, and a ``tools``
list. That list is NOT the list the model receives. Measured on this agent,
against a recording endpoint:

    llm_input.tools          38   the built-in tools only
    the actual wire request  85   the same 38, plus 47 MCP tools

MCP-bridged tools are attached AFTER the hook runs, and ``tools`` appears on
exactly one hook type in the whole plugin API (``llm_input``), so no hook can
see them. The plugin cannot close this gap; nothing inside it can.

The gap matters more than the numbers suggest. For a triage agent the MCP
tools ARE the agent -- `batfish_test_reachability`, `bgp_get_peers`,
`analysis_query`. A description carrying only the built-ins is complete,
well-formed, plausible, and describes a general-purpose coding assistant.
Workflows generated from it would exercise `read` and `edit`; reward suites
would be written against those; and the training corpus would be about the
wrong agent entirely. Nothing downstream can detect this: the catalogue is
non-empty, so every gate passes.

So the catalogue is read from the servers themselves, which is the only
authoritative source. Each server is asked for `tools/list` over the same
stdio transport and the same shim the agent uses, so what is reported is what
the agent could actually call -- not what a config file claims.

WHEN IT RUNS
------------
Only on a DESCRIBE pass, identified by ``PERCEPTEYE_ROLLOUT_ID`` being unset:
the SDK sets that variable for every real rollout and not for the warm-up
invocation it makes at startup. Spawning every server costs seconds, which is
worth paying once at registration and not on each graded rollout.
"""
from __future__ import annotations

import json
import os
import pathlib
import queue
import subprocess
import threading
import time

#: The MCP name separator OpenClaw uses when it bridges a server's tools into
#: the agent's namespace: ``<server>__<tool>``. Verified against the tool names
#: in a recorded model request, not assumed -- a mismatch here would produce a
#: catalogue of names the agent cannot actually call.
NAME_SEPARATOR = "__"

_INIT = {
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
               "clientInfo": {"name": "percepteye-describe", "version": "1"}},
}
_INITIALIZED = {"jsonrpc": "2.0", "method": "notifications/initialized"}
_LIST = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}


def _ask_server(name: str, entry: dict, *, timeout_s: float) -> list[dict]:
    """Ask one MCP server for its tools. Never raises; an error is an absence."""
    if not isinstance(entry, dict) or "command" not in entry:
        return []
    argv = [str(entry["command"]), *(str(a) for a in entry.get("args") or [])]
    env = dict(os.environ)
    env.update({k: str(v) for k, v in (entry.get("env") or {}).items()})

    try:
        proc = subprocess.Popen(
            argv, cwd=entry.get("cwd"), env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True,
            start_new_session=(os.name != "nt"),
        )
    except (OSError, ValueError):
        return []

    # Read INCREMENTALLY with a deadline, rather than writing everything and
    # waiting for the process to exit. A server that is slow to boot -- one
    # importing a large framework, say -- had not answered by the time a
    # write-then-EOF reader gave up, and its tools were silently missing from
    # the catalogue while the host's own probe (which waits properly) listed
    # twelve of them. The reader must outlast the slowest server, not the
    # fastest.
    lines: "queue.Queue[str | None]" = queue.Queue()

    def _pump() -> None:
        try:
            for line in proc.stdout:            # type: ignore[union-attr]
                lines.put(line)
        except (OSError, ValueError):
            pass
        finally:
            lines.put(None)

    reader = threading.Thread(target=_pump, daemon=True)
    reader.start()

    try:
        payload = "".join(json.dumps(m) + "\n" for m in (_INIT, _INITIALIZED, _LIST))
        proc.stdin.write(payload)               # type: ignore[union-attr]
        proc.stdin.flush()                      # type: ignore[union-attr]
    except (OSError, ValueError):
        proc.kill()
        return []

    out_lines: list[str] = []
    deadline = time.monotonic() + timeout_s
    try:
        while time.monotonic() < deadline:
            try:
                line = lines.get(timeout=0.2)
            except queue.Empty:
                if proc.poll() is not None:
                    break
                continue
            if line is None:
                break
            out_lines.append(line)
            if '"id":2' in line.replace(" ", "") or '"id": 2' in line:
                break
    finally:
        if proc.poll() is None:
            proc.kill()

    for line in out_lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if msg.get("id") != 2:
            continue
        tools = ((msg.get("result") or {}).get("tools")) or []
        return [
            {
                # Prefixed exactly as the host bridges it, so the name we
                # report is the name the agent can call.
                "name": f"{name}{NAME_SEPARATOR}{t['name']}",
                "description": str(t.get("description") or ""),
                "input_schema": t.get("inputSchema") or t.get("input_schema")
                                or {"type": "object", "properties": {}},
                "original_format": "openclaw_mcp",
            }
            for t in tools
            if isinstance(t, dict) and t.get("name")
        ]
    return []


def collect_mcp_tools(config_path: str | os.PathLike[str], *,
                      timeout_s: float = 30.0) -> tuple[list[dict], list[str]]:
    """Every MCP tool the agent could call, and the servers that did not answer.

    The unreachable list is returned rather than swallowed: a server that fails
    to start is indistinguishable, in the catalogue alone, from one that has no
    tools, and the difference decides whether a thin description is a fact
    about the agent or a fault in the environment.
    """
    try:
        cfg = json.loads(pathlib.Path(config_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return [], []

    servers = cfg.get("mcpServers")
    if not isinstance(servers, dict):
        nested = cfg.get("mcp")
        servers = nested.get("servers") if isinstance(nested, dict) else None
    if not isinstance(servers, dict):
        return [], []

    tools: list[dict] = []
    silent: list[str] = []
    for name, entry in servers.items():
        found = _ask_server(name, entry, timeout_s=timeout_s)
        if found:
            tools.extend(found)
        else:
            silent.append(name)
    return tools, sorted(silent)


def enrich(description_path: str | os.PathLike[str],
           config_path: str | os.PathLike[str]) -> dict | None:
    """Merge the MCP catalogue into a description the plugin already wrote.

    Returns the merged record, or None when there was nothing to enrich. The
    host-observed tools are kept and the MCP ones are ADDED: the built-ins are
    real tools the agent can call, and dropping them would trade one wrong
    catalogue for another.
    """
    path = pathlib.Path(description_path)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict):
        return None

    mcp_tools, silent = collect_mcp_tools(config_path)
    if not mcp_tools:
        # Recorded, not silent: "the host observed 38 tools" and "the host
        # observed 38 and every MCP server was unreachable" are different
        # facts, and only one of them is about the agent.
        if silent:
            record.setdefault("incomplete", [])
            if "mcp_tool_definitions" not in record["incomplete"]:
                record["incomplete"].append("mcp_tool_definitions")
            path.write_text(json.dumps(record), encoding="utf-8")
        return record

    observed = record.get("tool_definitions")
    existing = observed if isinstance(observed, list) else []
    seen = {t.get("name") for t in existing if isinstance(t, dict)}
    record["tool_definitions"] = existing + [
        t for t in mcp_tools if t["name"] not in seen
    ]
    if silent:
        record.setdefault("incomplete", [])
        if "mcp_tool_definitions" not in record["incomplete"]:
            record["incomplete"].append("mcp_tool_definitions")

    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(record), encoding="utf-8")
    tmp.replace(path)
    return record


def is_describe_pass() -> bool:
    """True when this invocation exists to describe, not to be graded.

    The SDK stamps ``PERCEPTEYE_ROLLOUT_ID`` on every real rollout and leaves
    it unset for the warm-up it runs before registering. Reusing that existing
    distinction avoids inventing a second switch that could disagree with it.
    """
    return not os.environ.get("PERCEPTEYE_ROLLOUT_ID")
