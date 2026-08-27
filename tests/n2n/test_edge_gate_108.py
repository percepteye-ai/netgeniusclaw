"""Feature 108 / US2: edge_gate is additive only — never affects PeerState or trust.

Confirms FR-004/FR-005: setting edge_gate=cloudflare_access for a peer does not
change its PeerState, consent status, trust model, or any other trust-bearing
computation. The edge_gate field is purely descriptive/display — it records that
an operator has configured Cloudflare Access externally, but the federation code
itself never reads it for any gating decision.

The live Cloudflare-side Access enforcement is validated via quickstart.md's
manual procedure, not unit-testable without a real Cloudflare account.
"""

from bgp.federation.manager import FederationManager, PeerState

PEER_A_AS = 65001
PEER_A_RID = "1.1.1.1"
PEER_A_IDENT = "as65001-1.1.1.1"

PEER_B_AS = 65002
PEER_B_RID = "2.2.2.2"
PEER_B_IDENT = "as65002-2.2.2.2"


def test_edge_gate_does_not_change_peer_state(manager):
    """Setting edge_gate=cloudflare_access on an existing peer must NOT alter
    its PeerState. A NOT_FEDERATED peer stays NOT_FEDERATED."""
    manager.upsert_peer(PEER_A_AS, PEER_A_RID)
    peer_before = manager.get_peer(PEER_A_IDENT)
    assert peer_before["state"] == PeerState.NOT_FEDERATED.value

    # Now set edge_gate — state must be untouched
    manager.upsert_peer(PEER_A_AS, PEER_A_RID, edge_gate="cloudflare_access")
    peer_after = manager.get_peer(PEER_A_IDENT)
    assert peer_after["state"] == PeerState.NOT_FEDERATED.value, (
        "edge_gate must never mutate PeerState"
    )


def test_edge_gate_does_not_affect_consent(manager):
    """After local_consent moves state to PENDING_REMOTE, setting edge_gate
    must NOT change the consent-derived state."""
    state = manager.local_consent(PEER_A_AS, PEER_A_RID)
    assert state == PeerState.CONSENT_PENDING_REMOTE

    peer_before = manager.get_peer(PEER_A_IDENT)
    assert peer_before["state"] == PeerState.CONSENT_PENDING_REMOTE.value

    # Apply edge_gate — state must remain consent-derived
    manager.upsert_peer(PEER_A_AS, PEER_A_RID, edge_gate="cloudflare_access")
    peer_after = manager.get_peer(PEER_A_IDENT)
    assert peer_after["state"] == PeerState.CONSENT_PENDING_REMOTE.value, (
        "edge_gate must not interfere with the consent state machine"
    )
    assert peer_after["edge_gate"] == "cloudflare_access"


def test_edge_gate_does_not_affect_trust_model(manager):
    """Setting edge_gate must not alter a peer's trust_model. The two fields
    are independent per FR-005."""
    manager.upsert_peer(PEER_A_AS, PEER_A_RID)
    manager.set_peer_trust(PEER_A_IDENT, "domain-verified",
                           claw_domain="peer-a.example.com")

    peer_before = manager.get_peer(PEER_A_IDENT)
    assert peer_before["trust_model"] == "domain-verified"

    # Now apply edge_gate — trust_model unchanged
    manager.upsert_peer(PEER_A_AS, PEER_A_RID, edge_gate="cloudflare_access")
    peer_after = manager.get_peer(PEER_A_IDENT)
    assert peer_after["trust_model"] == "domain-verified", (
        "edge_gate must never modify trust_model"
    )
    assert peer_after["claw_domain"] == "peer-a.example.com", (
        "edge_gate must not clobber claw_domain"
    )
    assert peer_after["edge_gate"] == "cloudflare_access"


def test_edge_gate_independent_between_peers(manager):
    """Peer A's edge_gate=cloudflare_access must not leak to Peer B. Each peer's
    edge_gate is stored per-row, not globally."""
    manager.upsert_peer(PEER_A_AS, PEER_A_RID, edge_gate="cloudflare_access")
    manager.upsert_peer(PEER_B_AS, PEER_B_RID)  # default → edge_gate='none'

    peer_a = manager.get_peer(PEER_A_IDENT)
    peer_b = manager.get_peer(PEER_B_IDENT)

    assert peer_a["edge_gate"] == "cloudflare_access"
    assert peer_b["edge_gate"] == "none", (
        "Peer A's edge_gate must not affect Peer B"
    )

    # Verify states are also independent
    assert peer_a["state"] == PeerState.NOT_FEDERATED.value
    assert peer_b["state"] == PeerState.NOT_FEDERATED.value


def test_edge_gate_toggle_is_reversible(manager):
    """edge_gate can be set to cloudflare_access and back to 'none' without
    side effects on peer state. The field round-trips correctly."""
    manager.upsert_peer(PEER_A_AS, PEER_A_RID)
    peer_initial = manager.get_peer(PEER_A_IDENT)
    assert peer_initial["edge_gate"] == "none"
    assert peer_initial["state"] == PeerState.NOT_FEDERATED.value

    # Toggle ON
    manager.upsert_peer(PEER_A_AS, PEER_A_RID, edge_gate="cloudflare_access")
    peer_on = manager.get_peer(PEER_A_IDENT)
    assert peer_on["edge_gate"] == "cloudflare_access"
    assert peer_on["state"] == PeerState.NOT_FEDERATED.value, (
        "state must be unchanged after enabling edge_gate"
    )

    # Toggle OFF
    manager.upsert_peer(PEER_A_AS, PEER_A_RID, edge_gate="none")
    peer_off = manager.get_peer(PEER_A_IDENT)
    assert peer_off["edge_gate"] == "none"
    assert peer_off["state"] == PeerState.NOT_FEDERATED.value, (
        "state must be unchanged after disabling edge_gate"
    )
