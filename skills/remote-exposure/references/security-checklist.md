# Gate exposure verification

- [ ] Gate uses TLS, a Gate-owned Route, an explicit listener address, and narrow `allowed_cidrs`; Door data listeners remain on loopback and management IPC remains local.
- [ ] For paired Doors, `gate_paired_door_mtls` verifies a trusted Door certificate. The Door verifies the Gate server name and trust chain. TLS references resolve through protected catalog entries.
- [ ] An unpaired client fails the TLS handshake. A client outside `allowed_cidrs` is rejected at the actual Gate boundary, even if a proxy or NAT is present.
- [ ] A harmless request reaches the intended Route and provider; Door and Gate rules produce the intended result; streamed provider responses arrive incrementally and unmodified.
- [ ] For agentless Gate, independent network access control is established. `force_shared` or a supplied API-key header is not counted as Gate client authentication.
- [ ] Any third-party ingress has a separate review of request transit, TLS termination, client identity, and the source IP observed by Gate.
