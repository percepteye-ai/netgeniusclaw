# Feature Specification: Token Optimization (Count + TOON)

**Feature Branch**: `006-token-optimization`
**Created**: 2026-03-26
**Status**: Draft
**Input**: User description: "Integrate the model provider count_tokens API for real-time token and cost tracking on every interaction, plus TOON format for all MCP server responses and LLM interactions to reduce token consumption by 40-60%."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Token Count and Cost Display (Priority: P1)

As a network operator using NetGeniusClaw, I want to see the exact number
of input tokens, output tokens, and dollar cost at the bottom of
every single interaction, so I always know what each operation costs
and can make informed decisions about which queries to run.

**Why this priority**: Transparency is the foundation. Users cannot
optimize what they cannot see. Every other optimization (TOON, cost
reduction) is meaningless without visibility. This also builds trust --
NetGeniusClaw never hides costs from its operator.

**Independent Test**: Can be fully tested by running any NetGeniusClaw
command and verifying that a token/cost summary line appears at the
bottom of the response showing input tokens, output tokens, total
tokens, and estimated cost in USD.

**Acceptance Scenarios**:

1. **Given** NetGeniusClaw is running with token tracking enabled,
   **When** the operator asks "show BGP peers on router R1",
   **Then** the response includes the BGP peer data AND a footer
   line showing: input tokens, output tokens, total tokens, and
   estimated cost (e.g., "Tokens: 1,245 in / 382 out / 1,627 total |
   Cost: $0.0158").

2. **Given** NetGeniusClaw is running a multi-tool operation (e.g., health
   check that calls pyATS, Grafana, and Prometheus),
   **When** the operation completes,
   **Then** the footer shows cumulative tokens across ALL tool calls
   in that interaction, not just the final one.

3. **Given** the operator has been using NetGeniusClaw for an extended
   session,
   **When** they ask "show session token usage",
   **Then** the system returns a breakdown of total session tokens,
   cost, per-tool token counts, and a comparison showing tokens
   saved by TOON format.

4. **Given** the the model endpoint is unreachable for token counting,
   **When** the operator runs a command,
   **Then** the system estimates token count locally (approximate)
   and marks the count as "estimated" rather than failing silently.

---

### User Story 2 - TOON Format for MCP Responses (Priority: P2)

As a network operator, I want all MCP server responses to be
serialized in TOON format instead of JSON, so that tabular network
data (route tables, interface lists, BGP peers, firewall rules)
consumes 40-60% fewer tokens, reducing cost and fitting more data
in the context window.

**Why this priority**: MCP tool responses are the largest source of
token consumption in NetGeniusClaw. Network data is inherently tabular --
route tables with hundreds of entries, interface lists across dozens
of devices, BGP peer tables. TOON's CSV-style array encoding is
purpose-built for this data shape.

**Independent Test**: Can be tested by running "show routes" via
SuzieQ or pyATS and comparing the token count of the TOON response
against the equivalent JSON response, verifying at least 30% savings.

**Acceptance Scenarios**:

1. **Given** a network query returns tabular data (e.g., 50 routes),
   **When** the MCP server returns the response,
   **Then** the response is serialized in TOON format with column
   headers and CSV-style rows instead of repeated JSON key-value
   pairs.

2. **Given** a network query returns deeply nested non-tabular data
   (e.g., a single device's detailed config),
   **When** the MCP server returns the response,
   **Then** the response uses TOON's YAML-style nested object
   notation, which still saves tokens by eliminating quotes and
   braces.

3. **Given** TOON serialization is active,
   **When** the operator asks "compare token usage with and without
   TOON",
   **Then** the system shows the TOON token count, the equivalent
   JSON token count, the savings percentage, and the dollar amount
   saved.

4. **Given** TOON encoding fails for a particular response,
   **When** the MCP server attempts to serialize,
   **Then** the system falls back to JSON and logs a warning, never
   failing the operation due to a serialization issue.

---

### User Story 3 - TOON in HEARTBEAT and SOUL (Priority: P3)

As the NetGeniusClaw project maintainer, I want HEARTBEAT.md and SOUL.md
updated so that NetGeniusClaw's identity includes token-consciousness --
it always counts tokens, always uses TOON, and always reports costs
transparently as part of its core operating behavior.

**Why this priority**: NetGeniusClaw's identity documents (SOUL.md,
HEARTBEAT.md) define how the agent behaves. If token tracking and
TOON aren't embedded in the identity, they'll be treated as optional
features rather than non-negotiable behaviors.

**Independent Test**: Can be tested by reading SOUL.md and
HEARTBEAT.md and verifying that token counting and TOON usage are
listed as mandatory behaviors, and that heartbeat check-ins include
token usage summaries.

**Acceptance Scenarios**:

1. **Given** SOUL.md has been updated,
   **When** NetGeniusClaw starts a new session,
   **Then** it follows the soul directive to count and display tokens
   on every interaction and serialize all responses in TOON format.

2. **Given** HEARTBEAT.md has been updated,
   **When** NetGeniusClaw performs a periodic heartbeat check-in,
   **Then** the check-in includes: session token count, session cost,
   TOON savings percentage, and top 5 most token-expensive operations.

---

### User Story 4 - Per-Tool Token Breakdown (Priority: P4)

As a network operator optimizing costs, I want to see a per-tool
breakdown of token consumption so I can identify which MCP tools and
skills are the most expensive and adjust my usage patterns.

**Why this priority**: Aggregate totals tell you the bill. Per-tool
breakdowns tell you where to optimize. This enables data-driven
decisions about which tools to use for specific tasks.

**Independent Test**: Can be tested by running several different
operations and then asking "show token breakdown by tool" to see
ranked usage.

**Acceptance Scenarios**:

1. **Given** NetGeniusClaw has executed multiple tool calls in a session,
   **When** the operator asks "show token usage by tool",
   **Then** the system returns a ranked table showing each tool's
   call count, total input tokens, total output tokens, total cost,
   and average tokens per call.

2. **Given** TOON is active,
   **When** the operator views the per-tool breakdown,
   **Then** each tool's entry includes a "TOON savings" column
   showing how many tokens were saved by TOON serialization for
   that specific tool.

---

### User Story 5 - TOON Across All Existing MCP Servers (Priority: P5)

As the NetGeniusClaw project maintainer, I want every existing MCP server
(pyATS, NetBox, Grafana, ServiceNow, protocol-mcp, etc.) to adopt
TOON serialization for their responses, not just the new servers.

**Why this priority**: The biggest savings come from the highest-
volume tools. pyATS (50+ tools), Grafana (75+ tools), and Meraki
(~804 endpoints) generate the most token-heavy responses. TOON on
these existing servers multiplies the savings across the entire
platform.

**Independent Test**: Can be tested by running a pyATS show command
and verifying the response is in TOON format, then repeating for
NetBox, Grafana, and other bundled MCP servers.

**Acceptance Scenarios**:

1. **Given** pyATS MCP server has been updated with TOON support,
   **When** the operator runs "show interfaces" via pyATS,
   **Then** the response is TOON-serialized with interface data in
   tabular CSV-style format.

2. **Given** all bundled MCP servers have been updated,
   **When** the operator runs any tool from any MCP server,
   **Then** the response is in TOON format by default with JSON
   fallback if TOON encoding fails.

---

### Edge Cases

- What happens when the the model provider count_tokens API is rate-limited?
- How does the system handle counting tokens for image or PDF content
  in tool responses?
- What happens when a TOON-encoded response exceeds the context
  window despite the savings?
- How does token counting work when the model is Sonnet (fallback)
  vs Opus (primary) -- different pricing?
- What happens when an MCP server returns binary data (pcap files)
  that cannot be TOON-encoded?
- How are cached tokens (prompt caching) reflected in the cost
  display?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST count input and output tokens for every
  LLM interaction using the model provider's official count_tokens API.
- **FR-002**: System MUST display a token/cost summary footer at the
  bottom of every response showing: input tokens, output tokens,
  total tokens, and estimated USD cost.
- **FR-003**: System MUST track cumulative session totals for tokens
  and cost, available on demand.
- **FR-004**: System MUST serialize all MCP server tool responses in
  TOON format by default.
- **FR-005**: System MUST fall back to JSON if TOON serialization
  fails for any response, logging a warning without failing the
  operation.
- **FR-006**: System MUST calculate TOON savings (tokens saved vs
  equivalent JSON) and include this in usage reports.
- **FR-007**: System MUST support per-tool token tracking with call
  count, input/output tokens, and cost per tool.
- **FR-008**: System MUST update SOUL.md to include token
  transparency and TOON usage as mandatory agent behaviors.
- **FR-009**: System MUST update HEARTBEAT.md to include token usage
  summaries in periodic check-ins.
- **FR-010**: System MUST support model-aware pricing (Opus, Sonnet,
  Haiku have different rates per million tokens).
- **FR-011**: System MUST provide a shared TOON serialization utility
  usable by all MCP servers to avoid duplicating TOON encoding logic.
- **FR-012**: System MUST log all token counts to the GAIT audit
  trail as part of each session summary.
- **FR-013**: System MUST handle prompt caching scenarios by
  reflecting cached vs uncached token costs accurately.
- **FR-014**: System MUST provide an approximate local token estimate
  when the the model endpoint is unreachable, clearly marked as estimated.
- **FR-015**: System MUST update all bundled MCP servers (pyATS,
  NetBox, Grafana, ServiceNow, protocol-mcp, SuzieQ, Batfish, gNMI,
  Azure, and others) to use TOON serialization.
- **FR-016**: All token tracking credentials (NETGENIUSCLAW_MODEL_API_KEY) MUST
  be read from environment variables.
- **FR-017**: System MUST never hide, omit, or suppress token counts.
  Every interaction shows its cost. This is non-negotiable.

### Key Entities

- **Token Count**: A record of input tokens, output tokens, and model
  used for a single LLM interaction or tool call.
- **Cost Estimate**: Calculated USD cost based on token count and
  model-specific pricing (input rate, output rate, cache discount).
- **Session Ledger**: Cumulative running total of all token counts
  and costs within a session, with per-tool breakdown.
- **TOON Response**: An MCP tool response serialized in TOON format,
  including the equivalent JSON token count for savings calculation.
- **Token Footer**: The mandatory display element appended to every
  response showing current interaction and session token/cost totals.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of interactions display a token/cost footer --
  zero exceptions.
- **SC-002**: TOON-serialized MCP responses achieve at least 30%
  token savings on average compared to equivalent JSON responses
  across all tool calls in a typical session.
- **SC-003**: Tabular network data (route tables, interface lists,
  BGP peer tables) achieves at least 50% token savings when
  TOON-serialized.
- **SC-004**: Token counts from the the model endpoint match billing
  within 5% accuracy.
- **SC-005**: Per-tool token breakdown is available within 1 second
  on demand.
- **SC-006**: SOUL.md and HEARTBEAT.md accurately reflect token
  counting and TOON as mandatory behaviors.
- **SC-007**: All artifact coherence checklist items are complete
  (README, install.sh, UI, SOUL.md, SKILL.md, .env.example, TOOLS.md,
  config/openclaw.json).
- **SC-008**: Existing MCP servers and skills remain fully functional
  after TOON integration (backwards compatibility).
- **SC-009**: TOON fallback to JSON succeeds 100% of the time when
  TOON encoding fails.

## Assumptions

- the model provider's count_tokens API is free to use and available at the
  rate limits sufficient for NetGeniusClaw's operational volume.
- The `toon-format` Python package provides reliable serialization
  and deserialization for all data types NetGeniusClaw's MCP servers return.
- the agent models (Opus 4.6, Sonnet 4.6, Haiku 4.5) can accurately
  parse and reason about TOON-formatted data with no accuracy loss
  compared to JSON.
- The NETGENIUSCLAW_MODEL_API_KEY environment variable is already configured
  for NetGeniusClaw's operation (required for the LLM itself, reused for
  token counting).
- Existing MCP servers can be updated to use a shared TOON
  serialization utility without breaking their existing tool schemas.
- Binary data (pcap files, images) will not be TOON-encoded; only
  structured text/JSON responses are candidates for TOON.
- Token pricing is hardcoded initially and updated manually when
  the model provider changes rates. An env var override is provided for
  custom pricing.
