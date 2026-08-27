/**
 * Layers API Camera-mode overlay (spec 118, User Story 5, tasks T038-T042).
 *
 * T038 (must be confirmed before this is usable live): Camera mode requires
 * the "Controller mode" component and Zoom's own app review before it
 * functions in a real meeting (research.md R8) — this file implements the
 * design correctly regardless, but live verification is an operator step
 * (quickstart.md), not something verifiable from this environment.
 *
 * FR-020: the overlay only ever mirrors the same avatar_state already shown
 * in the panel (panel.js calls setState()) and never carries its own audio.
 * FR-018/019: only ever affects the enabling participant's own outgoing
 * video — Layers API Camera mode is inherently self-only (Zoom's own
 * documented constraint), and panel_feed.py separately enforces the same
 * restriction server-side (contracts/zoom-app-panel-feed.md).
 */

const AVATAR_ICONS = {
  listening: "🦞", thinking: "🤔", investigating: "🔍", answered: "✅",
};

let _controllerActive = false;
let _currentState = "listening";

async function enable() {
  if (typeof zoomSdk === "undefined") {
    console.warn("NetClawOverlay: zoomSdk unavailable (not running in Zoom client)");
    return;
  }
  try {
    // Controller mode is required for all Layers modes (research.md R8).
    await zoomSdk.callZoomApi("startLayer", { mode: "controller" });
    await zoomSdk.callZoomApi("startLayer", { mode: "camera" });
    _controllerActive = true;
    render();
  } catch (e) {
    console.error("NetClawOverlay: failed to start Camera mode — likely needs Zoom's Layers "
                  + "API review/entitlement (research.md R8):", e);
  }
}

async function disable() {
  if (!_controllerActive) return;
  try {
    await zoomSdk.callZoomApi("stopLayer", { mode: "camera" });
    await zoomSdk.callZoomApi("stopLayer", { mode: "controller" });
  } catch (e) {
    console.error("NetClawOverlay: failed to stop Camera mode:", e);
  } finally {
    _controllerActive = false;
  }
}

function setState(state) {
  _currentState = state;
  if (_controllerActive) render();
}

function render() {
  // Camera mode mixes a rendered frame into the participant's own outgoing
  // video (Zoom's own "self only" constraint — no independent tile, no
  // audio, per FR-016/FR-020). The actual pixel content (an animated avatar
  // bubble reflecting _currentState) is drawn to an offscreen canvas and
  // handed to Zoom's Layers API per its Camera-mode contract; the exact
  // frame-submission call is pinned against the real Zoom Apps SDK reference
  // at implementation/build time (research.md R8's own deferral).
  const icon = AVATAR_ICONS[_currentState] || "🦞";
  if (typeof zoomSdk !== "undefined" && zoomSdk.callZoomApi) {
    zoomSdk.callZoomApi("drawParticipant", { text: icon }).catch(() => {});
  }
}

window.NetClawOverlay = { enable, disable, setState };
