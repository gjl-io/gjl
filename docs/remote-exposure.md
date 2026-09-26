# Remote access through Gate

Gate is the network-facing relay. Door binds to loopback and is for
local clients. Vault carries credential RPC, not provider traffic. Keep local
management IPC private; it is never an HTTP endpoint for remote clients.

## Choose the access boundary

- For a remote Door, use a user- or organization-operated private network and
  `gate_paired_door_mtls`. Gate verifies the paired Door certificate, checks the
  source address against `allowed_cidrs`, and applies its own Gate Route.
- `gate_agentless_tls` authenticates the **server**, not the client. It does not
  create a separate inbound bearer-token check. Use it only on a network whose
  client access is independently controlled, with narrow `allowed_cidrs`.
  A Route using `force_shared` ignores the inbound credential; an arbitrary
  bearer value cannot secure such a Route.
- Do not publish a Door listener through a public tunnel. A tunnel to an
  agentless Gate can also expose a shared credential Route to anyone who can
  reach the tunnel. An unrestricted CIDR confirmation is an acknowledgment of
  exposure, not authentication.

Third-party tunnels and reverse proxies can relay provider request content
through infrastructure outside your boundary. They can also change the source
IP seen by Gate, so `allowed_cidrs` may check the proxy rather than the actual
client. This guide does not prescribe such an ingress path. Deploy one only
after separately reviewing the provider-data boundary, client authentication,
TLS behavior, and observed source address.

## Prepare a paired-Door Gate listener

1. Establish a private route between the Door and Gate hosts. Restrict ingress
   to the expected Door source addresses at the network edge.
2. Provision Gate server identity and paired-Door client trust through the
   protected TLS material catalog. The catalog holds file paths; the ordinary
   Route/Listener configuration holds only stable references. See `gjl
   tls-material status` and `gjl tls-material catalog` on the Gate host.
3. Create a Gate Route (`role: "gate"`) and its selected provider credential.
   A Gate listener can bind only to a Gate Route.
4. Add a listener with `gjl listener put --expected-revision REV listener.json`.
   Replace the example addresses, references, and Route ID with provisioned
   values. This is a **listener object**, not a complete configuration file:

```json
{
  "id": "team-gate",
  "role": "gate",
  "network": "tcp",
  "address": "10.20.0.10:8443",
  "transport_mode": "gate_paired_door_mtls",
  "server_identity_ref": "gate-server",
  "client_trust_ref": "paired-door-roots",
  "route_id": "team-provider",
  "allowed_cidrs": ["10.20.0.0/24"]
}
```

The Gate server certificate must cover the DNS name the Door uses. Configure
the Door-to-Gate Route with that DNS name, the HTTPS Gate upstream, a paired
client identity reference, and a server trust reference. The daemon validates
the selected TLS material before activating the revision. Gate does not accept
cleartext. A listener using `0.0.0.0/0` or `::/0` additionally requires
`unrestricted_acknowledged: true`; avoid unrestricted access for this setup.

## Verify before use

1. Run `gjl config get`, `gjl listener list`, `gjl tls-material status`, and
   `gjl doctor` on the Gate host. Confirm the active Route, listener, TLS
   references, and health. These are local IPC commands.
2. From the intended paired Door, make a request through its Door listener and
   confirm that the Gate reaches the provider. Check the Gate Route's behavior
   with a harmless test request before using sensitive data.
3. From an unpaired client on an allowed source address, verify the Gate
   rejects the TLS handshake. From outside `allowed_cidrs`, send a request
   with a valid paired identity and verify Gate returns HTTP `403`. Do not
   infer success from a proxy's `403` alone; test the actual Gate boundary.
4. Test a streaming request through the intended Door-to-Gate path. Check that
   responses arrive incrementally and that Route masking does not rewrite the
   provider response body. HTTP hop-by-hop headers may change during relay.

Gate and Door both enforce their own Route rules on a Door-to-Gate path.
Requests and provider credentials never need a gjl-operated cloud service.
