---
name: gjl-operations
description: Operate an installed gjl relay through its local CLI or guide the user through Desktop for setup, Routes, listeners, credentials, Activity, Usage, and daemon health.
---

# Operate gjl

gjl is a local relay between an LLM client and provider. One daemon owns Door (local relay), Gate (shared TLS gateway), and Vault (credential broker); CLI and Desktop manage that daemon through local IPC. Use this skill for general gjl tasks. For body rules, read [Route rules](../route-replacements/SKILL.md); for a remote Gate, read [Gate access](../remote-exposure/SKILL.md).

## Discover, act, verify

1. If a shell is available, run `gjl help` first. It lists the installed command surface. Then use `gjl status`, `gjl doctor`, and the relevant read commands below. For option details, use `gjl <leaf command> --help` where supported. If the executable is missing, use the [install guide](../../docs/install.md); if the daemon is stopped, use the user's existing service or `gjl run`. Do not infer live state from documentation.
2. Identify the user's intended client path and provider surface. A local client normally points to a loopback Door listener; a shared client uses a TLS Gate listener or a paired Door → Gate path. A Route belongs to one role, selects a provider/auth surface and credential source, and owns its rules. A listener selects a Route. Use `gjl config get` and `gjl route list` / `gjl listener list` before changing these objects.
3. Choose the smallest authorized change. For configuration writes, use the current `revision` with `--expected-revision`; reread after a conflict rather than overwriting. `gjl route put --expected-revision N route.json` and `gjl listener put --expected-revision N listener.json` take one entity each; `gjl config apply --expected-revision N config.json` takes the full v1 document. Do not place credential values in those JSON files or command arguments. The CLI and Desktop both commit through the daemon.
4. Verify the resulting state with `gjl status`, `gjl doctor`, the relevant list/query command, and a harmless client request when behavior depends on real traffic. If shell access is unavailable, guide the user through the matching Desktop view in [Desktop map](references/desktop.md) and ask for only the result needed to proceed.

## Pick the relevant management surface

| Task | Start with CLI | Desktop |
| --- | --- | --- |
| Daemon and role health | `gjl status`, `gjl doctor`, `gjl instance list` | Dashboard, Door/Gate/Vault, Settings → Daemon |
| Routes and listeners | `gjl config get`, `gjl route list`, `gjl listener list` | Routing |
| Credentials and auth | `gjl credentials list`, `gjl credentials discover` | Credentials; Vault for pairings and grants |
| Traffic and masking events | `gjl audit query`, `gjl audit bodies` | Activity |
| Tokens, costs, prices | `gjl usage summary`, `gjl usage query`, `gjl pricing list` | Usage |
| Remote device inventory | `gjl connection list`, `gjl gate certificate status` | Connections; Gate → observed clients/certificates |
| Service, TLS, updates | `gjl service status`, `gjl tls-material status`, `gjl update --dry-run` | Settings |

Read [CLI task map](references/cli.md) for command families and [Desktop map](references/desktop.md) when explaining where the user can act. The installed `gjl help` and current daemon output take precedence over these maps.

## Boundaries to preserve

- Request processing is decoded body → all `block` rules against the original → ordered `replace` rules → credential boundary → provider. Provider response bodies are forwarded unchanged; any response rule affects only a local recording copy.
- `traffic_log_enabled` records traffic, `masking_audit_enabled` records actual rule matches, and `usage_tracking_enabled` records token metadata and estimated cost independently. Stored local bodies do not expire automatically. Exports and saved body files have separate retention. Remote audit delivery has metadata only.
- Inbound authentication is a Route choice (`force_shared`, `mismatch_passthrough`, or `mismatch_reject`) based on the provider wire mechanism. `force_shared` discards inbound auth and injects the Route credential; it is prohibited when Door uses Vault credentials. Vault exchanges credential RPCs, never provider request bodies.
- Never print credentials or captured bodies into general logs or a chat response. Use the daemon's protected credential input mechanisms. Deletion, credential replacement, pairing revocation, network exposure, and update installation have real effects; scope and verify them against the user's request.
