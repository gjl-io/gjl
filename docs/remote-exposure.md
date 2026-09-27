# Remote access and Internet tunnels

Gate is gjl's network-facing relay. Door is a local-device relay whose data
listener remains on loopback. Vault carries credential RPCs, not provider
traffic. Local management IPC is never an HTTP endpoint and must not be
published.

## Choose Door or Gate deliberately

Use Gate when access crosses the Internet, multiple people use the relay, or a
provider account, credential, or organization Route policy is shared. This is
the product-designed path for a network boundary.

A user may still publish a Door loopback data listener through Cloudflare
Tunnel, ngrok, Tailscale Funnel, or another tunnel. That is an exceptional
deployment choice rather than a different Door listener mode. Authenticate
clients in a separate tunnel or local proxy layer before Door, remove those
credentials before relay, and understand which tunnel components can read
provider request bodies. The final choice belongs to the operator.

| Client path | Transport and authentication |
| --- | --- |
| Paired `Door → Gate` | Prefer raw TCP passthrough. Gate terminates the inner TLS session and verifies the paired Door certificate. |
| Direct client → Gate | `gate_agentless_tls` authenticates the Gate server only. Add independent network or tunnel client authentication. |
| Tunnel → Door | Door stays `door_loopback_plaintext`. Terminate the tunnel at a loopback authentication and header-sanitizing proxy before Door. |

`force_shared` controls provider authentication. It is not remote-client
authentication, and an arbitrary bearer value does not secure an agentless
Gate or published Door.

## Prepare a paired-Door Gate listener

1. Provision the Gate server identity and paired-Door client trust through the
   protected TLS material catalog. The ordinary Route and listener
   configuration contains stable references, not certificate paths. Inspect
   `gjl gate certificate status`, `gjl tls-material status`, and `gjl
   tls-material catalog` on the Gate host.
2. Create a Gate Route (`role: "gate"`) and its selected provider credential.
   A Gate listener can bind only to a Gate Route.
3. Add a listener with `gjl listener put --expected-revision REV listener.json`.
   Replace the example address, references, CIDR, and Route ID with provisioned
   values. This is a listener object, not a complete configuration document:

```json
{
  "id": "team-gate",
  "role": "gate",
  "network": "tcp",
  "address": "127.0.0.1:8443",
  "transport_mode": "gate_paired_door_mtls",
  "server_identity_ref": "gate-server",
  "client_trust_ref": "paired-door-roots",
  "route_id": "team-provider",
  "allowed_cidrs": ["127.0.0.0/8"]
}
```

The loopback address above is appropriate when a tunnel connector runs on the
same host. For a direct private-network connection, bind the Gate listener to
the intended explicit interface address and use the actual Door source CIDRs.
Gate never accepts cleartext.

Configure the Door-to-Gate Route with the HTTPS tunnel or Gate address, the DNS
name covered by the Gate certificate, a paired client identity reference, and
a Gate trust reference. The daemon validates the selected TLS material before
activating the revision. A listener permitting `0.0.0.0/0` or `::/0` also
requires `unrestricted_acknowledged: true`; this acknowledgment is not client
authentication.

## Select the tunnel mode

The critical question is whether the tunnel passes the Gate TLS session through
or terminates it.

| Service | End-to-end Gate mTLS path | Layer 7 alternative |
| --- | --- | --- |
| Cloudflare Tunnel | Published TCP service plus client-side `cloudflared access tcp`; the inner Gate TLS session passes through the WebSocket tunnel. | Cloudflare Access can authenticate HTTP clients and `cloudflared` can validate its JWT locally. Use a sanitizing proxy before Door or agentless Gate. |
| ngrok | TCP endpoint, or TLS endpoint without `terminate-tls`. | HTTP Traffic Policy can validate JWT, OAuth/OIDC, mTLS, and IP policy at ngrok. Remove ingress headers before forwarding. |
| Tailscale Funnel | `tailscale funnel --tcp=PORT` raw TCP forwarder. | Funnel HTTPS terminates TLS locally but does not authenticate Internet visitors. Add a local authentication proxy. |

Raw TCP connectors usually cause Gate to observe the local connector address,
not the original Internet client. Configure Gate `allowed_cidrs` for the source
it actually sees and enforce original-client IP policy at the tunnel edge when
available. Do not enable PROXY protocol directly into gjl; Door and Gate do not
parse it.

The public [remote-exposure skill](../skills/remote-exposure/SKILL.md) contains
service-specific setup guidance, current official references, and a full
verification checklist.

## Verify before use

1. Run `gjl config get`, `gjl listener list`, `gjl tls-material status`, and
   `gjl doctor`. Confirm the active Route, listener, TLS references, observed
   connector source, and health.
2. From an intended paired Door, make a harmless request through its local
   Door listener. Confirm Gate reaches the provider and both Routes apply their
   own ordered rules.
3. From an unpaired client, verify the Gate TLS handshake fails. Test revoked
   and expired tunnel credentials and paired certificates as separate cases.
4. For a Layer 7 authentication proxy, confirm missing or invalid credentials
   fail before gjl. At the provider boundary, confirm tunnel credentials and
   identity assertion headers have been removed.
5. Test a streaming request through the full path. Responses must arrive
   incrementally and the provider response body must remain unmodified.
6. Disable tunnel request-body inspection, replay, packet capture, and verbose
   wire logging. Provider bodies and credentials must not enter operational
   logs.

Gate and Door both enforce their own Route rules on a Door-to-Gate path.
Requests and provider credentials never need a gjl-operated cloud service, but
a third-party Layer 7 tunnel may become an additional plaintext data boundary.
