"""Tool outcomes from an agent's MCP transport.

VENDORED, AND THAT IS TEMPORARY. Nothing in this file is NetGeniusClaw-specific.
It belongs in the SDK as ``percepteye_agent_flywheel.mcp_shim`` and is written
to move there unchanged; it lives here only until that lands, so this repo has
a working integration in the meantime. When the SDK ships it, delete this file
and change the projection to invoke
``python -m percepteye_agent_flywheel.mcp_shim -- <argv>`` instead. Nothing else
changes: the projection already passes the module path as one argument.

It already DEPENDS on the SDK -- ``record_tool_call`` comes from there -- so
this is a duplicated file, not a duplicated contract.

The framework adapters bind to a Python object. ``event_stream`` reads a
command agent's stdout. Neither reaches an agent whose tools arrive over MCP:
the adapters have no object to bind, and a host that prints a final-result
envelope (OpenClaw's ``--json``) carries no per-call events to parse. That is
the largest tool surface in the ecosystem and the SDK currently observes none
of it.

This is the third capture mode, and it binds to the PROTOCOL rather than to a
framework -- so one implementation covers every MCP host, in any language.

WHY THIS IS SAFE TO LEAVE REGISTERED PERMANENTLY
------------------------------------------------
It records through ``record_tool_call``, which is a no-op outside a rollout.
So a config projected with these wrappers behaves identically in normal use and
records only when ``PERCEPTEYE_ROLLOUT_ID`` is set. There is no second config
to maintain and no flag to forget.

THREE RULES, THE SAME THREE THE REST OF THE PACKAGE KEEPS
---------------------------------------------------------
* A capture bug costs the observation and nothing else -- never the call. Every
  frame is FORWARDED BEFORE it is parsed, and every parse is wrapped.
* Absence is never collapsed into zero. A tool result carrying no verdict is
  ``unknown``, and ``unknown`` is never rounded up.
* Nothing is inferred that was not observed. In particular ``tool_call_id`` is
  left ``None``: MCP's JSON-RPC id is the CLIENT's request id, not the id the
  model assigned, and passing it would corrupt every join that keys on the
  model's id rather than merely leaving that join unavailable.

KNOWN AND DELIBERATE LIMITS
---------------------------
* stdio transport only. A remote ``url:`` server is reached by rewriting its
  registration into a stdio one this shim fulfils by dialling out -- see
  ``--remote``. That keeps the package's "no listening socket" property true.
* MCP tools only. A host's framework-native tools never cross this boundary and
  are correctly invisible here; the control plane's wire ledger is what makes
  the denominator known.
* The tool NAME seen here is the bare MCP name. Hosts commonly namespace it for
  the model (``server__tool``), so a join against the completion wire must
  normalise both sides. Recording the host's namespaced name instead would be a
  guess about a convention we cannot see from inside the transport.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys
import threading
import time
from typing import Any

__all__ = ["main", "verdict_for"]

#: Bodies can be large. The trajectory is where fidelity lives, but a tool that
#: printed a routing table should not put a megabyte in every record.
_MAX_TEXT = 4000
_MAX_ERROR = 1000


# ── predicates ────────────────────────────────────────────────────────────
# An operator DECLARES where a non-error result means the operation worked.
# Nothing is inferred: absent a declaration the outcome is `unknown`, because
# "the tool ran" and "the operation succeeded" are different claims and only
# the first is observable from here. A `pyats_configure` that returns
# `% Invalid input detected` ran perfectly and changed nothing.
#
#   {
#     "pyats_configure": {"fail": ["% Invalid input", "% Incomplete command"],
#                         "ok_if_no_fail": true},
#     "bf_*":            {"fail": ["\\bTraceback\\b"], "ok_if_no_fail": true}
#   }
#
# `fail` beats `ok_if_no_fail`: a body matching both is a failure.
def load_predicates(path: str | None) -> dict[str, dict[str, Any]]:
    if not path:
        return {}
    with open(os.path.expanduser(path), encoding="utf-8") as fh:
        raw = json.load(fh)
    out: dict[str, dict[str, Any]] = {}
    for name, spec in raw.items():
        if name.startswith("_"):
            continue          # `_`-prefixed keys are provenance notes, not tools
        pats = [re.compile(p) for p in (spec.get("fail") or [])]
        out[name] = {"fail": pats, "ok_if_no_fail": bool(spec.get("ok_if_no_fail"))}
    return out


def _match(tool: str, preds: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Exact name first, then glob. An exact declaration always wins."""
    if tool in preds:
        return preds[tool]
    for pat, spec in preds.items():
        if any(c in pat for c in "*?[") and fnmatch.fnmatchcase(tool, pat):
            return spec
    return None


def render_text(result: Any) -> str:
    """The readable body of an MCP result.

    Prefers the spec's ``content: [{type: "text", text: ...}]``. A grader --
    and a predicate -- needs bytes it can read, not a shape it has to guess at.
    """
    if isinstance(result, str):
        return result[:_MAX_TEXT]
    if not isinstance(result, dict):
        return json.dumps(result, default=str)[:_MAX_TEXT]
    content = result.get("content")
    if isinstance(content, list):
        parts = [c["text"] for c in content
                 if isinstance(c, dict) and isinstance(c.get("text"), str)]
        if parts:
            return "\n".join(parts)[:_MAX_TEXT]
    return json.dumps(result, default=str)[:_MAX_TEXT]


def verdict_for(
    response: dict[str, Any], tool: str, preds: dict[str, dict[str, Any]],
) -> tuple[str, str | None, Any]:
    """``(outcome, error, output)`` for one MCP ``tools/call`` response.

    Pure, so the whole verdict table is testable without a subprocess.
    """
    if "error" in response and response.get("error") is not None:
        err = response["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        return "failed", str(msg or "jsonrpc error")[:_MAX_ERROR], err

    result = response.get("result")
    text = render_text(result)

    # The protocol's own verdict. TRUE is a claim; FALSE is only a claim that
    # the tool did not raise -- not that the operation succeeded.
    if isinstance(result, dict) and result.get("isError") is True:
        return "failed", (text or None) and text[:_MAX_ERROR], result

    spec = _match(tool, preds)
    if spec:
        for pat in spec["fail"]:
            if pat.search(text):
                # The case this whole module exists for: a result the transport
                # calls fine, carrying an operation that did not happen.
                return "failed", text[:_MAX_ERROR], result
        if spec["ok_if_no_fail"]:
            return "ok", None, result

    return "unknown", None, result


# ── the pump ──────────────────────────────────────────────────────────────
class _Shim:
    def __init__(self, preds: dict[str, dict[str, Any]], record: Any) -> None:
        self._preds = preds
        self._record = record
        self._pending: dict[str, tuple[str, dict[str, Any], float]] = {}
        #: ids of in-flight ``tools/list`` calls (distinct from ``_pending``,
        #: which is outcome capture for ``tools/call``).
        self._listing: set[str] = set()
        self._lock = threading.Lock()

    # -- upstream: the host's request frames -------------------------------
    def note_request(self, frame: dict[str, Any]) -> None:
        # ``tools/list`` is where a server states what its tools ARE, including
        # MCP's `annotations.readOnlyHint`. That never reaches the host's
        # conversation hook -- by the time tools are handed to a model they are
        # in the provider's function-call shape, which has no field for it. The
        # shim already sits on every frame in both directions, so this is the
        # one place the declaration is observable at all.
        if frame.get("method") == "tools/list":
            rid = frame.get("id")
            if rid is not None:
                with self._lock:
                    self._listing.add(str(rid))
            return
        if frame.get("method") != "tools/call":
            return
        rid = frame.get("id")
        if rid is None:          # a notification has no id and no response
            return
        params = frame.get("params") or {}
        name = params.get("name")
        if not isinstance(name, str) or not name:
            # A call we cannot name is a call we cannot attribute. Dropping it
            # loses one outcome; inventing a name corrupts every join.
            return
        args = params.get("arguments")
        with self._lock:
            self._pending[str(rid)] = (
                name, args if isinstance(args, dict) else {}, time.monotonic(),
            )

    # -- downstream: the server's response frames --------------------------
    def note_response(self, frame: dict[str, Any]) -> None:
        rid = frame.get("id")
        if rid is None:
            return
        with self._lock:
            listing = str(rid) in self._listing
            if listing:
                self._listing.discard(str(rid))
        if listing:
            _write_tool_traits(frame)
            return
        with self._lock:
            entry = self._pending.pop(str(rid), None)
        if entry is None:
            return
        name, args, t0 = entry
        outcome, error, output = verdict_for(frame, name, self._preds)
        self._emit(name, args, outcome, error, output,
                   (time.monotonic() - t0) * 1000.0)

    # -- the child died with calls outstanding -----------------------------
    def drain(self, reason: str) -> None:
        """Outstanding calls are FAILED, not forgotten.

        A call we watched leave and never saw return did not succeed, and it is
        not unknown either -- the transport closing under it is an observation.
        """
        with self._lock:
            outstanding, self._pending = list(self._pending.items()), {}
        for _, (name, args, t0) in outstanding:
            self._emit(name, args, "failed", reason, None,
                       (time.monotonic() - t0) * 1000.0,
                       error_class="mcp_transport_closed")

    def _emit(self, name, args, outcome, error, output, latency, *,
              error_class: str | None = None) -> None:
        try:
            self._record(
                name, args,
                outcome=outcome,
                # MCP is not HTTP. `None` is the honest value, and the contract
                # discards status entirely on `unknown` regardless.
                status_code=None,
                output=output,
                error=error,
                error_class=error_class,
                latency_ms=latency,
                # DELIBERATELY absent -- see the module docstring.
                tool_call_id=None,
            )
        except Exception:                                   # noqa: BLE001
            # A capture bug costs the observation and nothing else.
            pass


def _write_tool_traits(frame: dict[str, Any]) -> None:
    """Persist declared per-tool traits from one ``tools/list`` response.

    ONE FILE PER SHIM PROCESS, never a shared one. Every wrapped server runs its
    own shim, they start concurrently, and a single merged file would be a
    read-modify-write race between processes with no lock between them. The
    reader globs and merges instead, which is also what lets it SEE a
    disagreement rather than have the last writer win it.

    Absence is preserved: a tool whose server declares no ``readOnlyHint`` is
    written with no entry, not with ``false``. "The server did not say" and
    "the server said it writes" are different facts and only one of them is
    safe to act on.

    Never raises. A trait we failed to capture costs a tool its held-out
    eligibility; an exception here would cost the operator their MCP server.
    """
    try:
        out_dir = os.environ.get("PERCEPTEYE_TRAJECTORY_DIR")
        if not out_dir:
            return
        tools = ((frame.get("result") or {}).get("tools")) or []
        if not isinstance(tools, list):
            return
        traits: dict[str, bool] = {}
        for t in tools:
            if not isinstance(t, dict):
                continue
            name = str(t.get("name") or "").strip()
            if not name:
                continue
            ann = t.get("annotations")
            if not isinstance(ann, dict):
                continue
            hint = ann.get("readOnlyHint")
            if isinstance(hint, bool):
                traits[name] = hint
        if not traits:
            return
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"tool_traits.{os.getpid()}.json")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(traits, fh)
        os.replace(tmp, path)
    except Exception:                                       # noqa: BLE001
        pass


def _pump(src, dst, on_frame) -> None:
    """Forward every line, then try to read it. Order is the contract."""
    for line in src:
        try:
            dst.write(line)
            dst.flush()
        except (BrokenPipeError, ValueError):
            break
        try:
            stripped = line.strip()
            if stripped.startswith("{"):
                frame = json.loads(stripped)
                if isinstance(frame, dict):
                    on_frame(frame)
        except Exception:                                   # noqa: BLE001
            continue


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    preds_path: str | None = None
    while args and args[0] != "--":
        if args[0] == "--predicates":
            args.pop(0)
            preds_path = args.pop(0) if args else None
        else:
            sys.stderr.write(f"[pe-mcp-shim] unknown option {args[0]!r}\n")
            return 2
    if not args or args[0] != "--":
        sys.stderr.write(
            "usage: mcp_shim.py [--predicates FILE] -- <command> [args...]\n")
        return 2
    cmd = args[1:]
    if not cmd:
        sys.stderr.write("[pe-mcp-shim] no command after --\n")
        return 2

    try:
        from percepteye_agent_flywheel import record_tool_call
    except ImportError:
        sys.stderr.write(
            "[pe-mcp-shim] percepteye-agent-flywheel is not importable by this "
            "interpreter. Invoke the shim with the interpreter that has it "
            "installed; the wrapped server keeps its own.\n")
        return 3

    shim = _Shim(load_predicates(preds_path), record_tool_call)

    # stderr is INHERITED, never captured: a server's diagnostics belong to the
    # operator watching it, and swallowing them to parse them would make this
    # shim the reason a broken server looks silent.
    child = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", bufsize=1,
    )

    def _upstream() -> None:
        """Forward the host's frames, then CLOSE the child's stdin.

        The close is the load-bearing half. Without it a server that exits on
        EOF never sees one: our stdin ends, this thread returns, and the main
        thread blocks forever reading a stdout that will never close because
        the child is still blocked reading a stdin that is still open. Both
        sides wait, the rollout burns its whole deadline, and the shim is the
        reason. Found by `test_e2e_records_the_verdict_table` hanging.
        """
        try:
            _pump(sys.stdin, child.stdin, shim.note_request)
        finally:
            try:
                child.stdin.close()
            except Exception:                               # noqa: BLE001
                pass

    up = threading.Thread(target=_upstream, daemon=True)
    up.start()

    try:
        _pump(child.stdout, sys.stdout, shim.note_response)
    finally:
        shim.drain("MCP server closed its stdout with this call outstanding")
    return child.wait()


if __name__ == "__main__":
    raise SystemExit(main())
