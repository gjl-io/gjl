# Remote exposure verification

## Architecture

- [ ] The operator recorded why this deployment uses Gate or deliberately exposes Door. Internet, multi-user, and shared-account use defaults to Gate.
- [ ] Door data listeners remain loopback-only. Local management IPC is not published, proxied, or replaced with TCP.
- [ ] The complete client → tunnel → Door/Gate → provider path identifies every TLS termination point and every party able to read provider bodies.

## Authentication and transport

- [ ] A paired Door path uses raw TCP passthrough. Gate receives and verifies the actual Door certificate with `gate_paired_door_mtls`; the Door verifies the configured Gate server name and trust chain.
- [ ] A TLS-terminating proxy is not described as preserving gjl mTLS. Any Gate behind it is intentionally agentless and has independent ingress authentication.
- [ ] Door publication authenticates every request before Door. Browser-only redirects are not assumed to work for a headless LLM client.
- [ ] Tunnel authentication uses a dedicated field or header that does not replace provider `Authorization`; the proxy removes ingress credentials and tunnel identity assertions before gjl.
- [ ] Revocation, rotation, expiry, and least-privilege scope exist for tunnel credentials, JWT signing keys, service tokens, and paired Door certificates.

## Network and privacy

- [ ] Gate has explicit `allowed_cidrs` for the source address it actually observes. Original-client restrictions are enforced at the tunnel edge when a connector hides that address.
- [ ] PROXY protocol is disabled on a connection forwarded directly to gjl.
- [ ] Request-body inspection, replay, packet capture, and verbose wire logging are disabled throughout the tunnel path. Operational logs contain metadata only.
- [ ] The tunnel connector and any local authentication proxy listen on the narrowest practical local address and run with protected configuration and credentials.

## Tests

- [ ] An authorized harmless request reaches the intended Route and provider; streaming responses remain incremental and unmodified.
- [ ] Missing, invalid, expired, and revoked ingress credentials fail before gjl where applicable.
- [ ] An unpaired Door fails the Gate TLS handshake, and a revoked Door certificate stops working.
- [ ] Requests outside the tunnel edge IP policy fail even when Gate sees only the connector address.
- [ ] A request containing the tunnel credential is observed at the provider boundary without that credential or any tunnel identity assertion.
- [ ] Connector restart, host restart, tunnel revocation, and fail-closed behavior have been checked.
