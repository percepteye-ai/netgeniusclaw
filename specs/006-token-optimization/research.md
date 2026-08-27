# Research: Token Optimization (Count + TOON)

**Feature**: 006-token-optimization
**Date**: 2026-03-26

## Research Tasks

### 1. Anthropic count_tokens API

**Decision**: Use `anthropic.Anthropic().messages.count_tokens()` from the official `anthropic` Python SDK.

**Rationale**: This is the official, supported method for exact token counting. It uses the same tokenizer as the billing system, ensuring counts match actual usage within 5% (SC-004). The SDK is already a dependency since NetGeniusClaw uses Claude as its AI runtime.

**Alternatives considered**:
- `tiktoken` (OpenAI tokenizer): Wrong tokenizer for Claude models; would produce inaccurate counts.
- Manual `len(text) / 4` estimation: Too imprecise for cost tracking; used only as fallback when API unavailable.
- Third-party token counting libraries: No official support for Claude's tokenizer outside Anthropic's SDK.

**Fallback strategy**: When the Anthropic API is unreachable or rate-limited, fall back to `len(text) / 4` approximation and mark the count with `estimated: true`. This ensures the system never fails due to token counting issues (FR-014).

### 2. TOON Format Serialization

**Decision**: Use the `toon-format` Python package (`pip install toon-format`), imported as `import toon; toon.dumps(data)`.

**Rationale**: TOON (Tabular Object Oriented Notation) is specifically designed to reduce token consumption for LLM interactions. It achieves 40-60% savings on tabular data (which is the majority of network data: route tables, interface lists, BGP peers) by using CSV-style array encoding instead of repeated JSON key-value pairs.

**Alternatives considered**:
- MessagePack/CBOR: Binary formats; not human-readable, Claude cannot reason about them.
- YAML: Saves some tokens over JSON but not as much as TOON for tabular data.
- Custom CSV encoding: Would require a custom parser; TOON is standardized.
- Protocol Buffers: Binary format; not suitable for LLM context.

**Integration pattern**: Wrap as `serialize_response(data)` that tries TOON first, falls back to JSON on any error. Calculate savings by comparing token counts of both formats.

### 3. Token Pricing Model

**Decision**: Hardcoded pricing dictionary with environment variable override via `NETCLAW_TOKEN_PRICING_OVERRIDE`.

**Rationale**: Anthropic's pricing changes infrequently. Hardcoding with an override mechanism provides zero-config operation while allowing quick updates without code changes.

**Pricing (per 1M tokens)**:
| Model | Input | Output |
|-------|-------|--------|
| Opus 4.6 | $5.00 | $25.00 |
| Sonnet 4.6 | $3.00 | $15.00 |
| Haiku 4.5 | $1.00 | $5.00 |

**Prompt caching**: 90% discount on cached input tokens (Anthropic standard).

### 4. Thread Safety for Session Ledger

**Decision**: Use `threading.Lock` for thread-safe accumulation in session_ledger.py.

**Rationale**: MCP servers may process concurrent tool calls within a session. The session ledger must safely accumulate counts from multiple threads. Python's `threading.Lock` is lightweight and sufficient for this use case (no contention expected beyond tool-call parallelism).

**Alternatives considered**:
- `asyncio.Lock`: Would require the entire ledger to be async; unnecessary complexity.
- `multiprocessing.Lock`: Overkill; MCP servers run in a single process.
- No locking (single-threaded assumption): Unsafe if tools execute concurrently.

### 5. MCP Server Update Pattern

**Decision**: Add TOON serialization via import of shared `netclaw_tokens.toon_serializer.serialize_response()` in each MCP server's response path.

**Rationale**: A shared utility avoids duplicating TOON logic across 28+ servers. Each server wraps its return data with `serialize_response(data)` which handles TOON encoding, JSON fallback, and savings calculation.

**Integration approach**:
- For Python MCP servers (majority): Direct import of `netclaw_tokens.toon_serializer`
- For Node.js MCP servers (ui-related): Use a TOON conversion wrapper that post-processes responses
- For community/remote MCP servers: Add a TOON conversion middleware layer

### 6. GAIT Integration

**Decision**: Include token summaries in session GAIT logs as structured metadata.

**Rationale**: Constitution Principle IV (Immutable Audit Trail) requires all operational data to be recorded. Token usage is operational metadata that belongs in the audit trail.

**Format**: Add a `token_summary` field to GAIT session commit data containing: total_input_tokens, total_output_tokens, total_cost_usd, toon_savings_tokens, per_tool_breakdown.

### 7. Binary Data Handling

**Decision**: Skip TOON encoding for binary data (pcap files, images, PDFs); pass through unchanged.

**Rationale**: TOON is designed for structured text data. Binary content has no tabular structure to optimize. Attempting to TOON-encode binary data would fail or produce larger output.

**Detection**: Check if data is `bytes` type or contains non-UTF-8 content before attempting TOON serialization.
