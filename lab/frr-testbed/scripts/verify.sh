#!/usr/bin/env bash
# Verify FRR lab testbed — IPv6-only (OSPFv3 + MP-BGP IPv6 unicast)
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}PASS${NC}  $1"; }
fail() { echo -e "  ${RED}FAIL${NC}  $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo -e "  ${YELLOW}SKIP${NC}  $1"; }

ERRORS=0

echo "=== NetClaw FRR Lab Verification (IPv6-only) ==="
echo ""

# --- Container health ---
echo "--- Container Status ---"
for c in netclaw-edge1 netclaw-core netclaw-edge2; do
  if docker ps --format '{{.Names}}' | grep -q "^${c}$"; then
    pass "$c running"
  else
    fail "$c not running"
  fi
done
echo ""

# --- OSPFv3 convergence ---
echo "--- OSPFv3 Neighbors ---"
EDGE1_OSPF=$(docker exec netclaw-edge1 vtysh -c "show ipv6 ospf6 neighbor" 2>/dev/null || echo "")
if echo "$EDGE1_OSPF" | grep -q "Full"; then
  pass "Edge1 has OSPFv3 Full adjacency"
else
  fail "Edge1 OSPFv3 not converged (expected Full with Core)"
fi

CORE_OSPF=$(docker exec netclaw-core vtysh -c "show ipv6 ospf6 neighbor" 2>/dev/null || echo "")
CORE_FULL=$(echo "$CORE_OSPF" | grep -c "Full" || echo "0")
if [ "$CORE_FULL" -ge 2 ]; then
  pass "Core has $CORE_FULL OSPFv3 Full adjacencies (Edge1 + Edge2)"
else
  fail "Core has only $CORE_FULL OSPFv3 Full adjacencies (expected 2)"
fi

EDGE2_OSPF=$(docker exec netclaw-edge2 vtysh -c "show ipv6 ospf6 neighbor" 2>/dev/null || echo "")
if echo "$EDGE2_OSPF" | grep -q "Full"; then
  pass "Edge2 has OSPFv3 Full adjacency"
else
  fail "Edge2 OSPFv3 not converged (expected Full with Core)"
fi
echo ""

# --- Loopback reachability via OSPFv3 routing table ---
# Capture full output before grep — avoids set -o pipefail + grep -q SIGPIPE race
echo "--- Loopback Reachability (OSPFv3 routing table) ---"
E1_ROUTES=$(docker exec netclaw-edge1 ip -6 route show 2>/dev/null || true)
if echo "$E1_ROUTES" | grep -q "^fd00::2"; then
  pass "Edge1 has OSPFv3 route to Core loopback fd00::2"
else
  fail "Edge1 has no route to Core loopback fd00::2"
fi
if echo "$E1_ROUTES" | grep -q "^fd00::3"; then
  pass "Edge1 has OSPFv3 route to Edge2 loopback fd00::3"
else
  fail "Edge1 has no route to Edge2 loopback fd00::3"
fi
echo ""

# --- MP-BGP IPv6 unicast convergence ---
# FRR summary line format when Established: <nbr> <V> <AS> <Rcvd> <Sent> <Tbl> <InQ> <OutQ> <UpTime> <PfxRcvd> <PfxSnt> [Desc]
# When not Established, Up/Down shows "never" and State/PfxRcd shows text (Active, Idle, etc.)
echo "--- MP-BGP IPv6 Unicast Sessions ---"
CORE_BGP=$(docker exec netclaw-core vtysh -c "show bgp ipv6 unicast summary" 2>/dev/null || echo "")
if echo "$CORE_BGP" | grep "fd00::1" | grep -qvE "Active|Idle|Connect|OpenSent|never"; then
  pass "Core iBGP → Edge1 (fd00::1) Established"
else
  fail "Core missing iBGP session to Edge1 (fd00::1)"
fi
if echo "$CORE_BGP" | grep "fd00::3" | grep -qvE "Active|Idle|Connect|OpenSent|never"; then
  pass "Core iBGP → Edge2 (fd00::3) Established"
else
  fail "Core missing iBGP session to Edge2 (fd00::3)"
fi

EDGE1_BGP=$(docker exec netclaw-edge1 vtysh -c "show bgp ipv6 unicast summary" 2>/dev/null || echo "")
if echo "$EDGE1_BGP" | grep "fd00::2" | grep -qvE "Active|Idle|Connect|OpenSent|never"; then
  pass "Edge1 iBGP → Core (fd00::2) Established"
else
  fail "Edge1 missing iBGP session to Core (fd00::2)"
fi
echo ""

# --- Route propagation ---
echo "--- IPv6 Route Propagation ---"
if docker exec netclaw-edge1 vtysh -c "show bgp ipv6 unicast" 2>/dev/null | grep -q "fd00:dead:beef::/48"; then
  pass "Edge1 sees fd00:dead:beef::/48 (from Edge2 via RR)"
else
  fail "Edge1 missing fd00:dead:beef::/48"
fi
if docker exec netclaw-edge2 vtysh -c "show bgp ipv6 unicast" 2>/dev/null | grep -q "fd00::1"; then
  pass "Edge2 sees fd00::1/128 (Edge1 loopback via RR)"
else
  fail "Edge2 missing fd00::1/128"
fi
echo ""

# --- GRE tunnel + eBGP to WSL NetClaw (optional) ---
echo "--- GRE Tunnel (host side) ---"
if ip tunnel show gre-netclaw &>/dev/null; then
  pass "GRE tunnel gre-netclaw exists"
  if ping6 -c 1 -W 2 fd00:ee::0 &>/dev/null; then
    pass "GRE inner reachable (fd00:ee::0 — Edge1 side)"
  else
    fail "GRE inner fd00:ee::0 unreachable"
  fi
  if ip -6 addr show dev lo 2>/dev/null | grep -q "fd00::4"; then
    pass "WSL identity fd00::4/128 present on lo"
  else
    warn "WSL identity fd00::4/128 missing (run setup-gre.sh)"
  fi
else
  warn "GRE tunnel not configured (run scripts/setup-gre.sh)"
fi
echo ""

# --- eBGP to WSL NetClaw ---
echo "--- eBGP to WSL NetClaw ---"
EDGE1_NETCLAW=$(docker exec netclaw-edge1 vtysh -c "show bgp ipv6 unicast summary" 2>/dev/null || echo "")
if echo "$EDGE1_NETCLAW" | grep "fd00:ee::1" | grep -qvE "Active|Idle|Connect|OpenSent|never"; then
  pass "Edge1 eBGP → WSL NetClaw (fd00:ee::1) Established"
else
  warn "WSL NetClaw eBGP not Established (BGP daemon IPv6 peer required)"
fi
echo ""

# --- Summary ---
echo "==========================="
if [ "$ERRORS" -eq 0 ]; then
  echo -e "${GREEN}All checks passed${NC}"
else
  echo -e "${RED}$ERRORS check(s) failed${NC}"
fi
exit "$ERRORS"
