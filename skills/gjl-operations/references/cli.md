# CLI task map

Run `gjl help` to discover the installed command surface, then `gjl <leaf command> --help` for supported flags. In the table, `/` separates alternatives, not literal CLI syntax. Most management commands talk to the running daemon over local IPC; `gjl run` starts that daemon and `gjl gui` opens Desktop. Read current state before writing.

| Need | Commands to inspect | Mutation family |
| --- | --- | --- |
| Daemon, service, updates | `status`, `doctor`, `instance list`, `service status`, `update --dry-run` | `run`, `service install/start/stop/uninstall`, `update` |
| Config, Routes, listeners | `config get`, `route list`, `listener list` | `config apply`, `route put/delete`, `listener put/delete` (current `--expected-revision`) |
| Provider credentials | `credentials list`, `credentials discover`, `credentials recovery status` | `credentials login/register/replace/delete`; recovery commands for explicit repair |
| TLS and remote peers | `tls-material status/catalog`, `connection list/show`, `gate certificate status`, `door-gate certificate status` | `tls-material apply/reload/generate`; certificate enrollment and rotation commands |
| Vault borrowing | `vault pairings/grants`, `vault certificate status`, `door-vault certificate status`, `door-vault runtime status` | `vault approve/grant/revoke-grant/revoke-door`; invitation, certificate, runtime commands |
| Activity and audit | `audit query`, `audit correlate`, `audit bodies`, `audit body-read`, `audit remote-health` | `audit export`, `audit body-save`, `audit delete/compact` |
| Token use and price | `usage summary/series/query/detail`, `pricing list` | `usage export/delete/compact`, `usage recalculate prepare/apply/status`, `pricing set/reset` |
| Fixed-host routing | `fixed-host status` | `fixed-host activate/deactivate` |

`route put` and `listener put` accept a JSON file for one object. `config apply` accepts the complete v1 document, whose top-level fields are `schema_version`, `revision`, `listeners`, and `routes`. Use `gjl config get` for the current revision; follow the actual command help for argument order and required flags. For a first local Route and listener, see the [install guide](../../../docs/install.md). For credential input, use the installed CLI help or Desktop's **Credentials** view.

Audit body inspection can expose prompts and source code. Query event metadata first, read a body only when needed, and avoid pasting it into chat. `audit delete` and `usage delete` affect separate stores. Their exports and `audit body-save` output are separate files.
