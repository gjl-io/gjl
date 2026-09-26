# Install and verify gjl

Download the asset for your operating system and CPU from the
[GitHub release](https://github.com/gjl-io/gjl/releases). Desktop bundles
include a matching `gjl` CLI and daemon. Windows Arm64 has only the standalone
`gjl` binary. The first release is an **unsigned prerelease**: Windows and
macOS files have no platform-trusted publisher signature, and macOS files are
not notarized. A future signed release may add Windows MSIX.

| System | Desktop installer | Desktop archive | Standalone CLI/daemon |
| --- | --- | --- | --- |
| Windows x64 | — | `gjl-windows-amd64.zip` | `gjl-windows-amd64.exe` |
| Windows Arm64 | — | — | `gjl-windows-arm64.exe` |
| Linux x64 | `gjl-linux-amd64.deb` | `gjl-linux-amd64.zip` | `gjl-linux-amd64` |
| Linux Arm64 | `gjl-linux-arm64.deb` | `gjl-linux-arm64.zip` | `gjl-linux-arm64` |
| macOS Intel | `gjl-darwin-amd64.pkg` | `gjl-darwin-amd64.zip` | `gjl-darwin-amd64` |
| macOS Apple silicon | `gjl-darwin-arm64.pkg` | `gjl-darwin-arm64.zip` | `gjl-darwin-arm64` |

## Quick install

You can install gjl using our automated installer script:

- **Windows (PowerShell):**
  ```powershell
  irm https://gjl.io/install.ps1 | iex
  # CLI-only: $env:GJL_CLI_ONLY=1; irm https://gjl.io/install.ps1 | iex
  ```
- **macOS & Linux (curl):**
  ```bash
  curl -fsSL https://gjl.io/install.sh | sh
  # CLI-only: curl -fsSL https://gjl.io/install.sh | sh -s -- --cli-only
  ```

The installer detects whether a graphical desktop environment is available. If running in a headless or server environment without a display, it skips Flutter Desktop and installs only the standalone `gjl` binary. It also automatically adds gjl to your `PATH`.

Once installed, keep gjl updated using `gjl update` (or `gjl update --cli-only` / `gjl update --gui-only`).

## Check the download

Compare the downloaded file's **SHA-256** with the matching filename in that
release's checksum list. Do this before installing or running it. The initial
release publisher verifies all fifteen uploaded files against its reviewed,
Ed25519-signed internal manifest before publication. The published checksum
detects a different local download, but a checksum copied from the same release
page does not independently authenticate the publisher.

```powershell
# Windows PowerShell
(Get-FileHash .\gjl-windows-amd64.zip -Algorithm SHA256).Hash.ToLowerInvariant()
```

```sh
# Linux
sha256sum gjl-linux-amd64.deb

# macOS
shasum -a 256 gjl-darwin-arm64.pkg
```

Stop if a checksum differs. For this prerelease, a Windows publisher warning
or a macOS unidentified-developer warning is expected; decide whether to run
the file only after checking its source and checksum. Do not turn off
system-wide protection. Later signed releases will have separate signature
verification instructions.

## Install or run

- **Windows x64:** Unpack the verified `.zip` and run the Desktop app beside
  `gjl.exe` (or run `gjl gui`). The standalone `.exe` runs without Desktop.
  Windows Arm64 uses `gjl-windows-arm64.exe` alone.
- **Linux:** Install the verified `.deb` with
  `sudo apt install ./gjl-linux-amd64.deb` (substitute `arm64` if needed).
  It installs Desktop and `gjl` commands. Alternatively unpack the `.zip`
  and run Desktop and `gjl` from the extracted directory. For headless
  operation, make the standalone `gjl-linux-ARCH` executable and run it.
- **macOS:** Open the verified `.pkg` to install the Desktop app in Applications
  and `gjl` in `/usr/local/bin`. Alternatively unpack the `.zip` to obtain the
  app with its bundled CLI. The standalone `gjl-darwin-ARCH` is for CLI and
  headless use. Gatekeeper may block the unnotarized app or installer. After a
  failed open attempt, use **System Settings → Privacy & Security → Open
  Anyway** for that item if you trust it; macOS then asks for confirmation.
  This is a per-item decision, not a guarantee that every host policy will
  permit it. See [Apple's instructions](https://support.apple.com/en-us/102445).

Run `gjl version`, `gjl release-info`, and `gjl --help` with the installed or
extracted CLI. For standalone downloads, invoke the downloaded filename or
rename it to `gjl` (to `gjl.exe` on Windows). The daemon is a separate process
started with `gjl run`; Desktop and CLI manage it over owner-protected local
IPC. A display is not required for CLI/daemon operation.

## First local Door Route

The following example passes the client's OpenAI API credential through. It
does not store that credential in gjl. Start `gjl run` in one terminal.
In another terminal, confirm `gjl status` reports config revision 1, then save
the Route as `route.json`:

```json
{
  "id": "local-openai",
  "role": "door",
  "provider_surface": "openai_api",
  "target": "provider",
  "upstream": "https://api.openai.com",
  "credential": {"source": "passthrough"},
  "inbound_auth_policy": "mismatch_passthrough",
  "masking_rules": [],
  "traffic_log_enabled": false,
  "masking_audit_enabled": false,
  "usage_tracking_enabled": true
}
```

Apply it with `gjl route put --expected-revision 1 route.json`. Save this
listener as `listener.json`:

```json
{
  "id": "local-door",
  "role": "door",
  "network": "tcp",
  "address": "127.0.0.1:4000",
  "transport_mode": "door_loopback_plaintext",
  "route_id": "local-openai"
}
```

Apply it with `gjl listener put --expected-revision 2 listener.json`. Check
`gjl doctor` and point the client's OpenAI-compatible Base URL at
`http://127.0.0.1:4000/v1`; keep the credential in that client for this
passthrough example. If the revisions differ, inspect `gjl config get` and
use the current revision rather than replaying an uncertain mutation.

gjl appends the client request path to the Route upstream path. Keep the
upstream at the provider origin in this example: a client request to
`/v1/chat/completions` then reaches the provider at `/v1/chat/completions`.

For shared credentials, Gate, Vault, or more Routes, configure the relevant
credential and TLS boundaries deliberately. Gate remote access is covered in
the [remote access guide](remote-exposure.md).

## Alpha profiles and removal

An alpha does not promise state-file compatibility with another alpha. Use a
fresh profile for a newer alpha. Back up or export any configuration,
credentials, TLS material, pairings, audit, and usage records you need; old
state is not automatically deleted or converted. Keep the earlier release
asset if you need to reopen that profile. Uninstalling a package does not
mean its daemon-owned state, audit bodies, or saved exports have been erased.
Use CLI/Desktop deletion where available, stop the daemon, and remove unneeded
profile files and saved exports deliberately through your operating system.
