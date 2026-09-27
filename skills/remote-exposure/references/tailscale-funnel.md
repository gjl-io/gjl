# Tailscale Funnel

Funnel is public Internet ingress. Its tailnet policy controls which nodes may create a Funnel; it does not restrict who may visit the public Funnel URL. Funnel traffic has no Tailscale identity headers, and tailnet access rules do not authenticate Internet visitors.

## Paired Door → Gate: raw TCP passthrough

Tailscale Funnel's raw TCP forwarder is suitable for a paired-Door Gate because it forwards packets without terminating the inner Gate TLS session:

```sh
tailscale funnel --bg --tcp=443 tcp://127.0.0.1:GATE_PORT
```

Use the actual Funnel DNS name and selected public port in the Door-to-Gate Route. Set `gate_server_name` to the Funnel DNS name covered by the Gate certificate. The Door verifies that name and trust chain; Gate verifies the paired Door certificate.

Funnel permits public ports `443`, `8443`, and `10000`. Confirm current availability, beta status, platform support, and non-configurable bandwidth limits in the installed version and official documentation.

Anyone can reach the public TCP socket, but an unpaired client must fail Gate's mTLS handshake. Gate generally observes the local Tailscale forwarder address. Permit only that address in Gate `allowed_cidrs`; do not enable Funnel's PROXY protocol directly into gjl.

Tailscale documents that Funnel relay servers cannot decrypt the relayed connection. In raw TCP mode, the TLS endpoint for this design remains Gate.

## HTTP ingress: exceptional Door

The normal Funnel HTTPS reverse proxy terminates TLS in the local Tailscale daemon and forwards HTTP to a loopback service. It supplies encryption but no visitor authentication or identity header.

Do not point this mode straight at a Door listener. Point it at a loopback authentication and sanitizing proxy that verifies a short-lived JWT or another suitable client credential, removes that credential and all identity headers, and then forwards to Door. Keep the proxy body-free in its logs.

If all clients can join a private tailnet, consider Tailscale Serve instead of Funnel; Serve applies tailnet access controls and can provide identity headers. Gate remains the product-designed boundary when people share a provider account, credential, or organization Route policy.

## Official references

- [Tailscale Funnel](https://tailscale.com/docs/features/tailscale-funnel)
- [`tailscale funnel` command](https://tailscale.com/docs/reference/tailscale-cli/funnel)
- [Tailscale Serve and identity headers](https://tailscale.com/docs/features/tailscale-serve)
- [Funnel versus device sharing](https://tailscale.com/docs/reference/funnel-vs-sharing)
