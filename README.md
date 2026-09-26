# gjl

**A self-hosted policy boundary for LLM traffic.**

Inspect outbound requests, block content or rewrite decoded request bodies with
ordered regular-expression rules, and control provider credentials at a
boundary you operate.

[English](README.md) · [한국어](README.ko.md) · [简体中文](README.zh-Hans.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.fr.md)

[Website](https://gjl.io/) · [Releases](https://github.com/gjl-io/gjl/releases) ·
[Install and verify](docs/install.md) · [Security reports](SECURITY.md) ·
[Remote access](docs/remote-exposure.md) ·
[Connection observer](docs/connection-observer.md) ·
[Licenses](LICENSE.md)

## Quick Install & Get Started

Install gjl with a single command. The installer automatically detects your operating system, CPU architecture, and display environment, configures your `PATH`, and sets up the matching components.

### Windows (PowerShell)

```powershell
irm https://gjl.io/install.ps1 | iex
```

*Or via `curl.exe`:*
```powershell
curl.exe -fsSL https://gjl.io/install.ps1 | powershell -Command -
```

### macOS & Linux (curl)

```bash
curl -fsSL https://gjl.io/install.sh | sh
```

### CLI-only installation (exclude Desktop GUI)

If you prefer to install only the standalone `gjl` CLI on a system with a graphical desktop:

* **Windows:**
  ```powershell
  $env:GJL_CLI_ONLY=1; irm https://gjl.io/install.ps1 | iex
  # or: & ([scriptblock]::Create((irm https://gjl.io/install.ps1))) -CliOnly
  ```
* **macOS & Linux:**
  ```bash
  curl -fsSL https://gjl.io/install.sh | sh -s -- --cli-only
  # or: curl -fsSL https://gjl.io/install.sh | GJL_CLI_ONLY=1 sh
  ```

> [!TIP]
> **Headless & Server Environments**: On systems without a display server (such as Linux servers, headless SSH sessions, or Windows Server Core), the installer automatically skips downloading Flutter Desktop and installs only the standalone `gjl` CLI.

### Run

Immediately after installation in your current terminal:

- **Desktop GUI:**
  ```bash
  gjl gui
  ```
- **Terminal / Headless:**
  ```bash
  gjl run
  ```

### Updating gjl

Keep your installation up to date with `gjl update`:

```bash
gjl update             # Update all locally installed components (CLI and/or Desktop)
gjl update --cli-only  # Update only the gjl CLI
gjl update --gui-only  # Update only the Desktop GUI
gjl update --dry-run   # Check for updates without downloading
```

For manual binary downloads and checksum verification, see [Install and verify gjl](docs/install.md).

## Who gjl is for

- **People and teams focused on security** who want to block or mask sensitive
  content before it reaches a provider, keep provider credentials at a boundary
  they control, and optionally capture LLM requests and sanitized response
  copies in local logs.
- **People seeking better LLM results** who use Route rules to adjust prompt
  text or select another model supported by the provider in inspectable
  requests, based on what works for a specific workflow.
- **Individuals or organizations with several accounts for one LLM provider**
  who want a separate Route for each credential and explicit control over which
  account a client uses. gjl does not automatically balance or fail over
  between accounts.
- **Developers and teams using multiple coding agent tools** who want to track
  token consumption, calculate estimated costs, and compare usage patterns
  across different agents or workflows.
- **Team leads and organizations** who want to aggregate token consumption and
  estimated costs per individual member, client identity, or credential
  across shared infrastructure.

## What gjl does

gjl runs between an LLM client—such as a coding agent, IDE extension, or
developer tool—and an LLM provider. Each Route belongs to either Door or Gate
and owns its provider target, credential source, inbound authentication policy,
and masking rules.

The protected request path is:

```text
decoded body
  → block-rule precheck
  → ordered replacements
  → credential boundary
  → provider
```

- **Block or replace matching content in inspected requests.** Route rules run
  before provider authentication is injected. They cover supported decoded
  HTTP bodies, uncompressed Connect JSON payloads, and WebSocket text messages.
  They do not inspect gRPC or Connect Protobuf payloads, compressed Connect
  frames, WebSocket binary messages, headers, or URL paths and queries. A rule
  protects only content it actually matches on a supported path.
- **Adapt request content deliberately.** A Route can also rewrite a prompt
  phrase or a model field when its decoded body has a reliably identifiable
  shape. These are the same body rules used for sensitive data.
- **Keep provider credentials out of clients through Routes.** Bind one
  credential source to each Route and replace authentication only at the egress
  boundary, keeping upstream keys out of client configurations.
- **Broker credentials to paired relays with Vault.** Vault serves
  static API keys and manages OAuth refresh lifecycles over Door-Vault mTLS
  RPC without proxying LLM traffic. For OAuth, relays borrow only short-lived
  access tokens on demand, while refresh material never leaves the vault.
- **Track token usage and estimated costs.** gjl records provider-reported
  prompt, completion, and cache tokens alongside offline USD cost valuations
  in an owner-protected ledger. Usage tracking is independent of traffic
  logging, stores no prompt bodies or secrets, and requires no external
  monitoring service.
- **Preserve provider response bodies.** Route masking never rewrites the
  response body delivered to the client; it sanitizes only a bounded local
  recording copy. The relay removes HTTP hop-by-hop headers as required when
  forwarding a response.
- **Forward audit metadata without traffic bodies.** Operators can configure a
  remote audit sink to collect event and token metadata, but it receives
  metadata only. Request and sanitized-response bodies stay strictly in the
  owner-protected local audit store until explicitly deleted.
- **Operate without a vendor cloud.** gjl has no hosted control plane,
  product account, login, license server, device registration, or telemetry.

## Door, Gate, and Vault

Door, Gate, and Vault are concurrent capabilities of one daemon (started with `gjl run`), not
separate editions.

| Role | Purpose | Typical boundary |
| --- | --- | --- |
| **Door** | Local relay and Route switchboard | A developer workstation or local server |
| **Gate** | Shared TLS gateway, organization policy boundary, and credential injection point | A user- or organization-operated network boundary |
| **Vault** | Credential broker that serves API keys and owns refresh material | A dedicated credential boundary |

Supported deployment paths include:

```text
LLM client --> Door --------------------> Provider
LLM client --> Door --> Gate -----------> Provider
LLM client ------------> Gate -----------> Provider
               Door <-> Vault
            credential RPC only
```

Vault never receives prompts, source code, normal provider requests, or raw
provider responses.

## Downloading gjl

Download the asset for your operating system and architecture from
[GitHub Releases](https://github.com/gjl-io/gjl/releases).
Alpha releases are marked **Pre-release**. Read the release notes and
[verify the download](docs/install.md) before installing. Desktop bundles
include the matching `gjl`.

The initial prerelease has no Windows/macOS platform-trusted publisher
signature or macOS notarization. Windows MSIX is therefore unavailable; macOS
may require a per-item **Open Anyway** decision. See the install guide for
the exact trust limits and checks.

| Platform | Desktop + `gjl` | Standalone `gjl` |
| --- | --- | --- |
| Windows x64 | `gjl-windows-amd64.zip` | `gjl-windows-amd64.exe` |
| Windows Arm64 | — | `gjl-windows-arm64.exe` |
| Linux x64 | `gjl-linux-amd64.deb` or `gjl-linux-amd64.zip` | `gjl-linux-amd64` |
| Linux Arm64 | `gjl-linux-arm64.deb` or `gjl-linux-arm64.zip` | `gjl-linux-arm64` |
| macOS Intel | `gjl-darwin-amd64.pkg` or `gjl-darwin-amd64.zip` | `gjl-darwin-amd64` |
| macOS Apple silicon | `gjl-darwin-arm64.pkg` or `gjl-darwin-arm64.zip` | `gjl-darwin-arm64` |

### Desktop languages

The Desktop app supports eight interface languages. It follows the system
locale and uses English when no supported locale matches. The product names
gjl, Door, Gate, and Vault remain in English in every locale.

### Alpha profile retention

Alpha releases do not promise state-file compatibility with later alphas. Use
a fresh profile when trying a newer alpha. gjl does not automatically
delete or convert an earlier profile. Explicitly export or back up any config,
credentials, TLS material, pairing records, audit, and usage data you need
before changing profiles. Retain the earlier release asset and state backup for
recovery.


## Getting started

Desktop bundles include the `gjl` CLI and daemon. The desktop app manages the
local daemon through owner-protected IPC. It accepts credentials during entry
and sends them to the daemon; the daemon owns persistent credential storage and
enforces policy.

At a high level, routing LLM traffic through gjl requires three elements:

1. **A Route**: Defines the upstream provider target, masking rules, and
   authentication policy for either Door or Gate. By default, client credentials
   pass through unchanged, and traffic logging / masking audit default to off.
2. **A matching Listener**: The client entry point—either Door (local loopback)
   for a workstation or Gate (TLS) for shared network access—bound to that Route.
   (Listeners only bind to Routes of the same role.)
3. **The LLM client's Base URL**: Pointing your coding agent, IDE extension, or
   developer tool at that listener's address.

### Desktop setup

In the Desktop application, you can configure these either through the setup
wizard or manually:

- **Quick setup (Wizard)**: Click **+ (Add)** in the top dashboard HUD. Choosing
  **Use on this device** bundles steps 1 and 2, automatically
  creating a local Door Route and loopback listener with credential passthrough in
  one step. Choosing **Share with Team** guides you to configure
  either a shared **Gate** endpoint or a **Vault** credential broker.
- **Manual setup**: Open the **Routing** view to create and inspect Routes and
  Listeners individually.

> [!TIP]
> **Managing provider credentials (optional):** By default, gjl passes inbound
> client credentials through to the provider without storing them. If you want
> gjl to manage, inject, or broker provider credentials at the boundary
> instead, register the credential in the separate **Credentials** catalog first
> before referencing it in your Route.

### Headless or CLI management

In a headless environment or from the command line, run the daemon and manage
entities individually using the bundled `gjl` binary:

```console
$ gjl run
```

In another terminal:

```console
$ gjl status
$ gjl doctor
$ gjl route --help
$ gjl listener --help
$ gjl --help
```

The CLI and Desktop use a Unix domain socket on macOS/Linux and a named pipe on
Windows. They do not write daemon-owned configuration, credentials, or audit
storage directly.

## Using Route replacements

`replace` is a request-body rule, not just a secret masker. A narrowly scoped
Route could change `an apple` to `the green apple` if that exact change has been
shown to improve a particular task. It could also change a client's requested
model from `gpt-5.6-sol` to `gpt-6-sol` when the provider accepts the newer model
but the client has not added it yet. A rewrite cannot make an unavailable model
available or change a model name carried only in a header or URL.

**Choose the match from the actual decoded body.** Before enabling a rule,
consider whether its pattern uniquely identifies the intended text. A bare
model name or everyday phrase may also occur in prompts, code, examples, or
other fields. Temporarily enable the Route's traffic log, inspect a local
request `body` in Desktop Activity or through `gjl audit query`,
`gjl audit bodies`, and `gjl audit body-save`, and use its field shape to
design the pattern. Header values are outside body replacement. Capture before
activating a rewrite when you need to see the client's original body: the audit
request body records what was sent to the provider after replacement. Traffic
logging is off by default, stores bodies locally until explicit deletion, and
should be enabled only with that retention in mind. A body saved to a separate
file needs separate deletion.

For example, one captured WebSocket `response.create` request body used compact
JSON with no spaces: `{"type":"response.create","model":"gpt-6-sol",...}`.
Its model field was surrounded by commas. For a client that sends the same
shape with the older model, this Route rule targets that field:

```json
{
  "id": "upgrade-model",
  "mode": "replace",
  "pattern": ",\"model\":\"gpt-5\\.6-sol\",",
  "replacement": ",\"model\":\"gpt-6-sol\","
}
```

The example is shape-specific: it will not match pretty-printed JSON or a
`model` field in another position. Inspect that client's request body and adjust
the rule if its actual shape differs. gjl uses Go RE2 regex syntax and
applies replace rules in Route order after checking all block rules against the
original decoded body. Rules never rewrite the provider response body sent to
the client; they sanitize only the local response recording copy.

For sensitive-text rules, it can help to tell the client-side AI that outbound
request content is rewritten at the network boundary. Describe the placeholder
and expected behavior without including the secret itself. The provider sees
the rewritten request, so an instruction inside that request cannot give it
access to the original text. For a Route configured to use `<GJL_MASKED>`, an
agent instruction can say:

> gjl replaces matching sensitive text with `<GJL_MASKED>` before the
> provider receives the request. Keep that placeholder intact; do not try to
> reconstruct its original value.

Check an actual request after changing a rule, then turn off temporary traffic
logging and explicitly delete unneeded audit events.

See the [Route replacement skill](skills/route-replacements/SKILL.md) for a
workflow that starts from captured body shape and checks rule specificity.

## Security model

- Routes strictly belong to either Door or Gate. A Door listener binds only to
  Door Routes, while a Gate listener binds only to Gate Routes; a single Route
  cannot be shared across roles.
- Masking rules belong to a Route. Every block rule checks the original decoded
  request before any replacement runs; replacements then run in list order.
- Provider authentication is handled independently from body masking and is
  selected by provider wire mechanism, not by the name of a coding agent.
- Provider requests and credentials never pass through infrastructure operated
  by the gjl authors.
- Door is local-first. For remote or shared access, use Gate with TLS and CIDR
  controls. Do not publish a Door endpoint without strict edge access control.
- Local traffic bodies do not expire automatically. Deletion is an explicit,
  filtered or fully confirmed management operation.
- Gate may keep best-effort Observed Client metadata (such as source IP,
  bounded User-Agent and companion claims, and authentication HMAC
  fingerprints) in a separate owner-protected local store. These observations
  are not verified human identities, and deleting audit events does not erase
  that separate store.
- An operator-configured remote audit sink can receive metadata, including
  observed-client/actor identifiers and provider-reported token usage, but
  never traffic bodies or raw Observed Client signals. Treat this metadata as
  potentially sensitive when configuring retention and remote access.
- Update checks are advisory. A release daemon reads only public tags from this
  GitHub repository; it never downloads or installs an update automatically.

Read [Remote access through Gate](docs/remote-exposure.md) before
making any listener reachable outside its host.

## Why the source is private

We believe AI has made a basic relay easier to recreate, reducing the benefit
of publishing its implementation. gjl handles sensitive LLM traffic and
credentials, and we judge that publishing its full source would make it easier
for attackers to look for weaknesses. We therefore keep the product source
private as part of our security approach.

You can inspect where your running gjl processes connect with our public
Python [connection observer](docs/connection-observer.md). It labels visible
Route upstreams, Gate/Vault connections, known OAuth servers, and GitHub;
unidentified destinations appear as `UNKNOWN` for you to review. It makes no
safety judgment and does not read request bodies or credentials.

Start gjl, then run this from the repository root:

```sh
python -m pip install -r tools/requirements.txt
python tools/observe_connections.py --duration 600
```

## Repository contents

This repository is the public distribution home for gjl. It contains:

- official release downloads and canonical version tags;
- public operational and security documentation;
- an optional [local connection observer](docs/connection-observer.md) that
  labels visible network peers without making a safety judgment;
- agent skills that help configure supported workflows safely; and
- [`llms.txt`](llms.txt), an AI task map for gjl's CLI, Desktop, and product
  guides.

Current agent skills cover general operation, Route body rules, and
private-network Gate access:

- [`skills/gjl-operations`](skills/gjl-operations/SKILL.md) — discovers the
  installed CLI, maps tasks to Desktop views, and guides local management.
- [`skills/route-replacements`](skills/route-replacements/SKILL.md) — designs
  body block and replace rules from observed request shapes, including
  sensitive text, prompt phrases, and model fields.
- [`skills/remote-exposure`](skills/remote-exposure/SKILL.md) — guides
  paired-Door Gate mTLS and checks the remote access boundary.

## Reports and licensing

Report security vulnerabilities privately through
[GitHub's vulnerability reporting form](https://github.com/gjl-io/gjl/security/advisories/new).
Use [GitHub Issues](https://github.com/gjl-io/gjl/issues/new) for non-security bugs.
Do not include secrets or private traffic in a public issue. See
[SECURITY.md](SECURITY.md).

Repository licensing terms and the product binary license are unified in
[LICENSE.md](LICENSE.md). The public installer scripts, Python tools, and agent
skills are [MIT-licensed](LICENSE-MIT). Official product binaries remain
proprietary under the [product binary license](PRODUCT-LICENSE.md). See
[NOTICE.md](NOTICE.md) and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## Project guarantees

gjl is designed around local and operator-owned authority:

- no vendor-operated backend or runtime service;
- no product account, login, paid-feature lock, or device registration;
- no telemetry;
- no provider request, credential, configuration, or audit data in update
  checks; and
- no automatic update installation or rollback.

The only vendor-side network interactions are unauthenticated reads of public
GitHub tags, downloading official release assets when the user explicitly runs
`gjl update`, and opening the public release page from the Desktop GUI when requested.
