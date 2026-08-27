#!/usr/bin/env python3
"""Measure Border agent turn latency (spec 116, FR-016a).

Reports, in one invocation:
  1. Fixed preparation time  -- the `bundle-tools:NNms` component of the
     gateway's own [trace:embedded-run] log line for a freshly-fired trivial
     turn (the same field specs/116-border-turn-latency/research.md used to
     find the root cause).
  2. Trivial-turn end-to-end time -- wall-clock for a controlled two-character
     answer, same method as the spec's 37.9s baseline.
  3. Recent real phone-question durations -- min/median/max over the last N
     n2n-edge (phone-originated) turns found in the gateway's own logs,
     computed as the delta between that turn's [trace:embedded-run] line and
     its "[agent] run <runId> ended" line, same method as the spec's
     36s-452s baseline.

Usage:
    python3 scripts/measure-turn-latency.py [--phone-sample-size N]

Requires: the openclaw-gateway systemd --user service running and readable via
`journalctl --user -u openclaw-gateway` (or set MEASURE_LOG_SOURCE=file and
MEASURE_LOG_FILE=<path> to read from a log file instead).
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-servers", "protocol-mcp"))

TRACE_RE = re.compile(
    r"\[trace:embedded-run\] prep stages: runId=(?P<run_id>[0-9a-f-]+) "
    r"sessionId=(?P<session_id>\S+) phase=stream-ready totalMs=(?P<total_ms>\d+) "
    r"stages=(?P<stages>\S+)"
)
RUN_ENDED_RE = re.compile(r"\[agent\] run (?P<run_id>[0-9a-f-]+) ended with stopReason=")
TIMESTAMP_RE = re.compile(r"^(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+-]\d{2}:\d{2})")


def _read_gateway_logs(since: str = "-24 hours") -> list:
    source = os.environ.get("MEASURE_LOG_SOURCE", "journalctl")
    if source == "file":
        path = os.environ["MEASURE_LOG_FILE"]
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    result = subprocess.run(
        ["journalctl", "--user", "-u", "openclaw-gateway", "--since", since,
         "--no-pager", "-o", "short-iso"],
        capture_output=True, text=True, timeout=30,
    )
    return result.stdout.splitlines()


def _parse_ts(line: str):
    m = TIMESTAMP_RE.search(line)
    if not m:
        return None
    ts = m.group("ts")
    # Python's fromisoformat handles this format directly (3.11+); fall back
    # to a manual strip of fractional seconds beyond microsecond precision.
    try:
        from datetime import datetime
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def find_bundle_tools_ms(lines: list) -> int | None:
    """Extract the most recent bundle-tools:NNms value from any
    [trace:embedded-run] line -- the fixed preparation cost this feature
    targets (research.md Finding 1)."""
    latest = None
    for line in lines:
        m = TRACE_RE.search(line)
        if not m:
            continue
        stages = m.group("stages")
        bt = re.search(r"bundle-tools:(\d+)ms", stages)
        if bt:
            latest = int(bt.group(1))
    return latest


def find_phone_turn_durations(lines: list, sample_size: int = 20) -> list:
    """Find the last `sample_size` n2n-edge (phone-originated) turns and
    compute each one's end-to-end duration as the delta between its
    [trace:embedded-run] timestamp and its "[agent] run ... ended" timestamp
    (same runId) -- reproducing the spec's original 36s-452s measurement
    method."""
    trace_ts_by_run = {}
    for line in lines:
        m = TRACE_RE.search(line)
        if not m:
            continue
        if not m.group("session_id").startswith("n2n-edge"):
            continue
        ts = _parse_ts(line)
        if ts is not None:
            trace_ts_by_run[m.group("run_id")] = ts

    durations = []
    for line in lines:
        m = RUN_ENDED_RE.search(line)
        if not m:
            continue
        run_id = m.group("run_id")
        start_ts = trace_ts_by_run.get(run_id)
        if start_ts is None:
            continue
        end_ts = _parse_ts(line)
        if end_ts is None:
            continue
        durations.append((end_ts - start_ts).total_seconds())

    return durations[-sample_size:]


async def _measure_trivial_turn_end_to_end() -> tuple[float, float]:
    """Fires two turns in the same (fresh) session and returns
    (first_turn_s, second_turn_s). Per spec.md Acceptance Scenario 1, SC-001's
    <12s target applies to "a Border that has been running long enough to have
    served at least one prior request" -- i.e. a WARM turn, not a cold first
    one in a brand-new session. The first turn's cost is reported separately
    since a one-time per-session warm-up is explicitly acceptable (FR-004b)."""
    from bgp.federation.gateway import run_agent_turn
    session_key = f"measure-turn-latency-{uuid.uuid4()}"
    t0 = time.monotonic()
    await run_agent_turn("Reply with exactly the two characters: OK", session_key=session_key)
    first_s = time.monotonic() - t0
    t1 = time.monotonic()
    await run_agent_turn("Reply with exactly the two characters: OK", session_key=session_key)
    second_s = time.monotonic() - t1
    return first_s, second_s


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phone-sample-size", type=int, default=20,
                         help="Number of recent phone-originated turns to sample (default 20, "
                              "matching the spec's original sample)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    print("Measuring trivial-turn end-to-end time (firing two live turns, same session)...",
          file=sys.stderr)
    import asyncio
    first_s, second_s = asyncio.run(_measure_trivial_turn_end_to_end())

    print("Reading gateway logs for fixed preparation time and phone-turn history...",
          file=sys.stderr)
    lines = _read_gateway_logs()
    bundle_tools_ms = find_bundle_tools_ms(lines)
    phone_durations = find_phone_turn_durations(lines, sample_size=args.phone_sample_size)

    result = {
        "first_turn_end_to_end_s": round(first_s, 2),
        "second_turn_end_to_end_s": round(second_s, 2),
        "fixed_preparation_ms": bundle_tools_ms,
        "phone_turn_sample_count": len(phone_durations),
        "phone_turn_durations_s": [round(d, 1) for d in phone_durations],
    }
    if phone_durations:
        result["phone_turn_min_s"] = round(min(phone_durations), 1)
        result["phone_turn_median_s"] = round(statistics.median(phone_durations), 1)
        result["phone_turn_max_s"] = round(max(phone_durations), 1)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print()
    print("=== Border Agent Turn Latency Measurement (spec 116, FR-016a) ===")
    print(f"First turn (cold, new session):  {result['first_turn_end_to_end_s']}s"
          f"  (one-time per-session warm-up cost, acceptable per FR-004b)")
    print(f"Second turn (warm, same session): {result['second_turn_end_to_end_s']}s"
          f"  (baseline: 37.9s; target SC-001: <12s; SC-003: must not repeat first-turn cost)")
    if bundle_tools_ms is not None:
        print(f"Fixed preparation time (last cold turn logged): {bundle_tools_ms / 1000:.1f}s"
              f"  (baseline: 26.8s; target SC-002: <3s)")
    else:
        print("Fixed preparation time:        no [trace:embedded-run] line found in recent logs")
    if phone_durations:
        print(f"Recent phone-question turns:   n={result['phone_turn_sample_count']}  "
              f"min={result['phone_turn_min_s']}s  "
              f"median={result['phone_turn_median_s']}s  "
              f"max={result['phone_turn_max_s']}s"
              f"  (baseline: 36s-452s; target SC-004: median >=3x faster)")
    else:
        print("Recent phone-question turns:   no n2n-edge turns found in recent logs")


if __name__ == "__main__":
    main()
