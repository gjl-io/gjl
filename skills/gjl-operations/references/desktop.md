# Desktop map

Run `gjl gui` to open Desktop when installed. Its dashboard is a pipeline canvas with entry points into full-screen views; there is no conventional sidebar. It manages the same local daemon as the CLI. If the daemon is unavailable, the dashboard offers startup or service guidance.

| Open from dashboard canvas | What the user can do or inspect |
| --- | --- |
| **Door** | Local relay status and Door-related management. |
| **Gate** | Gate certificate invitations/enrollments and observed clients. Gate Routes/listeners are edited in **Routing**. |
| **Vault** | Credential broker status, Door pairing/certificates, grants, and recovery controls. |
| **Routing** | Add/edit/delete Routes and listeners; edit a Route's provider surface, credential source, auth policy, ordered masking rules, traffic logging, masking audit, and usage tracking; import/export the configuration. |
| **Credentials** | Inspect and register credentials, initiate supported OAuth login, and manage existing entries. Credential values are entered through protected UI flows. |
| **Activity** | Filter traffic, masking, credential, and operational events; correlate a trace; inspect or save locally stored bodies; export, delete, and compact audit records. |
| **Usage** | Filter requests, tokens, and estimated cost by time or identity; inspect trends and detail; manage token prices, recalculate valuations, export, delete, and compact ledger records. |
| **Connections** | Inspect configured remote Gate/Vault connection inventory. |
| **Settings** | Daemon lifecycle and service; appearance; screen capture; updates; organization audit delivery; fixed-host interception; TLS material catalog/reload. |

The dashboard also offers a setup flow for local Door or shared Gate/Vault paths. Use current on-screen labels if localization differs; `gjl`, Door, Gate, and Vault remain English. A Desktop screenshot is a local screen capture and may contain sensitive data.
