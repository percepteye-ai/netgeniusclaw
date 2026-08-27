# FRR Lab Testbed

Three FRR routers for testing NetGeniusClaw's protocol participation. **IPv6-only**
— OSPFv3 and MP-BGP IPv6 unicast. There is no IPv4 anywhere in it; the configs
carry `no ip forwarding`.

## Topology

```
  host (AS 65001)          Edge1 (AS 65000)      Core (AS 65000, RR)    Edge2 (AS 65000)
  fd00::4/128              fd00::1/128           fd00::2/128            fd00::3/128
        │                        │                      │                     │
        └── GRE ─────────────────┤                      │                     │
            fd00:ee::/127        └──── OSPFv3 ──────────┴──── OSPFv3 ─────────┘
                                       fd00:12::/127          fd00:23::/127
            eBGP 65001↔65000           iBGP → RR            iBGP RR hub      iBGP → RR
```

Edge2 originates `fd00:dead:beef::/48`. Seeing that prefix on Edge1 is the
end-to-end proof that it travelled through the route reflector.

## Quick start

The three bridges are declared `external:` in `docker-compose.yml`, so **they
must exist before compose runs** — without this step `docker compose up` fails
with a missing-network error. They are IPv4-disabled deliberately, so no
container interface can pick up a v4 address:

```bash
docker network create --ipv4=false --ipv6 --subnet fd00:dc:12::/64 --gateway fd00:dc:12::fe --driver bridge frr-testbed_edge1-core
docker network create --ipv4=false --ipv6 --subnet fd00:dc:23::/64 --gateway fd00:dc:23::fe --driver bridge frr-testbed_core-edge2
docker network create --ipv4=false --ipv6 --subnet fd00:dc:ee::/64 --gateway fd00:dc:ee::fe --driver bridge frr-testbed_peering
```

```bash
docker compose up -d
sleep 15                        # OSPFv3 + BGP convergence
bash scripts/verify.sh
```

## Verify by hand

The commands are the v3/v6 forms. Their IPv4 equivalents return **empty output**
against this lab, which reads as "nothing is up" rather than as the wrong
question:

```bash
docker exec netclaw-edge1 vtysh -c "show ipv6 ospf6 neighbor"
docker exec netclaw-core  vtysh -c "show ipv6 ospf6 neighbor"

docker exec netclaw-core  vtysh -c "show bgp ipv6 unicast summary"
docker exec netclaw-edge1 vtysh -c "show bgp ipv6 unicast summary"

docker exec netclaw-edge1 vtysh -c "show bgp ipv6 unicast" | grep fd00:dead:beef::/48
docker exec netclaw-edge1 ip -6 route show
```

## Peering the host with the lab (optional)

`scripts/setup-gre.sh` builds an IPv6 GRE tunnel from the host to Edge1 and puts
`fd00::4/128` on the host's loopback, so the host can run eBGP into AS 65000.

```bash
sudo bash scripts/setup-gre.sh
sudo bash scripts/teardown-gre.sh
```

> **Linux host only.** It creates a GRE interface and a loopback address in the
> host's own network namespace. On macOS the containers run inside Docker
> Desktop's Linux VM, so the host has no namespace to attach to — the three
> routers still converge among themselves and every `docker exec` check above
> still works, but the host cannot become a BGP peer. Use a Linux host or VM if
> you need that fourth speaker.

## Networks

| Network | Subnet | Purpose |
|---------|--------|---------|
| `frr-testbed_edge1-core` | `fd00:dc:12::/64` | Edge1 ↔ Core underlay |
| `frr-testbed_core-edge2` | `fd00:dc:23::/64` | Core ↔ Edge2 underlay |
| `frr-testbed_peering` | `fd00:dc:ee::/64` | Edge1 exposed to the host |
| GRE inner | `fd00:ee::/127` | Host ↔ Edge1 (RFC 6164) |

Router loopbacks are `fd00::1` (edge1), `fd00::2` (core), `fd00::3` (edge2) and
`fd00::4` (host). Point-to-point links use `/127` per RFC 6164.

## Teardown

```bash
docker compose down
docker network rm frr-testbed_edge1-core frr-testbed_core-edge2 frr-testbed_peering
```
