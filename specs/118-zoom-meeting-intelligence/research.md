# Research: NetGeniusClaw for Zoom — Meeting Intelligence (MVP)

## R1 — How does a recognized meeting request reach Border's existing investigation path?

**Decision**: The new Zoom listener (`zoom-rtms-mcp`) never calls `run_agent_turn()` directly. Instead
it makes a local, loopback-only call into a new restricted channel on the Border federation daemon
(`bgp/federation/zoom_channel.py`), which calls `run_agent_turn(prompt=..., session_key=f"n2n-zoom-
{meeting_uuid}")` — the daemon-autonomous-turn pattern already used by `chat.py` for inbound peer
chat messages (an external event triggers the daemon to initiate a turn on its own, not the reverse).

**Rationale**: Every existing caller of `run_agent_turn()` in the codebase (`chat.py`, `invocation.py`,
`gateway_ws.py`, `service.py`) lives inside `bgp/federation/` and is invoked by the Border daemon
itself, never by an external MCP server importing it directly — MCP servers are separate processes
per Constitution Principle V ("MCP-Native Integration... no bespoke integration patterns outside the
MCP protocol"). `edge.py`'s `EdgeChannel`/`EDGE_METHODS` is the closest precedent for "an external,
non-mesh-peer process talks to the Border over a restricted method set" (feature 066), and `chat.py`
is the closest precedent for "an inbound event autonomously triggers a turn" (peer chat). Combining
both patterns — a new restricted local channel, dispatching to the existing autonomous-turn logic —
reuses two already-proven mechanisms instead of inventing a third.

**Alternatives considered**:
- *zoom-rtms-mcp imports `bgp.federation.gateway` directly*: rejected — breaks the MCP-server process
  boundary every other integration respects, and couples an MCP server's lifecycle to the Border
  daemon's internal module layout.
- *Route through the full iN2N enrolled-member/pinned-key trust model (like a mobile edge device)*:
  rejected as overkill — `zoom-rtms-mcp` runs on the same Border host as the daemon (not a remote,
  independently-operated device), so the remote-trust machinery `EdgeChannel` needs for an untrusted
  network peer (enrollment tokens, pinned keys, TLS) has no threat model to answer here. A loopback-
  only restricted channel gets the same method-allowlist safety property (mirroring `EDGE_METHODS`)
  without the remote-enrollment machinery that doesn't apply.

## R2 — Where does intent/entity recognition (location/technology/time-window) run?

**Decision**: Inside `zoom-rtms-mcp` itself, as a deterministic, rule-based extractor (keyword/pattern
matching against known site names, technology terms, and relative-time phrases) run on every new
transcript/chat line as it lands in a meeting's live buffer — not an LLM call, and not something the
Border daemon does.

**Rationale**: This keeps `zoom-rtms-mcp` self-contained (Constitution Principle V: each MCP server
is a complete capability) and keeps the safety-critical distinction — "is this actually a question/
request, or a hypothetical/past-tense/third-party remark?" — auditable and testable as plain code
rather than dependent on model behavior. It also matches the existing pattern of deterministic,
non-LLM classification elsewhere in NetGeniusClaw (e.g. `bgp-intel-mcp`'s registry lookups). Only once the
extractor decides "this is a real, present-tense, first-person investigation request" does it call
out to the new Border channel (R1) — the LLM/agent turn only ever sees requests that already passed
this filter, which is what makes FR-009 ("never treat hypothetical/past-tense/third-party speech as
authorization") enforceable independent of model judgment.

**Alternatives considered**: Running recognition as an LLM-driven step inside the agent turn itself —
rejected because it would mean every meeting utterance triggers a full agent turn just to decide
whether to act, which is both wasteful and, more importantly, moves the safety boundary inside the
model's judgment rather than in front of it.

## R3 — How does the Zoom App panel receive live updates?

**Decision**: `zoom-rtms-mcp` runs a small companion WebSocket endpoint (same process, separate port)
that the Zoom App's frontend JS connects to directly per meeting. Avatar state, detected topic, and
investigation results are pushed down this connection as they change. This is entirely separate from,
and does not touch, the NCFED mesh, GAIT, or any peer-trust machinery — it is a local
presentation-layer feed from one MCP server to the browser surface running inside the Zoom client.

**Rationale**: The Zoom App is a browser-embedded surface (runs inside the Zoom client, not inside
NetGeniusClaw's own process boundary), so it cannot import Python or call MCP tools directly — it needs a
network-reachable endpoint. Keeping that endpoint owned by `zoom-rtms-mcp` (rather than exposing
anything from the Border daemon itself to the browser) keeps the Border daemon's attack surface
unchanged: nothing outside the existing NCFED trust model gets a new way to reach it.

**Alternatives considered**: Having the Zoom App poll an MCP tool over HTTP — rejected; MCP's
request/response tool-call model is a poor fit for "push a state change the instant it happens,"
which is what makes the shared panel (US3) and camera overlay (US5) feel live rather than laggy.

## R4 — RTMS ingestion: build vs. use the official SDK

**Decision**: Use Zoom's official RTMS Python SDK (released Feb 2026 alongside the Node.js SDK) for
the WebSocket signaling/session lifecycle and message parsing, rather than hand-rolling the RTMS wire
protocol.

**Rationale**: Constitution's MCP Server Standards already establishes "no custom protocol
implementations" as the norm for MCP transports; the same reasoning applies to a first-party
real-time protocol Zoom maintains and versions on its own schedule. Python keeps `zoom-rtms-mcp`
consistent with every other NetGeniusClaw MCP server (Constitution: "Python 3.10+ (MCP servers, scripts)").
RTMS media/transcript signals needed for this feature are: per-participant transcript, meeting chat
(added to RTMS July 2026), active-speaker, and screen-share/content signals — raw audio/video media
streams are explicitly not consumed in this pass (no audio/video processing is needed since no
avatar speaks with synthesized audio, per FR-016).

**Alternatives considered**: Node.js RTMS SDK — rejected only to keep the whole server in one
language matching the rest of NetGeniusClaw's MCP fleet; there is no functional reason it couldn't work,
this is a consistency call, not a capability gap.

## R5 — RTMS/webhook public reachability

**Decision**: Treat "a public HTTPS endpoint for Zoom's RTMS-start webhook to reach `zoom-rtms-mcp`"
as an environment/deployment concern, satisfied by whatever ingress mechanism the operator's NetGeniusClaw
install already runs (ngrok HTTP tunnel, a reverse proxy, Cloudflare Tunnel in HTTP mode, etc.) — not
something this feature builds or mandates.

**Rationale**: Spec 108's Cloudflare Tunnel work is scoped specifically to eN2N's TCP/private-network
transport between federation peers, a different protocol and threat model from an HTTPS webhook a
third-party SaaS (Zoom) needs to reach. Re-using it isn't a fit; inventing a second tunnel mechanism
for this one feature isn't justified either. `quickstart.md` documents the requirement (a reachable
HTTPS URL) and leaves the "how" to the operator's existing environment, consistent with how every
other webhook-driven NetGeniusClaw integration (Twilio voice, feature 042/043) already treats this.

## R6 — Official Zoom Meetings MCP registration

**Decision**: Register as an **external / remote-OAuth** integration per `docs/ADDING-AN-MCP.md`'s
decision table (no `config/openclaw.json` entry; tracked in `EXTERNAL_INTEGRATIONS` with reason
`remote/OAuth`) — the same treatment as the Datadog MCP integration (spec 016).

**Rationale**: Zoom's own MCP documentation (as of this research) describes a hosted/remote MCP
service authenticated via standard OAuth/API-key connector patterns, not a locally-vendored package.
This matches `docs/ADDING-AN-MCP.md`'s "Remote / OAuth" row exactly. The specific tool names Zoom's
Meetings MCP exposes (semantic search, assets, recordings) will be confirmed against Zoom's connector
setup flow at implementation time; the registration *kind* is not contingent on that detail.

## R7 — Read/write safety boundary: what's new vs. what's reused

**Decision**: This feature adds no new write-approval mechanism. The zoom-meeting-context skill's
extractor (R2) only ever constructs an agent prompt for recognized, present-tense, first-person
*investigation* (read/diagnostic) requests — by construction, a hypothetical/past-tense/third-party
remark never reaches the point of producing a prompt at all, satisfying FR-009 before the agent is
ever invoked. If a meeting utterance is somehow phrased as a direct configuration-change command, the
resulting agent turn still passes through whatever existing device-write approval gate NetGeniusClaw's
underlying vendor skills already enforce (Constitution Principles I–III: observe-before-write,
ITSM-gated changes) — unchanged, regardless of which channel (CLI, chat, mobile, voice, or now Zoom)
originated the turn.

**Rationale**: Constitution Principle XV (Backwards Compatibility) — this feature must not touch
shared write-approval interfaces. The NCFED `Authorizer`/`approval_request` mechanism (grants, human
approval, GAIT-linked) governs *peer-to-peer task delegation trust* across federation, a different
axis from *device configuration write safety*, which lives in the vendor MCP servers/skills
themselves. Meeting-sourced requests are just another origin for an ordinary agent turn; they inherit
whatever gate already exists at the point where a write would actually be attempted.

## R8 — Camera-overlay avatar: Layers API access

**Decision**: Layers API "Camera mode" requires the "Controller mode" component and app review before
it's usable in a real meeting (per Zoom's Zoom Apps guide). This is flagged as a setup/timeline
prerequisite in `quickstart.md`, not resolved further here — the exact review/approval process is an
operational step for the app owner (John), not a design decision this plan can make. If review access
turns out to be gated behind a partner program NetGeniusClaw doesn't have, User Story 5 degrades gracefully
to "side-panel avatar only" (User Story 3) without affecting User Stories 1/2/4.

**Rationale**: Constitution Principle XVI requires the spec/plan to proceed on documented assumptions
rather than blocking on an external approval process outside NetGeniusClaw's control; User Story 5 was
explicitly prioritized P3 for exactly this reason.
