"""Deterministic, rule-based recognizer for meeting transcript/chat lines
(research.md R2). Two responsibilities, deliberately combined in one module
because the safety boundary (US4/FR-009) has to run BEFORE anything is ever
constructed as a request — not as a downstream filter:

1. Classify an utterance as a genuine, present-tense, first-person
   investigation/action request, vs. hypothetical/past-tense/third-party
   remarks that must never be treated as a request at all (US4).
2. For genuine requests, extract location/technology/time-window (US1).

No LLM call happens here (research.md R2) — this is plain pattern matching,
auditable and testable as code.
"""

import re
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Known vocabulary (deterministic matching — extend as needed; not exhaustive
# by design, matches spec's own example: Toronto/BGP)
# ---------------------------------------------------------------------------

KNOWN_LOCATIONS = [
    "toronto", "ottawa", "montreal", "vancouver", "new york", "chicago",
    "dallas", "atlanta", "london", "frankfurt", "singapore", "tokyo",
]

KNOWN_TECHNOLOGIES = [
    "bgp", "ospf", "eigrp", "firewall", "vpn", "interface", "routing",
    "dns", "dhcp", "switch", "router", "load balancer", "circuit",
    "isp", "peer", "peering", "vlan", "mpls", "sd-wan", "wan",
]

# Hypothetical / suggestion markers — a sentence containing these about a
# change is never authorization (FR-009), regardless of what follows.
_HYPOTHETICAL_MARKERS = (
    "could we", "we could", "should we", "might want to", "maybe we",
    "what if we", "i guess we", "perhaps we", "we might", "it might be worth",
    "we should probably", "just thinking", "hypothetically",
)

# Past-tense / third-party attribution markers — a statement ABOUT a change,
# not a request FOR one.
_PAST_TENSE_THIRD_PARTY_MARKERS = (
    "they shut", "they disabled", "they configured", "they changed",
    "someone shut", "someone disabled", "someone changed", "was shut down by",
    "was disabled by", "last time we", "previously we", "they did that",
    "the other team", "already did", "had already",
)

# Direct imperative write-commands — genuine requests, but for a
# configuration-changing action (must go through the existing approval gate
# downstream, per research.md R7 — NOT suppressed, unlike the two lists above).
_WRITE_IMPERATIVE_VERBS = (
    "shut", "disable", "enable", "configure", "delete", "remove", "reload",
    "restart", "reboot", "reset", "set ", "change the config", "write erase",
)

# Investigative question markers — present-tense, first-person requests to
# look into something.
_INVESTIGATE_MARKERS = (
    "netclaw", "can you check", "can you look", "what happened", "what's going on",
    "why did", "why is", "is it down", "did we lose", "are we seeing",
    "can you investigate", "check whether", "what is the status", "how's the",
)

_WORD_NUMBERS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11",
    "twelve": "12", "fifteen": "15", "twenty": "20", "thirty": "30",
}
_NUMBER_WORD_RE = r"(?:\d+|" + "|".join(_WORD_NUMBERS.keys()) + ")"

_TIME_WINDOW_RE = re.compile(
    r"\b(?:about |around |roughly )?(" + _NUMBER_WORD_RE + r")\s*(minute|minutes|min|hour|hours)\s*(?:ago|back)\b",
    re.IGNORECASE,
)


@dataclass
class Classification:
    kind: str  # "investigate" | "write_command" | "suppressed" | "none"
    reason: str = ""


def classify(text: str) -> Classification:
    lowered = text.lower()

    # FR-009: hypothetical/past-tense/third-party — suppressed BEFORE anything
    # else is checked. A sentence can't be "hypothetical" and also acted on.
    for marker in _HYPOTHETICAL_MARKERS:
        if marker in lowered:
            return Classification("suppressed", f"hypothetical marker: {marker!r}")
    for marker in _PAST_TENSE_THIRD_PARTY_MARKERS:
        if marker in lowered:
            return Classification("suppressed", f"past-tense/third-party marker: {marker!r}")

    # Direct imperative write command — a genuine request, held for approval
    # downstream (not suppressed).
    for verb in _WRITE_IMPERATIVE_VERBS:
        if lowered.strip().startswith(verb) or f" {verb}" in lowered:
            # Guard against false positives like "we should probably shut..."
            # already caught above by the hypothetical check running first.
            return Classification("write_command", f"imperative verb: {verb.strip()!r}")

    # Investigation/read request
    for marker in _INVESTIGATE_MARKERS:
        if marker in lowered:
            return Classification("investigate", f"investigative marker: {marker!r}")

    # A location+technology+time-window combination with no explicit marker
    # still reads as a description of an event worth investigating (spec's
    # own example: "Toronto lost its BGP sessions about ten minutes ago").
    if _find_location(lowered) and _find_technology(lowered) and _TIME_WINDOW_RE.search(lowered):
        return Classification("investigate", "location+technology+time-window present")

    return Classification("none", "no recognized pattern")


def _find_location(lowered: str) -> Optional[str]:
    for loc in KNOWN_LOCATIONS:
        if loc in lowered:
            return loc.title()
    return None


def _find_technology(lowered: str) -> Optional[str]:
    for tech in KNOWN_TECHNOLOGIES:
        if tech in lowered:
            return tech.upper() if len(tech) <= 5 else tech.title()
    return None


def _find_time_window(lowered: str) -> Optional[str]:
    m = _TIME_WINDOW_RE.search(lowered)
    if not m:
        return None
    qty, unit = m.group(1), m.group(2)
    qty = _WORD_NUMBERS.get(qty.lower(), qty)
    return f"~{qty} {unit}"


@dataclass
class ExtractedFields:
    location: Optional[str]
    technology: Optional[str]
    time_window: Optional[str]


def extract_fields(text: str) -> ExtractedFields:
    lowered = text.lower()
    return ExtractedFields(
        location=_find_location(lowered),
        technology=_find_technology(lowered),
        time_window=_find_time_window(lowered),
    )
