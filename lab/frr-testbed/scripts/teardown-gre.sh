#!/usr/bin/env bash
# Teardown GRE tunnel between host and Edge1 — IPv6-only (inner + outer)
set -euo pipefail

HOST_PEERING_IP="${HOST_PEERING_IP:-fd00:dc:ee::100}"
HOST_IDENTITY="${HOST_IDENTITY:-fd00::4}"

echo "=== Tearing Down GRE Tunnel (IPv6 inner + outer) ==="

echo "[1/4] Removing IPv6 host routes via GRE..."
ip -6 route del fd00::1/128   2>/dev/null || true
ip -6 route del fd00::2/128   2>/dev/null || true
ip -6 route del fd00::3/128   2>/dev/null || true
ip -6 route del fd00:12::/127 2>/dev/null || true
ip -6 route del fd00:23::/127 2>/dev/null || true

echo "[2/4] Removing WSL identity route from lo..."
ip -6 addr del "$HOST_IDENTITY/128" dev lo 2>/dev/null || true

echo "[3/4] Removing host GRE tunnel..."
ip -6 tunnel del gre-netclaw 2>/dev/null || true

echo "[4/4] Removing Edge1 GRE tunnel..."
docker exec netclaw-edge1 ip -6 tunnel del gre-netclaw 2>/dev/null || true

# Remove host IPv6 peering address from Docker bridge (underlay cleanup)
PEERING_BRIDGE=$(ip -6 route show fd00:dc:ee::/64 2>/dev/null | awk '{print $3}' || echo "")
if [ -n "$PEERING_BRIDGE" ]; then
  ip -6 addr del "$HOST_PEERING_IP/64" dev "$PEERING_BRIDGE" 2>/dev/null || true
fi

echo ""
echo "=== GRE Tunnel Removed ==="
