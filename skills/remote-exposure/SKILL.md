---
name: remote-exposure
description: Set up or review gjl Gate access for remote clients, especially paired Door mTLS, Gate listeners, TLS material, and source CIDR checks.
---

# Remote Gate access

Use the [remote access guide](../../docs/remote-exposure.md) for the exact listener fields and test procedure. Use [gjl operations](../gjl-operations/SKILL.md) for CLI and Desktop navigation.

1. Choose the client path. A paired Door on a user- or organization-operated private network uses `gate_paired_door_mtls`. Direct agentless clients use `gate_agentless_tls` only when the network independently restricts client access: this mode authenticates the Gate server, not the client.
2. On Gate, inspect `gjl config get`, `gjl gate certificate status`, `gjl tls-material status`, and `gjl tls-material catalog`. Create a Gate-owned Route and selected credential, then a TLS Gate listener with an explicit IP:port, `route_id`, server identity reference, client trust reference for paired Doors, and narrow `allowed_cidrs`. Certificate paths belong in the protected TLS catalog, not the listener JSON.
3. For Door → Gate, configure the Door Route with the HTTPS Gate upstream, expected server name, server trust reference, and paired client identity. Door and Gate each apply their own Route rules. Vault, if used, exchanges credential RPCs only; it never receives the provider request body.
4. Apply each change using the latest revision (`gjl route put --expected-revision ...`, `gjl listener put --expected-revision ...`). Verify with `gjl doctor`, active configuration, a harmless request, rejection of an unpaired client, rejection outside the allowed CIDRs, and incremental response streaming.

Keep Door listeners on loopback and management IPC local. `force_shared` ignores inbound credentials, so an arbitrary bearer header does not authenticate an agentless Gate client. A tunnel or reverse proxy can carry provider bodies and change the source IP Gate sees; review that boundary before using one. Use the [verification checklist](references/security-checklist.md) for an exposure review.
