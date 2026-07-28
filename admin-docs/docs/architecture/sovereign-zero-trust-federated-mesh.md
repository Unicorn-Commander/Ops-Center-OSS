# Sovereign Zero-Trust Federated Mesh

The canonical name for the Unicorn Commander platform architecture. Use
this name consistently across all decks, RFPs, marketing material,
technical specifications, and customer communications.

## The four-word headline

**Sovereign Zero-Trust Federated Mesh**

Each word maps to a structural property of the platform — none is
decorative.

| Word | Property |
|---|---|
| **Sovereign** | Each instance owns its users, data, agents, and policy boundary. Self-determined operations; no external authority required. |
| **Zero-Trust** | No implicit trust between instances. Every cross-instance request is authenticated and authorized at the time of the request. Aligns with NIST 800-207 and Executive Order 14028 mandates. |
| **Federated** | Cross-instance trust via standard protocols (OIDC, OAuth 2.0, SAML). Identity, agent state, and operational metadata propagate via well-known interop primitives. |
| **Mesh** | Any-to-any topology. Peers can promote, replicate, fail over, and succeed each other. No fixed hub; deployers configure trust relationships per-pair. |

## Full descriptor (datasheets, RFPs, technical specifications)

> A Sovereign Zero-Trust Federated Mesh supporting both centralized and
> decentralized topologies, with cross-instance state replication,
> automatic leader promotion, line-of-succession failover, and
> configurable per-peer trust relationships. Each instance is
> self-sovereign over its users and data; identity federation, agent
> state synchronization, and operational metadata propagate across the
> mesh under zero-trust authentication on every hop.

## Boardroom one-liner (executive decks, customer-facing material)

> Sovereign federated infrastructure — works centralized for compliance,
> decentralized for resilience, customer's choice.

## Audience-tuned variants

| Audience | Recommended phrasing |
|---|---|
| **CFO / Boardroom** | "Sovereign federated platform" — drop "mesh," reads as enterprise-grade. |
| **CTO** | "Sovereign Zero-Trust Federated Mesh" — full headline; gives the topology and the mechanism in one. |
| **DARPA** | "Resilient Sovereign Mesh" — emphasizes the auto-promotion and state-replication research angle. |
| **DoD procurement** | "Sovereign Zero-Trust Federated Mesh" — every word maps to a checkbox in the DoD reference architecture (FICAM + ZTA + Mission Partner Environment + JADC2 mesh framing). |

## Wording to avoid

| Avoid | Why |
|---|---|
| **"Decentralized" (alone)** | Too crypto-coded in 2026. Makes finance and defense readers skim. Use "centralized or decentralized" to communicate the *capability* without inheriting the cryptocurrency-association connotation. |
| **"Hub-and-spoke"** | Undersells the architecture. It describes one possible deployment configuration, not the architectural capability. |
| **"Mesh" (alone, CFO/CEO contexts)** | Reads as DIY / unmanaged in finance and legal contexts. Pair it with "Sovereign" or "Federated" for credibility. |
| **Acronyms (SZTFM, etc.)** | Kill spoken use, kill meaning. Stick to the four-word name. |

## Capability layers covered by the architecture

The combination of these capabilities is what justifies the
multi-domain compound name:

1. **Identity layer** — federated SSO between sovereign Keycloak realms,
   first-broker-login email-based auto-linking, configurable per-peer
   trust relationships (any instance can choose any other as
   authoritative, peer, or none).
2. **Topology layer** — mesh-shaped, supporting:
   - Centralized (one designated authoritative node, others spokes)
   - Decentralized (peer-to-peer, no fixed root)
   - Hybrid (regional hubs with peer-level cross-region trust)
3. **State layer** — agent memory, project state, and operational
   metadata replicate across the mesh with eventual or strong
   consistency depending on the data type.
4. **Security layer** — zero-trust on every cross-instance hop;
   authentication and authorization at request time, no implicit
   long-lived trust.
5. **Resilience layer** — automatic leader promotion, line-of-succession
   failover, mesh self-healing under partition.

## Why this is novel

The combination of *identity federation + agent state synchronization
+ automatic promotion across instances + zero-trust per-hop* is not
covered by any single existing standard or product. Closest analogs,
none of which cover the full picture:

| Analog | Covers | Doesn't cover |
|---|---|---|
| Matrix Protocol | Federation + state sync (for chat) | Agents, sovereignty primitives, leader election |
| Self-Sovereign Identity (W3C DIDs) | Sovereignty of *identity* | Agent runtime, state sync, mesh topology |
| Raft / Paxos consensus | Leader election, replicated state | Identity federation, zero-trust at scale |
| JADC2 (DoD mesh) | Resilient mesh networking | Application-layer identity and agent state |
| Kubernetes federation | Cross-cluster service sync | Identity sovereignty, zero-trust between peers |

Magic Unicorn synthesizes capabilities from four different domains
into one platform. The architecture name should reflect that synthesis
rather than borrow a term that only covers one slice.

## Usage rule

When writing any new artifact (technical doc, deck, blog, RFP response,
customer-facing material) that references the platform's structural
design, **start from the four-word name and the full descriptor above**.
Don't re-invent terminology — consistency is what makes the name
recognizable across audiences.

If a particular audience needs a tuned variant, use one of the rows in
the "Audience-tuned variants" table — those are pre-vetted to land in
that room.
