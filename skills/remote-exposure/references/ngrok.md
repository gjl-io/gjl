# ngrok

Choose whether ngrok passes the Gate TLS session through or terminates it. This choice determines which component authenticates the client and who can read request bodies.

## Paired Door → Gate: TCP or unterminated TLS

Use a TCP endpoint, or a TLS endpoint without a `terminate-tls` action, to retain gjl's end-to-end mTLS. A simple TCP endpoint starts with:

```sh
ngrok tcp 127.0.0.1:GATE_PORT
```

Use a stable TCP address or stable TLS domain for a persistent deployment so the Door Route and Gate certificate name do not change. Configure the Door Route's HTTPS upstream to the assigned host and port, and set `gate_server_name` to the DNS name in the Gate certificate.

For this mode:

- Do not attach `terminate-tls`, OAuth, OIDC, or HTTP JWT actions to the passthrough connection. Terminating mTLS at ngrok authenticates the client to ngrok and prevents Gate from receiving the Door certificate.
- An `on_tcp_connect` IP restriction can reject unwanted source networks before the connector. Gate still sees the local ngrok agent as its source, so set Gate `allowed_cidrs` for that observed connector address.
- Do not enable upstream PROXY protocol when ngrok forwards directly to gjl. gjl does not parse its preamble.
- ngrok's Traffic Inspector does not support TCP endpoints. Keep any other packet or event capture body-free.

## HTTP ingress: agentless Gate or exceptional Door

HTTP/HTTPS endpoints terminate TLS in ngrok. Traffic Policy can authenticate requests with OAuth, OIDC, mutual TLS, IP restrictions, or JWT validation, but this is an ngrok boundary rather than gjl paired-Door mTLS.

For non-browser LLM clients, prefer JWT validation in a dedicated header such as `X-GJL-Tunnel-Authorization` when the client can supply it. Configure an exact issuer, audience, allowed signing algorithms, and JWKS source. Run `jwt-validation` before forwarding and then use `remove-headers` to delete the ingress credential. Do not consume the provider `Authorization` header for tunnel authentication.

Forward authenticated traffic through a loopback sanitizing proxy to Door, or to a deliberately agentless Gate. If the deployment must keep bodies opaque to the ngrok cloud, use an unterminated TCP/TLS endpoint and perform authentication at a local TLS proxy; edge HTTP actions require ngrok to process plaintext HTTP.

Leave Traffic Inspector disabled for LLM traffic. When enabled, it can capture, display, edit, and replay HTTP request and response bodies.

## Official references

- [TCP Agent Endpoints](https://ngrok.com/docs/gateway/endpoints/tcp/)
- [TLS termination and end-to-end encryption](https://ngrok.com/docs/gateway/domains/tls-termination/)
- [JWT Validation action](https://ngrok.com/docs/gateway/traffic-policy/actions/jwt-validation/)
- [Restrict IPs action](https://ngrok.com/docs/gateway/traffic-policy/actions/restrict-ips/)
- [Add and remove headers](https://ngrok.com/docs/gateway/traffic-policy/examples/add-and-remove-headers/)
- [Traffic Inspector](https://ngrok.com/docs/share-localhost/inspection/)
