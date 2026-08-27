# Implementation Plan: Token Optimization (Count + TOON)

**Branch**: `006-token-optimization` | **Date**: 2026-03-26 | **Spec**: specs/006-token-optimization/spec.md
**Input**: Feature specification from `/specs/006-token-optimization/spec.md`

## Summary

Add real-time token counting and cost tracking to every NetGeniusClaw interaction using Anthropic's `count_tokens()` API, plus TOON-format serialization for all MCP server responses to reduce token consumption by 40-60%. This is implemented as a shared Python library (`src/netclaw_tokens/`) consumed by all bundled MCP servers, with identity updates to SOUL.md and HEARTBEAT.md making token transparency a mandatory agent behavior.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: anthropic (SDK with count_tokens), toon-format (TOON serialization), FastMCP (existing MCP framework)
**Storage**: N/A (in-memory session ledger; no persistent storage)
**Testing**: pytest
**Target Platform**: Linux/macOS server (same as existing NetGeniusClaw)
**Project Type**: Shared library + skill + updates to existing MCP servers
**Performance Goals**: Token footer generation < 50ms; TOON serialization adds < 100ms per response
**Constraints**: Must not break any existing MCP server; TOON failures must fall back to JSON silently
**Scale/Scope**: 28+ bundled MCP servers to update, 1 shared library, 1 skill, identity doc updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Safety-First | PASS | Read-only library; no device interaction |
| II. Read-Before-Write | PASS | No device writes involved |
| III. ITSM-Gated | N/A | No production device changes |
| IV. Immutable Audit Trail | PASS | Token summaries will be included in GAIT logs (FR-012) |
| V. MCP-Native | PASS | Not an MCP server itself; enhances existing MCP servers |
| VI. Multi-Vendor Neutrality | PASS | Vendor-agnostic shared library |
| VII. Skill Modularity | PASS | Single-purpose token-tracker skill |
| VIII. Verify After Change | PASS | Each MCP server update verified by test |
| IX. Security by Default | PASS | ANTHROPIC_API_KEY read from env var (FR-016) |
| X. Observability | PASS | Token metrics are observability data |
| XI. Artifact Coherence | PENDING | All artifacts listed in spec SC-007 will be updated |
| XII. Documentation-as-Code | PENDING | SKILL.md, README updates planned |
| XIII. Credential Safety | PASS | API key from env var, never hardcoded |
| XIV. Human-in-the-Loop | N/A | No external communications |
| XV. Backwards Compatibility | PASS | TOON falls back to JSON; existing behavior preserved |
| XVI. Spec-Driven Development | PASS | Following SDD workflow |

**Gate Result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/006-token-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (speckit.tasks)
```

### Source Code (repository root)

```text
src/
└── netclaw_tokens/
    ├── __init__.py
    ├── counter.py           # Token counting via Anthropic API + local fallback
    ├── toon_serializer.py   # TOON serialization with JSON fallback
    ├── cost_calculator.py   # Model-aware pricing calculator
    ├── session_ledger.py    # Cumulative session tracking with per-tool breakdown
    └── footer.py            # Token footer formatter

tests/
├── unit/
│   ├── test_counter.py
│   ├── test_toon_serializer.py
│   ├── test_cost_calculator.py
│   ├── test_session_ledger.py
│   └── test_footer.py
└── integration/
    └── test_mcp_toon_integration.py

workspace/skills/token-tracker/
└── SKILL.md                 # Skill documentation
```

**Structure Decision**: Single shared library under `src/netclaw_tokens/` (new directory). This is a library, not an MCP server, so it lives in `src/` rather than `mcp-servers/`. All bundled MCP servers import from this library. Tests follow standard pytest layout under `tests/`.

## Complexity Tracking

No constitution violations to justify.
