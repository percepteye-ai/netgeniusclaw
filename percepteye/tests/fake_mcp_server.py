"""A minimal MCP stdio server, for testing the shim against real frames.

Behaviour is selected by tool name so one server covers the whole verdict
table. It also answers `initialize` and `tools/list`, which the shim must
forward untouched and must NOT record.
"""
import json
import sys

BEHAVIOURS = {
    # ran, said so
    "tool_ok": lambda: {"content": [{"type": "text", "text": "done"}], "isError": False},
    # ran, raised
    "tool_error": lambda: {"content": [{"type": "text", "text": "exploded"}], "isError": True},
    # THE dangerous shape: transport-clean, operation refused
    "tool_silent_fail": lambda: {
        "content": [{"type": "text", "text": "% Invalid input detected at '^' marker."}],
        "isError": False,
    },
    # ran, said nothing either way
    "tool_no_verdict": lambda: {"content": [{"type": "text", "text": "42 routes"}]},
}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        req = json.loads(line)
        rid, method = req.get("id"), req.get("method")

        if method == "initialize":
            out = {"jsonrpc": "2.0", "id": rid,
                   "result": {"protocolVersion": "2026-03-26", "capabilities": {}}}
        elif method == "tools/list":
            # Two tools declare MCP's readOnlyHint and the rest declare
            # nothing, so a consumer can be tested on all three states:
            # declared-read, declared-write, and undeclared.
            _ann = {"tool_ok": True, "tool_error": False}
            out = {"jsonrpc": "2.0", "id": rid, "result": {"tools": [
                ({"name": n, "annotations": {"readOnlyHint": _ann[n]}}
                 if n in _ann else {"name": n})
                for n in BEHAVIOURS]}}
        elif method == "tools/call":
            name = (req.get("params") or {}).get("name")
            if name == "tool_jsonrpc_error":
                out = {"jsonrpc": "2.0", "id": rid,
                       "error": {"code": -32000, "message": "boom"}}
            elif name == "tool_crash":
                return 7          # die with the call outstanding
            else:
                out = {"jsonrpc": "2.0", "id": rid, "result": BEHAVIOURS[name]()}
        else:
            continue              # a notification; nothing to answer

        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
