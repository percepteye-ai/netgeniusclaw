"""Feature 108 / Phase 2: transport and edge_gate field primitives.

Verifies T003/T004/T005 at the store level:
  - default values for new peers (SC-005 regression guard)
  - explicit values round-trip through upsert/get/list
  - metadata-only upsert doesn't clobber transport/edge_gate
  - edge_gate is independent of transport (FR-005)
"""

PEER_AS = 65001
PEER_RID = "4.4.4.4"
PEER_IDENT = "as65001-4.4.4.4"

# Second peer for list_peers test
PEER2_AS = 65002
PEER2_RID = "5.5.5.5"
PEER2_IDENT = "as65002-5.5.5.5"


# ---- SC-005: defaults for new peers ----------------------------------------

def test_new_peer_defaults_to_ngrok_none(manager):
    """A peer inserted with no explicit transport/edge_gate args must default to
    ('ngrok', 'none') — the zero-regression guard for existing rows (SC-005)."""
    manager.upsert_peer(PEER_AS, PEER_RID)
    p = manager.get_peer(PEER_IDENT)
    assert p is not None, "peer should exist after upsert"
    assert p["transport"] == "ngrok", "default transport must be 'ngrok'"
    assert p["edge_gate"] == "none", "default edge_gate must be 'none'"


# ---- Explicit values round-trip ---------------------------------------------

def test_explicit_transport_persists(manager):
    """An explicitly-supplied transport value must round-trip through get_peer."""
    manager.upsert_peer(PEER_AS, PEER_RID, transport="cloudflare_tunnel")
    p = manager.get_peer(PEER_IDENT)
    assert p["transport"] == "cloudflare_tunnel"


def test_explicit_edge_gate_persists(manager):
    """An explicitly-supplied edge_gate value must round-trip through get_peer."""
    manager.upsert_peer(PEER_AS, PEER_RID, edge_gate="cloudflare_access")
    p = manager.get_peer(PEER_IDENT)
    assert p["edge_gate"] == "cloudflare_access"


# ---- Metadata-only upsert preserves transport/edge_gate ---------------------

def test_metadata_upsert_preserves_transport(manager):
    """A metadata-only upsert (e.g. display_name) must not overwrite transport."""
    manager.upsert_peer(PEER_AS, PEER_RID, transport="cloudflare_tunnel")
    # Now upsert with only display_name — transport must be untouched
    manager.upsert_peer(PEER_AS, PEER_RID, display_name="renamed")
    p = manager.get_peer(PEER_IDENT)
    assert p["transport"] == "cloudflare_tunnel", (
        "metadata-only upsert must not clobber transport"
    )


def test_metadata_upsert_preserves_edge_gate(manager):
    """A metadata-only upsert (e.g. endpoint_host) must not overwrite edge_gate."""
    manager.upsert_peer(PEER_AS, PEER_RID, edge_gate="cloudflare_access")
    # Now upsert with only endpoint_host — edge_gate must be untouched
    manager.upsert_peer(PEER_AS, PEER_RID, endpoint_host="new.host.io")
    p = manager.get_peer(PEER_IDENT)
    assert p["edge_gate"] == "cloudflare_access", (
        "metadata-only upsert must not clobber edge_gate"
    )


# ---- FR-005: edge_gate is independent of transport --------------------------

def test_transport_and_edge_gate_independent(manager):
    """Setting transport must not imply edge_gate, and vice versa (FR-005:
    edge_gate is never implied by transport selection)."""
    # Set transport only — edge_gate stays at default
    manager.upsert_peer(PEER_AS, PEER_RID, transport="cloudflare_tunnel")
    p = manager.get_peer(PEER_IDENT)
    assert p["transport"] == "cloudflare_tunnel"
    assert p["edge_gate"] == "none", (
        "setting transport must not imply an edge_gate"
    )

    # Now set edge_gate separately — transport must be unchanged
    manager.upsert_peer(PEER_AS, PEER_RID, edge_gate="cloudflare_access")
    p = manager.get_peer(PEER_IDENT)
    assert p["transport"] == "cloudflare_tunnel", (
        "setting edge_gate must not change transport"
    )
    assert p["edge_gate"] == "cloudflare_access"


# ---- list_peers includes transport fields -----------------------------------

def test_list_peers_includes_transport_fields(manager):
    """list_peers must return transport and edge_gate per peer, with correct
    values for peers configured differently."""
    manager.upsert_peer(PEER_AS, PEER_RID, transport="cloudflare_tunnel",
                        edge_gate="cloudflare_access")
    manager.upsert_peer(PEER2_AS, PEER2_RID)  # defaults: ngrok / none

    peers = manager.list_peers()
    assert len(peers) == 2

    by_ident = {p["identity"]: p for p in peers}

    p1 = by_ident[PEER_IDENT]
    assert p1["transport"] == "cloudflare_tunnel"
    assert p1["edge_gate"] == "cloudflare_access"

    p2 = by_ident[PEER2_IDENT]
    assert p2["transport"] == "ngrok"
    assert p2["edge_gate"] == "none"
