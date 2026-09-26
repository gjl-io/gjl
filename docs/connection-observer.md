# Observe network destinations

`tools/observe_connections.py` prints the network peers visible for running
`gjl` and Desktop processes and their visible children. It makes no
safety decision. A destination that it cannot identify is marked `UNKNOWN`.
The tool does not read request bodies, credentials, or audit data, and it does
not upload observations.

## Run

Install Python 3.10 or newer and the single dependency:

```sh
python -m pip install -r tools/requirements.txt
python tools/observe_connections.py --duration 600
```

Start gjl first, then run the observer while doing normal work. Use
`Ctrl+C` to finish early. On Windows, `py -3` may be used in place of `python`.
The same script works on Windows, macOS, and Linux. It looks for the running
daemon's binary, a `gjl` beside Desktop, and then `PATH`. If none is found,
pass `--gjl /path/to/gjl` (or the Windows `.exe` path). For a daemon using a
nondefault management endpoint, also pass `--ipc ADDRESS`. Use `--pid PID` for
an executable with a different name. The observer follows visible child
processes, including an external credential refresh helper while it remains a
child. It never launches an LLM client or changes daemon configuration.

Examples:

```sh
python tools/observe_connections.py --gjl /opt/gjl/bin/gjl --duration 300
python tools/observe_connections.py --pid 12345 --label 'Audit sink=audit.example.org:443'
```

The `--label` option only adds a display label. It does not hide or permit
anything. It accepts `NAME=HOST:PORT` or `NAME=URL`; do not put credentials in
the argument. Use `--no-config` if the local `gjl` CLI is unavailable or you
prefer not to query it.

## Where labels come from

- `gjl config get` supplies the active Route upstreams and listener IDs. The
  observer labels an upstream with its Route and the listener IDs that refer to
  that Route, including Gate route matchers. It also labels incoming connections
  to visible or configured data listener ports.
- `gjl connection list` supplies the secret-free endpoints of Gate and Vault
  connections known to Door.
- Public, built-in GitHub update and provider OAuth hostnames are included in
  the script. These are descriptive labels even when the corresponding feature
  is not in use.
- The optional remote audit sink endpoint is provisioned outside the main
  config and is absent from these read-only CLI views. It remains `UNKNOWN`
  unless the user adds a label. A custom proxy or external helper destination
  may likewise need a manual label.

The script calls only the bundled `gjl` read commands over local IPC; it does
not open daemon state files. The label set is a snapshot from the start of
observation. Restart the observer after editing Routes or connections.

## Reading the output

Each row shows time, direction, process/PID, local and remote IP:port, and a
label. `INBOUND` is an accepted client connection to a Door or Gate listener;
`LABELED` means the remote address matches a configured or known destination;
`UNKNOWN` means no label matched. Unknown rows are repeated at the end so they
are easy to review. Labels matched through DNS say `DNS/IP match; hostname not
observed`: a socket gives an IP address, not the requested HTTPS hostname. A
shared IP can therefore produce more than one candidate label. The observer
does not reverse-resolve an IP and treat the result as proof of identity.

The script polls process sockets every 0.2 seconds by default. Very short
connections, unconnected UDP sends, processes that exit before a scan, or
connections hidden by OS permissions can be missed. A warning lists process
IDs whose sockets could not be read. Unix sockets and Windows named pipes used
for local management are outside this internet-socket view. DNS resolution of
known hosts is performed by the observer itself to attach labels; this may
contact the configured system DNS resolver. No capture or verdict is claimed
beyond what the displayed rows show.

## Reproduce the live integration test

From the public repository root, set `GJL_TEST_BINARY` to an installed or
downloaded `gjl` binary and run
`python -m unittest discover -s tools -p test_gjl_live.py -v`. The test starts
an isolated daemon, adds a Door Route pointing at a local mock provider, and
checks that the observer prints that Route label for the daemon's real
outbound socket. It does not contact a real LLM provider. Internal maintainers
with access to the private source checkout can set `GJL_TEST_SOURCE`
instead; that variant builds a temporary `gjl` binary first.
