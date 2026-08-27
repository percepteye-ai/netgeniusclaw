# Zoom RTMS MCP Server

NetClaw-authored MCP server for **NetGeniusClaw for Zoom — Meeting Intelligence** ([spec 118](../../specs/118-zoom-meeting-intelligence/spec.md)). Ingests live meeting transcript, chat, active-speaker, and screen-share-start/stop signals via Zoom's Realtime Media Streams (RTMS) — deliberately not a Meeting SDK bot, since Zoom reserves that participant path for human use and directs AI applications to RTMS instead. Recognizes network-investigation questions with a deterministic (non-LLM) extractor and routes them into NetGeniusClaw's existing Border/NCFED investigation path.

## Tools (9)

| Tool | Description |
|------|-------------|
| `zoom_enable_listening` | Enable RTMS listening for a meeting (FR-001/FR-015) |
| `zoom_disable_listening` | Disable listening and destroy the live buffer immediately (FR-014) |
| `zoom_list_active_meetings` | Which meetings currently have listening enabled (FR-015) |
| `zoom_meeting_status` | Connection state, avatar state, participant count for one meeting |
| `zoom_recent_transcript` | Recent transcript entries from the live buffer |
| `zoom_recent_chat` | Recent in-meeting chat entries from the live buffer |
| `zoom_active_speaker` | Current active speaker, if known |
| `zoom_live_context` | Aggregate: connection/avatar state, recent transcript+chat, active speaker, current investigation |
| `zoom_search_historical_meetings` | Thin pass-through to the official Zoom Meetings MCP (US2) — not yet wired to a live connection in every environment; see research.md R6 |

Full contract: [`contracts/zoom-rtms-mcp-tools.md`](../../specs/118-zoom-meeting-intelligence/contracts/zoom-rtms-mcp-tools.md).

## Architecture

This server also runs three background services, independent of any MCP tool call:

- **`webhook.py`** — receives Zoom's `meeting.rtms_started`/`meeting.rtms_stopped` webhook (HTTP, `ZOOM_RTMS_WEBHOOK_PORT`, default 8899), including Zoom's standard URL-validation handshake.
- **`panel_feed.py`** — a WebSocket server (`ZOOM_PANEL_FEED_PORT`, default 8900) feeding the NetGeniusClaw Zoom App side panel (`ui/netclaw-zoom-app/`) live status/avatar/results, per [`contracts/zoom-app-panel-feed.md`](../../specs/118-zoom-meeting-intelligence/contracts/zoom-app-panel-feed.md).
- **`zoom_channel_client.py`** — a loopback client connecting to the Border federation daemon's `bgp/federation/zoom_channel.py`, submitting recognized investigation requests and receiving pushed results. Per [`contracts/zoom-channel-internal.md`](../../specs/118-zoom-meeting-intelligence/contracts/zoom-channel-internal.md).

`extractor.py` classifies every new transcript/chat line: hypothetical/past-tense/third-party remarks are suppressed before anything is ever submitted (FR-009 — the safety boundary is enforced by never sending the request, not by filtering downstream); genuine investigation requests get location/technology/time-window extracted and forwarded.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ZOOM_CLIENT_ID` | For REST-triggered launch only | Zoom Marketplace app Client ID |
| `ZOOM_CLIENT_SECRET` | For REST-triggered launch only | Zoom Marketplace app Client Secret |
| `ZOOM_ACCOUNT_ID` | For REST-triggered launch only | Zoom account ID |
| `ZOOM_RTMS_WEBHOOK_SECRET` | Yes | Event Subscription secret token — verifies Zoom's webhook signature |
| `ZOOM_RTMS_WEBHOOK_PORT` | No | Webhook HTTP port (default `8899`) |
| `ZOOM_PANEL_FEED_PORT` | No | Panel WebSocket port (default `8900`) |
| `N2N_ZOOM_CHANNEL_HOST` | No | Border host for the loopback channel (default `127.0.0.1`) |
| `N2N_ZOOM_CHANNEL_PORT` | Yes, to reach the Border | Must match the Border daemon's own `N2N_ZOOM_CHANNEL_PORT` |
| `N2N_ZOOM_CHANNEL_SECRET` | Yes, to reach the Border | Shared local secret, must match the Border's env |

## Transport

**stdio** (JSON-RPC 2.0) via FastMCP, same as every other NetGeniusClaw MCP server. The webhook/panel-feed/channel-client services above run as background threads/tasks alongside the stdio loop, started at import time.

## Known Environment Limitations (honest, not hidden)

- **Zoom's official RTMS Python SDK** is not resolvable from a public index in the environment this server was authored in — `rtms_listener.py` imports it defensively and degrades to a clearly-logged no-op (webhook receipt, extractor, panel feed, and MCP tools all still work) if it isn't installed. Install it per Zoom's own distribution instructions for live meeting signals.
- **Official Zoom Meetings MCP** exact tool name/credential shape is still being confirmed against Zoom's connector setup flow (research.md R6) — `zoom_search_historical_meetings` returns an explicit "not yet configured" note rather than a fabricated result until that's wired.
- **Layers API "Camera mode"** (the optional camera-overlay avatar) requires Zoom's own Controller-mode entitlement/app review (research.md R8) — implemented in `ui/netclaw-zoom-app/overlay.js` per design, but live verification is an operator step.
- **Device-write approval correlation** (`InvestigationRequest.write_action_detected`/`approval_ref`): the fields exist for audit correlation, but there is no signal today surfaced back from `run_agent_turn` distinguishing "holding on a pending device-write approval" from "still thinking" — documented in detail in `bgp/federation/zoom_channel.py`'s `_run_investigation`. The approval gate itself is NOT bypassed; this is a visibility gap in the Zoom-facing audit record, not a safety gap.

## Installation

```bash
cd mcp-servers/zoom-rtms-mcp/
pip install -r requirements.txt
```

## Testing

```bash
cd mcp-servers/zoom-rtms-mcp/
python3 -m pytest tests/ -v
```
