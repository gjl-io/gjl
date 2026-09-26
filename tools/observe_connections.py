#!/usr/bin/env python3
"""Show network peers of gjl processes, with descriptive labels only."""

from __future__ import annotations

import argparse
import ctypes
import ipaddress
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from urllib.parse import urlsplit

try:
    import psutil
except ImportError:
    print("Install psutil first: python -m pip install psutil", file=sys.stderr)
    raise SystemExit(2)


# Public, built-in destinations in updatecheck, credentials/oauthflow,
# credentials/nativeoauth, and credentials/externalagent. These describe hosts,
# not the URL path or the reason for any particular connection.
BUILT_IN_HOSTS = {
    "api.github.com": "GitHub update check",
    "github.com": "GitHub page (opened by user)",
    "auth.openai.com": "OpenAI OAuth",
    "platform.claude.com": "Claude OAuth refresh",
    "claude.ai": "Claude OAuth login",
    "api.anthropic.com": "Anthropic OAuth / external refresh",
    "accounts.google.com": "Google OAuth login",
    "oauth2.googleapis.com": "Google OAuth token",
    "www.googleapis.com": "Google OAuth user info",
    "auth.x.ai": "xAI OAuth",
    "auth.kimi.com": "Kimi OAuth",
    "chatgpt.com": "Codex external refresh",
}

PROCESS_NAMES = {"gjl", "gjl-cli", "gjl-desktop", "desktop"}


@dataclass(frozen=True)
class Destination:
    host: str
    port: int
    label: str
    source: str


def safe(value: object) -> str:
    return "".join(ch if ch.isprintable() and ch not in "\r\n\t" else "?" for ch in str(value))


def process_name(value: str) -> str:
    name = os.path.basename(value).lower()
    if name.endswith(".exe"):
        name = name[:-4]
    return name.replace("_", "-").replace(" ", "-")


def is_gjl_process(name: str) -> bool:
    return name in PROCESS_NAMES or name.startswith(("gjl-windows-", "gjl-linux-", "gjl-darwin-"))


def find_gjl(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    # Prefer the running daemon's own binary, then a CLI beside Desktop.
    desktop_paths: list[Path] = []
    for proc in psutil.process_iter(attrs=["pid", "name"], ad_value=None):
        name = process_name(proc.info.get("name") or "")
        if not is_gjl_process(name):
            continue
        try:
            executable = Path(proc.exe())
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            continue
        if name == "gjl" or name.startswith(("gjl-windows-", "gjl-linux-", "gjl-darwin-")):
            return str(executable)
        desktop_paths.append(executable.parent)
    for folder in desktop_paths:
        candidate = folder / ("gjl.exe" if sys.platform == "win32" else "gjl")
        if candidate.is_file():
            return str(candidate)
    return shutil.which("gjl")


def endpoint(value: str) -> tuple[str, int] | None:
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https", "ws", "wss"} or not parsed.hostname:
            return None
        port = parsed.port or (443 if parsed.scheme in {"https", "wss"} else 80)
        return parsed.hostname.lower().rstrip("."), port
    except ValueError:
        return None


def manual_endpoint(value: str) -> Destination:
    if "=" not in value:
        raise ValueError("label must be NAME=HOST:PORT")
    label, address = value.split("=", 1)
    if not label.strip() or any(ch in label for ch in "\r\n\t"):
        raise ValueError("label name must be nonempty and one line")
    parsed = endpoint(address) if "://" in address else endpoint("https://" + address)
    if parsed is None:
        raise ValueError("label destination must be HOST:PORT or an HTTP(S) URL")
    return Destination(*parsed, label.strip(), "manual")


def query_gjl(gjl: str, command: list[str], ipc: str | None) -> object | None:
    args = [gjl, *command]
    if ipc:
        args += ["--ipc", ipc]
    try:
        result = subprocess.run(args, capture_output=True, timeout=8, check=False)
        if result.returncode == 0 and len(result.stdout) <= 8 * 1024 * 1024:
            return json.loads(result.stdout)
    except (OSError, subprocess.TimeoutExpired, ValueError, json.JSONDecodeError):
        pass
    return None


def labels_from_gjl(gjl: str | None, ipc: str | None) -> tuple[list[Destination], dict[int, str], list[str]]:
    labels: list[Destination] = []
    listener_ports: dict[int, str] = {}
    notes: list[str] = []
    if not gjl:
        return labels, listener_ports, ["gjl CLI not found; Route and Gate/Vault labels unavailable"]

    document = query_gjl(gjl, ["config", "get"], ipc)
    if isinstance(document, dict):
        listeners = document.get("listeners", [])
        routes = document.get("routes", [])
        route_listeners: dict[str, set[str]] = defaultdict(set)
        if isinstance(listeners, list):
            for item in listeners:
                if not isinstance(item, dict):
                    continue
                listener_id = str(item.get("id", "?"))
                route_id = item.get("route_id")
                if isinstance(route_id, str) and route_id:
                    route_listeners[route_id].add(listener_id)
                for matcher in item.get("route_matchers", []):
                    if isinstance(matcher, dict) and isinstance(matcher.get("route_id"), str):
                        route_listeners[matcher["route_id"]].add(listener_id)
                address = item.get("address", "")
                if isinstance(address, str):
                    parsed = endpoint("http://" + address)
                    if parsed:
                        listener_ports[parsed[1]] = f"{item.get('role', '?')} listener {listener_id}"
                        labels.append(Destination(parsed[0], parsed[1], listener_ports[parsed[1]], "config"))
        if isinstance(routes, list):
            for route in routes:
                if not isinstance(route, dict):
                    continue
                upstream = route.get("upstream")
                parsed = endpoint(upstream) if isinstance(upstream, str) else None
                if parsed:
                    route_id = str(route.get("id", "?"))
                    via = ",".join(sorted(route_listeners.get(route_id, set()))) or "unbound"
                    label = f"{route.get('target', 'provider')} Route {route_id} via {via}"
                    labels.append(Destination(*parsed, label, "config"))
        notes.append(f"config revision {document.get('revision', '?')} read via local IPC")
    else:
        notes.append("config get unavailable; Route and listener labels unavailable")

    connections = query_gjl(gjl, ["connection", "list"], ipc)
    if isinstance(connections, dict) and isinstance(connections.get("connections"), list):
        for item in connections["connections"]:
            if not isinstance(item, dict):
                continue
            parsed = endpoint(item.get("endpoint", ""))
            if parsed:
                labels.append(Destination(*parsed, f"{item.get('kind', 'remote')} connection {item.get('id', '?')}", "connection"))
        notes.append("Gate/Vault connections read via local IPC")
    else:
        notes.append("connection list unavailable; Gate/Vault labels may be missing")
    return labels, listener_ports, notes


def address_ips(host: str, port: int) -> set[str]:
    try:
        return {ipaddress.ip_address(host.split("%", 1)[0]).compressed}
    except ValueError:
        pass
    try:
        return {
            ipaddress.ip_address(item[4][0].split("%", 1)[0]).compressed
            for item in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        }
    except (OSError, ValueError):
        return set()


class Catalog:
    def __init__(self, destinations: list[Destination]) -> None:
        self.lock = threading.Lock()
        self.index: dict[tuple[str, int], list[Destination]] = {}
        self.unresolved: set[str] = set()
        self.pending = len(destinations)
        queue: Queue[Destination] = Queue()
        for item in destinations:
            queue.put(item)

        def worker() -> None:
            while True:
                try:
                    item = queue.get_nowait()
                except Empty:
                    return
                addresses = address_ips(item.host, item.port)
                with self.lock:
                    if not addresses:
                        self.unresolved.add(item.host)
                    for address in addresses:
                        key = (address, item.port)
                        old = self.index.get(key, [])
                        if item not in old:
                            self.index[key] = [*old, item]
                    self.pending -= 1

        for _ in range(min(4, len(destinations))):
            threading.Thread(target=worker, daemon=True).start()

    def snapshot(self) -> tuple[dict[tuple[str, int], list[Destination]], int, list[str]]:
        with self.lock:
            return dict(self.index), self.pending, sorted(self.unresolved)


def selected_processes(explicit_pids: set[int]) -> dict[int, tuple["psutil.Process", str, float]]:
    found: dict[int, tuple["psutil.Process", str, float]] = {}
    parents: dict[int, int] = {}
    for pid, parent, raw_name in process_rows():
        name = process_name(raw_name)
        parents[pid] = parent
        if pid in explicit_pids or is_gjl_process(name):
            try:
                proc = psutil.Process(pid)
                found[pid] = (proc, name or "?", proc.create_time())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    # Include refresh helpers and other children while their parent relationship exists.
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if pid not in found and parent in found:
                try:
                    proc = psutil.Process(pid)
                    found[pid] = (proc, process_name(proc.name()), proc.create_time())
                    changed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    return found


def process_rows() -> list[tuple[int, int, str]]:
    if sys.platform == "win32":
        return windows_process_rows()
    return [
        (proc.info["pid"], proc.info.get("ppid") or 0, proc.info.get("name") or "")
        for proc in psutil.process_iter(attrs=["pid", "ppid", "name"], ad_value=None)
    ]


def windows_process_rows() -> list[tuple[int, int, str]]:
    """One Toolhelp snapshot avoids expensive per-PID ppid calls on Windows."""
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        _fields_ = [
            ("size", wintypes.DWORD), ("usage", wintypes.DWORD),
            ("pid", wintypes.DWORD), ("heap", ctypes.c_size_t),
            ("module", wintypes.DWORD), ("threads", wintypes.DWORD),
            ("parent", wintypes.DWORD), ("priority", wintypes.LONG),
            ("flags", wintypes.DWORD), ("name", wintypes.WCHAR * 260),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32FirstW.restype = wintypes.BOOL
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateToolhelp32Snapshot(0x00000002, 0)
    if handle == ctypes.c_void_p(-1).value:
        return []
    rows: list[tuple[int, int, str]] = []
    try:
        entry = ProcessEntry()
        entry.size = ctypes.sizeof(entry)
        if kernel.Process32FirstW(handle, ctypes.byref(entry)):
            while True:
                rows.append((entry.pid, entry.parent, entry.name))
                if not kernel.Process32NextW(handle, ctypes.byref(entry)):
                    break
    finally:
        kernel.CloseHandle(handle)
    return rows


def socket_address(value: object) -> tuple[str, int] | None:
    try:
        if not value:
            return None
        return ipaddress.ip_address(value.ip.split("%", 1)[0]).compressed, int(value.port)
    except (AttributeError, TypeError, ValueError):
        return None


def describe_peer(
    peer: tuple[str, int],
    local: tuple[str, int],
    listening_ports: dict[int, str],
    configured_listeners: dict[int, str],
    catalog: dict[tuple[str, int], list[Destination]],
) -> tuple[str, str]:
    if local[1] in listening_ports:
        return "INBOUND", listening_ports[local[1]]
    matches = catalog.get(peer, [])
    if matches:
        names = sorted({f"{item.label} ({item.host}:{item.port})" for item in matches})
        literal = any(item.host == peer[0] for item in matches)
        suffix = "exact IP" if literal else "DNS/IP match; hostname not observed"
        return "LABELED", "; ".join(names) + " [" + suffix + "]"
    if peer[1] in configured_listeners and ipaddress.ip_address(peer[0]).is_loopback:
        return "LABELED", configured_listeners[peer[1]] + " [loopback port match]"
    return "UNKNOWN", "unknown destination"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=600, help="seconds to observe; 0 runs until Ctrl+C (default: 600)")
    parser.add_argument("--interval", type=float, default=0.2, help="poll interval in seconds (default: 0.2)")
    parser.add_argument("--pid", type=int, action="append", default=[], help="also observe this process and its children")
    parser.add_argument("--gjl", help="path to bundled gjl CLI (default: search PATH)")
    parser.add_argument("--ipc", help="IPC address for a nondefault daemon profile")
    parser.add_argument("--label", action="append", default=[], metavar="NAME=HOST:PORT", help="add a descriptive endpoint label")
    parser.add_argument("--no-config", action="store_true", help="skip read-only gjl CLI queries")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.duration < 0 or not 0.05 <= args.interval <= 10 or any(pid <= 0 for pid in args.pid):
        raise SystemExit("duration must be >= 0, interval 0.05..10, and PIDs positive")
    try:
        manual = [manual_endpoint(value) for value in args.label]
    except ValueError as error:
        raise SystemExit(str(error)) from error

    gjl = None if args.no_config else find_gjl(args.gjl)
    dynamic, configured_listeners, notes = labels_from_gjl(gjl, args.ipc) if not args.no_config else ([], {}, ["CLI lookup disabled"])
    builtins = [Destination(host, 443, label, "built-in") for host, label in BUILT_IN_HOSTS.items()]
    catalog = Catalog([*dynamic, *builtins, *manual])

    print("gjl connection observer - destination labels only; no safety verdict")
    for note in notes:
        print("source:", safe(note))
    print("source: label DNS lookup runs in background")
    print("scope: TCP/connected UDP sockets of gjl, Desktop, and visible children")
    print("TIME                 DIR      PROCESS (PID)             LOCAL -> REMOTE                         LABEL")
    sys.stdout.flush()

    started = time.monotonic()
    seen: dict[tuple[object, ...], tuple[str, str, str]] = {}
    observed_pids: set[int] = set()
    unreadable: set[int] = set()
    scans = 0
    explicit_pids = set(args.pid)
    try:
        while args.duration == 0 or time.monotonic() - started < args.duration:
            cycle_started = time.monotonic()
            current_catalog, _, _ = catalog.snapshot()
            processes = selected_processes(explicit_pids)
            observed_pids.update(processes)
            sockets: list[tuple[int, str, float, object]] = []
            listening_ports = dict(configured_listeners)
            for pid, (proc, name, birth) in processes.items():
                try:
                    connections = proc.net_connections(kind="inet")
                except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
                    unreadable.add(pid)
                    continue
                for conn in connections:
                    local = socket_address(conn.laddr)
                    if local and conn.status == psutil.CONN_LISTEN:
                        listening_ports.setdefault(local[1], f"local listener in {name} ({pid})")
                    elif local and conn.raddr:
                        sockets.append((pid, name, birth, conn))
            for pid, name, birth, conn in sockets:
                local = socket_address(conn.laddr)
                remote = socket_address(conn.raddr)
                if not local or not remote:
                    continue
                transport = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                key = (pid, birth, transport, local, remote)
                if key in seen:
                    continue
                direction, label = describe_peer(remote, local, listening_ports, configured_listeners, current_catalog)
                clock = time.strftime("%Y-%m-%d %H:%M:%S")
                endpoint_text = f"{local[0]}:{local[1]} -> {remote[0]}:{remote[1]} {transport}"
                print(f"{clock}  {direction:<8} {safe(name)[:18]:<18} ({pid:<6}) {endpoint_text:<39} {safe(label)}")
                sys.stdout.flush()
                seen[key] = (direction, label, endpoint_text)
            scans += 1
            time.sleep(max(0.0, args.interval - (time.monotonic() - cycle_started)))
    except KeyboardInterrupt:
        print("\nStopped by user.")

    final_catalog, pending, unresolved = catalog.snapshot()
    unknown = []
    late_labels = []
    for key, details in seen.items():
        if details[0] != "UNKNOWN":
            continue
        direction, label = describe_peer(key[4], key[3], {}, configured_listeners, final_catalog)
        if direction == "UNKNOWN":
            unknown.append((key, details))
        else:
            late_labels.append((key, details, label))
    print(f"\nObserved socket tuples: {len(seen)}; unknown labels: {len(unknown)}; processes: {len(observed_pids)}; scans: {scans}")
    for key, details, label in late_labels:
        print(f"  LATE LABEL pid={key[0]} {details[2]}: {safe(label)}")
    for key, details in unknown:
        print(f"  UNKNOWN pid={key[0]} {details[2]}")
    if unresolved:
        print("Unresolved label hosts:", ", ".join(safe(host) for host in unresolved))
    if pending:
        print(f"DNS labels still pending: {pending}; some UNKNOWN rows may be due to unresolved names")
    if unreadable:
        print("Could not inspect socket information for PIDs:", ", ".join(map(str, sorted(unreadable))))
    if not observed_pids:
        print("No matching gjl process was seen. Use --pid if its executable has another name.")
    print("Labels are IP/DNS hints from a start-of-run config snapshot; the user interprets the connections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
