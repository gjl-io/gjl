# Cloudflare Tunnel

Use Cloudflare Tunnel in one of two distinct modes. Do not mix their security claims.

## Paired Door → Gate: TCP through Access

This is the preferred Cloudflare design for an Internet-reachable Gate.

1. Publish the Gate listener as a TCP service, such as `tcp://127.0.0.1:GATE_PORT`, and protect its hostname with a Cloudflare Access policy.
2. On the Door host, run a client-side TCP bridge:

   ```sh
   cloudflared access tcp --hostname gate.example.com --url 127.0.0.1:LOCAL_PORT
   ```

3. Point the Door-to-Gate Route at `https://127.0.0.1:LOCAL_PORT`, while keeping `gate_server_name` equal to the DNS name covered by the Gate certificate. The Door's configured client identity and Gate trust references remain in force.
4. Confirm with a handshake test that the TLS session begins at Door and terminates at Gate. Cloudflare carries TCP over a WebSocket connection; it does not replace the inner gjl mTLS session in this mode.

Cloudflare requires `cloudflared` on both ends for this published TCP pattern and uses a browser Access login for the documented interactive flow. Verify the current headless or service-auth mechanism before assuming it works for unattended clients. Cloudflare recommends its private-network client path rather than published TCP for long-lived connections; test LLM streaming and reconnect behavior.

Gate sees the origin-side `cloudflared` connector address, not the Internet client's address. Restrict the original client at Access and configure Gate `allowed_cidrs` for the connector address it actually observes.

## HTTP/HTTPS ingress: agentless Gate or exceptional Door

Cloudflare terminates public HTTPS in this mode and can read the HTTP request. Use it only after the user accepts that data boundary.

- Protect the hostname with an Access application. Interactive users can use identity policies; headless clients can use a narrowly scoped Service Auth policy and service token if their client can send the required headers.
- Enable cloudflared's origin-side Access JWT validation for the published application (`originRequest.access.required`, `teamName`, and the application `audTag`). This makes `cloudflared` verify the Access assertion before proxying.
- Route the tunnel to a loopback authentication and header-sanitizing proxy. That proxy removes `Cf-Access-Jwt-Assertion`, `CF_Authorization`, `CF-Access-Client-Id`, `CF-Access-Client-Secret`, and any other ingress credential before forwarding to Door or an agentless Gate.
- Do not use Access OAuth in the provider `Authorization` header unless a trusted proxy translates and removes it before gjl. Provider authentication and tunnel authentication are separate boundaries.
- Keep origin TLS verification enabled when the local hop uses HTTPS. Configure `originServerName` and `caPool` for a private CA; do not solve certificate errors with `noTLSVerify`.

An illustrative locally managed L7 ingress rule is:

```yaml
ingress:
  - hostname: door.example.com
    service: http://127.0.0.1:AUTH_PROXY_PORT
    originRequest:
      access:
        required: true
        teamName: TEAM_NAME
        audTag:
          - ACCESS_APPLICATION_AUD
  - service: http_status:404
```

The target is an authentication and sanitizing proxy, not management IPC. Keep real tokens and account values outside the file.

## Official references

- [Protocols for published applications](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/protocols/)
- [Arbitrary TCP with client-side cloudflared](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/non-http/cloudflared-authentication/arbitrary-tcp/)
- [Cloudflare Tunnel origin parameters](https://developers.cloudflare.com/tunnel/reference/origin-parameters/)
- [Cloudflare Access service tokens](https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/)
- [Validate Access JWTs](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/)
