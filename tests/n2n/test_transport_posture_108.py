"""Feature 108 / US3: transport and edge-gate posture visibility.

Verifies:
  - probe_local_transport returns "n/a" when no peer uses cloudflare_tunnel
  - probe_local_transport returns "n/a" when disabled
  - probe_local_transport returns "false" when cloudflared is not active (mocked)
  - probe_local_transport returns "true" when cloudflared is active + hostname resolves (mocked)
  - probe_local_transport returns "false" when DNS resolution fails (mocked)
  - posture _channel_security includes by_transport and edge_gated counts
"""

import os
import sys

import pytest
from unittest.mock import patch, MagicMock

# Ensure protocol-mcp package is importable
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "mcp-servers", "protocol-mcp"))

from bgp.federation.transport_health import probe_local_transport
from bgp.federation.posture import _channel_security


# ---------------------------------------------------------------------------
# probe_local_transport tests
# ---------------------------------------------------------------------------

def test_probe_returns_na_when_no_cf_peers():
    """All peers have transport='ngrok' → returns 'n/a'."""
    peers = [
        {"transport": "ngrok", "endpoint_host": "a.ngrok.io"},
        {"transport": "ngrok", "endpoint_host": "b.ngrok.io"},
    ]
    assert probe_local_transport(peers) == "n/a"


def test_probe_returns_na_when_disabled():
    """Peers have cloudflare_tunnel but enabled=False → returns 'n/a'."""
    peers = [
        {"transport": "cloudflare_tunnel", "endpoint_host": "tunnel.example.com"},
    ]
    assert probe_local_transport(peers, enabled=False) == "n/a"


@patch("bgp.federation.transport_health._check_cloudflared_active", return_value=False)
def test_probe_returns_false_when_cloudflared_not_active(mock_check):
    """cloudflared service not active → returns 'false'."""
    peers = [
        {"transport": "cloudflare_tunnel", "endpoint_host": "tunnel.example.com"},
    ]
    assert probe_local_transport(peers) == "false"
    mock_check.assert_called_once()


@patch("bgp.federation.transport_health._hostname_resolves", return_value=True)
@patch("bgp.federation.transport_health._check_cloudflared_active", return_value=True)
def test_probe_returns_true_when_healthy(mock_check, mock_dns):
    """cloudflared active + hostname resolves → returns 'true'."""
    peers = [
        {"transport": "cloudflare_tunnel", "endpoint_host": "tunnel.example.com"},
    ]
    assert probe_local_transport(peers) == "true"
    mock_check.assert_called_once()
    mock_dns.assert_called_once_with("tunnel.example.com")


@patch("bgp.federation.transport_health._hostname_resolves", return_value=False)
@patch("bgp.federation.transport_health._check_cloudflared_active", return_value=True)
def test_probe_returns_false_when_dns_fails(mock_check, mock_dns):
    """cloudflared active but hostname doesn't resolve → returns 'false'."""
    peers = [
        {"transport": "cloudflare_tunnel", "endpoint_host": "tunnel.example.com"},
    ]
    assert probe_local_transport(peers) == "false"
    mock_check.assert_called_once()
    mock_dns.assert_called_once_with("tunnel.example.com")


# ---------------------------------------------------------------------------
# _channel_security transport visibility test
# ---------------------------------------------------------------------------

def test_posture_channel_security_includes_transport(manager):
    """_channel_security includes by_transport counts and edge_gated tally."""
    # Insert a cloudflare_tunnel peer and an ngrok peer via the real manager.
    manager.upsert_peer(
        peer_as=65001, router_id="1.1.1.1",
        display_name="cf-peer",
        endpoint_host="tunnel.example.com",
        transport="cloudflare_tunnel",
        edge_gate="cloudflare",
    )
    manager.upsert_peer(
        peer_as=65002, router_id="2.2.2.2",
        display_name="ngrok-peer",
        endpoint_host="abc.ngrok.io",
        transport="ngrok",
        edge_gate="none",
    )

    # Build a minimal mock service whose .manager is the real manager fixture.
    service = MagicMock()
    service.manager = manager
    # _channel_security accesses service.channels — provide empty dict (no live
    # TLS connections in unit test context).
    service.channels = {}
    service.cert_enforce = False
    service.cert_mode = False
    service.pq_mode = "opportunistic"
    service.pq_available = False

    result = _channel_security(service)

    # Verify transport aggregation (Feature 108 / T013).
    assert "by_transport" in result
    assert result["by_transport"]["cloudflare_tunnel"] == 1
    assert result["by_transport"]["ngrok"] == 1

    # Verify edge_gated count — only the cf-peer has edge_gate != "none".
    assert "edge_gated" in result
    assert result["edge_gated"] == 1
