"""Feature 108 (T015): local Cloudflare Tunnel health probe.

Checks whether this claw's own tunnel transport is healthy — independent of
any specific peer's state. Consumed by /n2n/health and /n2n/faults (FR-007).

Returns: "true" (healthy), "false" (unhealthy), or "n/a" (not using cf tunnel).
"""

import logging
import socket
import subprocess

logger = logging.getLogger("n2n.transport_health")


def probe_local_transport(peers: list, *, enabled: bool = True) -> str:
    """Check whether the local Cloudflare Tunnel is healthy.

    Args:
        peers: list of peer dicts from manager.list_peers()
        enabled: whether health checking is enabled (from N2N_TRANSPORT_HEALTH_CHECK env)

    Returns:
        "true"  — tunnel hostname resolves and cloudflared service is active
        "false" — tunnel hostname doesn't resolve OR cloudflared service is not active
        "n/a"   — health check disabled OR no peer uses cloudflare_tunnel transport
    """
    if not enabled:
        return "n/a"

    # Find any peer (or self-record) using cloudflare_tunnel
    cf_peers = [p for p in peers if (p.get("transport") or "ngrok") == "cloudflare_tunnel"]
    if not cf_peers:
        return "n/a"

    # Check 1: is the local cloudflared service active?
    # Uses systemctl --user (matching the durable-service pattern from T009)
    if not _check_cloudflared_active():
        logger.debug("transport_health: cloudflared service not active")
        return "false"

    # Check 2: does the configured tunnel hostname resolve?
    # Use the first cloudflare_tunnel peer's endpoint_host as the hostname to probe.
    hostname = cf_peers[0].get("endpoint_host")
    if hostname and not _hostname_resolves(hostname):
        logger.debug("transport_health: hostname %s does not resolve", hostname)
        return "false"

    return "true"


def _check_cloudflared_active() -> bool:
    """Check if any cloudflared systemd user service is active.

    Returns False when systemctl is unavailable (container environments, macOS)
    rather than crashing — the probe degrades gracefully to "can't determine."
    """
    try:
        result = subprocess.run(
            ["systemctl", "--user", "list-units", "--type=service",
             "--state=active", "--plain", "--no-legend"],
            capture_output=True, text=True, timeout=5,
        )
        return "cloudflared" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # systemctl not available (container, macOS, missing binary) — can't determine
        return False


def _hostname_resolves(hostname: str) -> bool:
    """Check if a hostname resolves via DNS (any address family, any record type)."""
    try:
        socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return True
    except (socket.gaierror, OSError):
        return False
