/**
 * NetClaw Zoom App side panel (spec 118, tasks T021/T034/T035/T036/T037).
 * Connects to zoom-rtms-mcp's panel_feed WebSocket
 * (contracts/zoom-app-panel-feed.md), renders avatar/status/results, wires
 * Collaborate Mode + Guest Mode (US3), and offers the camera-overlay toggle
 * (US5, delegates the actual Layers API call to overlay.js).
 */

const AVATAR_ICONS = {
  listening: "🦞", thinking: "🤔", investigating: "🔍", answered: "✅",
};

let meetingUuid = null;
let participantId = null;
let ws = null;
let overlayEnabled = false;

const avatarEl = document.getElementById("avatar");
const statusEl = document.getElementById("status");
const topicEl = document.getElementById("topic");
const resultEl = document.getElementById("result");
const overlayBtn = document.getElementById("overlay-toggle");

function connect() {
  // Same-origin as the Home URL that served this panel (contracts: the
  // panel_feed server and the webhook/OAuth server share a host in this
  // feature's design, research.md R3).
  const wsUrl = (location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/";
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    statusEl.textContent = "Listening";
    // Only meeting_uuid is actually required to register this connection
    // server-side (panel_feed.py's _handler keys _connections purely on it —
    // participant_id is only used later for the camera-overlay own-feed
    // restriction). Requiring both here meant a getUserContext() failure
    // alone (confirmed live 2026-08-19: getMeetingContext() succeeded,
    // getUserContext() didn't, both live in the same try block so
    // participantId was silently left null) permanently prevented viewer
    // registration — the panel looked connected ("Listening") but never
    // received a single subsequent broadcast (thinking/investigating/
    // answered all vanished into an empty recipient set), with no error
    // visible anywhere.
    if (meetingUuid) {
      sendViewerJoined();
    } else {
      // Zoom's own getMeetingContext()/getUserContext() are rejected outright
      // on this app (confirmed live 2026-08-19: "No Permission for this API
      // [code:80004, reason:app_not_support]" on both — a Marketplace-side
      // app configuration gap, not something fixable here). This server
      // already knows the true meeting_uuid authoritatively from the RTMS
      // webhook, independent of the Zoom SDK, so ask it directly instead of
      // being permanently stuck with no way to ever identify this meeting.
      send({ type: "identify_by_active_meeting" });
    }
  };
  ws.onclose = () => {
    statusEl.textContent = "Disconnected — retrying…";
    statusEl.className = "degraded";
    setTimeout(connect, 3000);
  };
  ws.onerror = () => { /* onclose will fire and retry */ };
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    handleServerMessage(msg);
  };
}

function sendViewerJoined() {
  send({ type: "viewer_joined", meeting_uuid: meetingUuid, participant_id: participantId });
}

function send(msg) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
}

function handleServerMessage(msg) {
  if (msg.type === "identified") {
    // Response to identify_by_active_meeting — meetingUuid was null until
    // now, so the mismatch filter below would otherwise drop this.
    meetingUuid = msg.meeting_uuid;
    sendViewerJoined();
    return;
  }
  if (msg.meeting_uuid && msg.meeting_uuid !== meetingUuid) return;

  switch (msg.type) {
    case "avatar_state":
      avatarEl.textContent = AVATAR_ICONS[msg.state] || "🦞";
      statusEl.textContent = msg.state.charAt(0).toUpperCase() + msg.state.slice(1);
      statusEl.className = "";
      if (window.NetClawOverlay) window.NetClawOverlay.setState(msg.state);
      break;
    case "topic_detected":
      topicEl.style.display = "block";
      topicEl.textContent = [
        msg.location ? `Location: ${msg.location}` : null,
        msg.technology ? `Technology: ${msg.technology}` : null,
        msg.time_window ? `Time window: ${msg.time_window}` : null,
      ].filter(Boolean).join(" · ") || "Investigating detected topic…";
      break;
    case "investigation_result":
      resultEl.style.display = "block";
      resultEl.textContent = msg.answer_summary || "Could not complete this investigation.";
      break;
    case "connection_state":
      if (msg.state === "degraded") {
        statusEl.textContent = "Connection degraded";
        statusEl.className = "degraded";
      } else if (msg.state === "connecting") {
        statusEl.textContent = "Connecting…";
        statusEl.className = "connecting";
      }
      break;
  }
}

overlayBtn.addEventListener("click", async () => {
  overlayEnabled = !overlayEnabled;
  overlayBtn.textContent = overlayEnabled ? "Disable camera overlay" : "Enable camera overlay";
  overlayBtn.className = overlayEnabled ? "enabled" : "";
  send({
    type: overlayEnabled ? "camera_overlay_enable" : "camera_overlay_disable",
    meeting_uuid: meetingUuid, participant_id: participantId,
  });
  if (window.NetClawOverlay) {
    if (overlayEnabled) await window.NetClawOverlay.enable();
    else await window.NetClawOverlay.disable();
  }
});

// ---- Zoom Apps SDK: Collaborate Mode + Guest Mode (US3) --------------------

async function initZoomSdk() {
  if (typeof zoomSdk === "undefined") {
    // Not running inside the Zoom client (e.g. local dev) — fall back to a
    // query-string meeting_uuid so the panel is still testable standalone.
    const params = new URLSearchParams(location.search);
    meetingUuid = params.get("meeting_uuid") || "dev-meeting";
    participantId = params.get("participant_id") || "dev-participant";
    connect();
    return;
  }

  // Collaborate Mode capabilities (startCollaborate/joinCollaborate/
  // leaveCollaborate/onCollaborateChange) only actually work once this app
  // has passed Zoom's app review — until then, requesting them can make
  // zoomSdk.config() reject outright. Request core + Collaborate together
  // first, but fall back to core-only rather than letting one rejected
  // capability set kill the whole panel before it ever connects.
  const CORE_CAPS = ["getRunningContext", "getMeetingContext", "getUserContext", "onMeeting"];
  const COLLABORATE_CAPS = ["startCollaborate", "joinCollaborate", "leaveCollaborate", "onCollaborateChange"];
  let collaborateAvailable = true;
  try {
    await zoomSdk.config({ capabilities: [...CORE_CAPS, ...COLLABORATE_CAPS] });
  } catch (err) {
    console.warn("NetClaw: Collaborate Mode capabilities unavailable (app review pending?) — falling back to core capabilities.", err);
    collaborateAvailable = false;
    try {
      await zoomSdk.config({ capabilities: CORE_CAPS });
    } catch (err2) {
      console.error("NetClaw: zoomSdk.config failed even with core capabilities — falling back to standalone mode.", err2);
      const params = new URLSearchParams(location.search);
      meetingUuid = params.get("meeting_uuid") || "dev-meeting";
      participantId = params.get("participant_id") || "dev-participant";
      connect();
      return;
    }
  }

  // Split into two try/catch blocks (confirmed live 2026-08-19: a combined
  // block made it impossible to tell from the console which of the two calls
  // was actually the one throwing "No Permission for this API [code:80004,
  // reason:app_not_support]" — that ambiguity cost a full debugging round).
  try {
    const meetingContext = await zoomSdk.getMeetingContext();
    meetingUuid = meetingContext.meetingUUID;
  } catch (err) {
    console.error("NetClaw: getMeetingContext() failed — this is the critical one, no meeting_uuid means nothing can ever route:", err);
    // Last-resort fallback: Zoom sometimes appends meeting_uuid as a query
    // param on the Home URL launch even when the SDK call itself is denied.
    // Never falls back to a made-up value like "dev-meeting" here (unlike
    // the zoomSdk-undefined branch above) — a wrong meeting_uuid would
    // register this connection under a key nothing will ever push to,
    // identical in effect to never registering at all, just harder to debug.
    const params = new URLSearchParams(location.search);
    meetingUuid = params.get("meeting_uuid") || null;
  }

  try {
    const userContext = await zoomSdk.getUserContext();
    // Guest Mode (FR-012): an unauthenticated participant still has a
    // per-session participantId even without a Zoom login — treated
    // identically to an authenticated one by this panel and by panel_feed.py.
    participantId = userContext.participantId || userContext.screenName || "guest";
  } catch (err) {
    console.error("NetClaw: getUserContext() failed — camera-overlay own-feed restriction degrades to \"unknown\", viewer registration still proceeds on meeting_uuid alone:", err);
    participantId = "unknown-participant";
  }

  if (collaborateAvailable) {
    try {
      zoomSdk.onCollaborateChange((event) => {
        // Collaborate Mode (US3): every collaborator renders the same
        // meeting_uuid-scoped state via the shared panel_feed connection —
        // nothing extra needed here beyond making sure this connection is live.
        if (event.collaborateUUID && !ws) connect();
      });
    } catch (err) {
      console.warn("NetClaw: onCollaborateChange registration failed.", err);
    }
  }

  connect();
}

initZoomSdk();
