---
name: remote-exposure
description: Configure or review remote and Internet access to gjl through Gate or an intentionally tunnel-published Door, including Cloudflare Tunnel, ngrok, Tailscale Funnel, TLS passthrough, mTLS, and ingress authentication.
---

# Remote and tunneled access

Use the [remote access guide](../../docs/remote-exposure.md) for gjl listener and Route fields. Use [gjl operations](../gjl-operations/SKILL.md) for CLI and Desktop navigation.

## Choose the product path first

Recommend **Gate** when traffic crosses the Internet, multiple people share access, or one provider account or policy boundary is shared. Gate is the network-facing role and supports TLS, paired-Door mTLS, CIDR policy, shared Route enforcement, and credential injection.

Door is a local-device role. A user may deliberately publish its loopback data listener through a tunnel, but explain that this places a local credential and policy boundary behind third-party ingress. Require a separate ingress authentication layer and keep the final choice with the user.

| Need | Preferred path | Required boundary |
| --- | --- | --- |
| Remote gjl clients with device identity | `Door → Gate → provider` | Raw TCP passthrough so Gate receives the Door certificate and enforces `gate_paired_door_mtls` |
| Direct clients on an independently restricted network | `client → Gate → provider` | `gate_agentless_tls` plus independent client access control; server TLS alone does not authenticate the client |
| Exceptional publication of one local Door | `client → tunnel auth/sanitizer → Door → provider` | Door remains loopback-only; authenticate before Door and remove ingress credentials before relay |

## Work from the actual TLS path

1. Inspect the installed surfaces before changing them: `gjl help`, `gjl config get`, `gjl route list`, `gjl listener list`, `gjl gate certificate status`, and `gjl tls-material status`. Check the installed tunnel client's version and help. Vendor commands and plan limits change.
2. Draw the path from client to provider and mark every TLS termination point. If Gate must verify a paired Door, select a raw TCP mode that carries the inner Gate TLS session unchanged. An HTTP/HTTPS tunnel or an edge `terminate-tls` action ends that session and cannot preserve gjl's paired-Door mTLS.
3. Read only the reference for the chosen ingress:
   - [Cloudflare Tunnel](references/cloudflare-tunnel.md)
   - [ngrok](references/ngrok.md)
   - [Tailscale Funnel](references/tailscale-funnel.md)
4. Configure the gjl side with the current configuration revision. A Gate listener uses an explicit IP:port, Gate-owned Route, TLS material references, and explicit `allowed_cidrs`. A Door listener stays on loopback with `door_loopback_plaintext`; a tunnel publishes a local authentication proxy or that loopback data port, never management IPC.
5. Create or modify vendor-side tunnels only when the user requested that external change. Otherwise, produce the exact configuration and verification plan without changing their tunnel account.
6. Verify the complete path with [the exposure checklist](references/security-checklist.md), including a harmless streaming request and negative authentication tests.

## Preserve these boundaries

- `force_shared` replaces provider authentication; it does not authenticate a remote client. Do not count an arbitrary provider bearer header as ingress authentication.
- Prefer a dedicated ingress credential header over `Authorization`, because `Authorization` may carry provider authentication. Validate the ingress credential before gjl and remove it, along with tunnel identity assertions, before forwarding. Unknown headers can otherwise reach the provider.
- Raw TCP connectors normally make Gate observe the local connector address. Set `allowed_cidrs` for the address Gate actually sees and enforce original-client IP restrictions at the tunnel edge when available. gjl does not parse the PROXY protocol, so do not send PROXY protocol records directly to a Door or Gate listener.
- Never expose the local management socket or named pipe. Do not add a localhost TCP management endpoint.
- Determine whether the tunnel provider can decrypt provider request bodies. Layer 7 termination makes plaintext available at that termination point; raw TCP around the inner Gate TLS session does not. Disable request-body capture, replay, and verbose wire logging in the tunnel layer.
- Keep tunnel credentials, Access service tokens, JWTs, client keys, provider credentials, and captured bodies out of configuration examples, command arguments, chat output, and general logs.
