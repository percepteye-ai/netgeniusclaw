"""Feature 108 / US1: endpoint stability for Cloudflare Tunnel transport.

Proves that a claw using cloudflare_tunnel transport has a durable, restart-
surviving endpoint address (SC-001) and that peers NOT using this feature
behave identically to before (SC-005 regression guard).

Store-level only — no real tunnel or network connection is involved. The point
is that the reconnect supervisor reads the same host:port after a "restart"
(fresh FederationManager over the same DB) regardless of whether the peer was
configured with cloudflare_tunnel or ngrok transport.
"""

from bgp.federation.manager import FederationManager

# Cloudflare-Tunnel-hosted peer
CF_PEER_AS = 65099
CF_PEER_RID = "10.255.255.1"
CF_PEER_IDENT = f"as{CF_PEER_AS}-{CF_PEER_RID}"
CF_HOST = "netclaw-en2n.byrnbaker.me"
CF_PORT = 7179

# ngrok peer (no transport specified — regression guard)
NGROK_PEER_AS = 65001
NGROK_PEER_RID = "4.4.4.4"
NGROK_PEER_IDENT = f"as{NGROK_PEER_AS}-{NGROK_PEER_RID}"
NGROK_HOST = "2.tcp.ngrok.io"
NGROK_PORT = 19432


# ---- T011: cloudflare_tunnel endpoint survives simulated restart (SC-001) ----

def test_cloudflare_tunnel_endpoint_survives_restart(tmp_path):
    """A peer configured with transport=cloudflare_tunnel persists its endpoint
    across a simulated restart (fresh FederationManager over the same DB)."""
    db_dir = str(tmp_path / "cf")

    # --- Phase 1: initial insert with cloudflare_tunnel transport ---
    mgr = FederationManager(base_dir=db_dir)
    mgr.upsert_peer(CF_PEER_AS, CF_PEER_RID,
                    endpoint_host=CF_HOST, endpoint_port=CF_PORT,
                    transport="cloudflare_tunnel")

    before = mgr.get_peer(CF_PEER_IDENT)
    assert before is not None, "peer must exist after upsert"
    assert before["endpoint_host"] == CF_HOST
    assert before["endpoint_port"] == CF_PORT
    assert before["transport"] == "cloudflare_tunnel"
    assert before["endpoint_updated_at"], "written endpoint must bump freshness"
    mgr.close()

    # --- Phase 2: simulated restart (fresh manager, same DB) ---
    restarted = FederationManager(base_dir=db_dir)
    after = restarted.get_peer(CF_PEER_IDENT)

    assert after is not None, "peer row must survive restart"
    assert after["endpoint_host"] == CF_HOST, "endpoint_host must be durable"
    assert after["endpoint_port"] == CF_PORT, "endpoint_port must be durable"
    assert after["transport"] == "cloudflare_tunnel", "transport must be durable"
    assert after["endpoint_updated_at"] == before["endpoint_updated_at"], \
        "freshness marker must survive restart unchanged"

    # The supervisor's next-dial target is exactly what get_peer returns — verify
    # byte-for-byte equality of the fields the reconnect logic consumes.
    assert (after["endpoint_host"], after["endpoint_port"], after["transport"]) == \
           (before["endpoint_host"], before["endpoint_port"], before["transport"])
    restarted.close()


# ---- T012: ngrok peer regression guard (SC-005) ----

def test_ngrok_peer_defaults_and_round_trips_unchanged(tmp_path):
    """A peer with no explicit transport (or transport=None) defaults to 'ngrok'
    and its endpoint-persistence behavior is byte-for-byte unchanged from the
    pre-108 baseline (feature 063)."""
    db_dir = str(tmp_path / "ngrok")

    # --- Phase 1: insert with no transport (mimics pre-108 callers) ---
    mgr = FederationManager(base_dir=db_dir)
    mgr.upsert_peer(NGROK_PEER_AS, NGROK_PEER_RID,
                    endpoint_host=NGROK_HOST, endpoint_port=NGROK_PORT)
    # transport=None → stored as 'ngrok' (the default)

    before = mgr.get_peer(NGROK_PEER_IDENT)
    assert before is not None
    assert before["endpoint_host"] == NGROK_HOST
    assert before["endpoint_port"] == NGROK_PORT
    assert before["transport"] == "ngrok", \
        "omitted transport must default to 'ngrok' (SC-005 contract)"
    assert before["endpoint_updated_at"], "endpoint freshness must be set"
    mgr.close()

    # --- Phase 2: restart round-trip ---
    restarted = FederationManager(base_dir=db_dir)
    after = restarted.get_peer(NGROK_PEER_IDENT)

    assert after is not None
    # Same endpoint persistence guarantees as 063's test_upsert_persists_endpoint
    assert after["endpoint_host"] == NGROK_HOST
    assert after["endpoint_port"] == NGROK_PORT
    assert after["transport"] == "ngrok"
    assert after["endpoint_updated_at"] == before["endpoint_updated_at"]

    # No unexpected fields appear — the key set is identical before/after.
    # (Guards against accidental schema additions that break callers.)
    assert set(before.keys()) == set(after.keys()), \
        "restart must not add or remove columns from get_peer() output"

    # The full row round-trips identically (byte-for-byte unchanged behavior).
    for key in before:
        assert after[key] == before[key], \
            f"field {key!r} changed across restart: {before[key]!r} → {after[key]!r}"
    restarted.close()


def test_ngrok_peer_no_unexpected_fields_vs_cloudflare(tmp_path):
    """Both cloudflare_tunnel and ngrok peers share the same column set —
    no transport-specific fields leak into the row that could break existing
    callers expecting only the baseline schema."""
    db_dir = str(tmp_path / "both")
    mgr = FederationManager(base_dir=db_dir)

    mgr.upsert_peer(CF_PEER_AS, CF_PEER_RID,
                    endpoint_host=CF_HOST, endpoint_port=CF_PORT,
                    transport="cloudflare_tunnel")
    mgr.upsert_peer(NGROK_PEER_AS, NGROK_PEER_RID,
                    endpoint_host=NGROK_HOST, endpoint_port=NGROK_PORT)

    cf_row = mgr.get_peer(CF_PEER_IDENT)
    ngrok_row = mgr.get_peer(NGROK_PEER_IDENT)

    # Both rows must have identical column sets
    assert set(cf_row.keys()) == set(ngrok_row.keys()), \
        "cloudflare_tunnel and ngrok peers must share the same schema"
    mgr.close()
