"""Optional end-to-end observer test against a real gjl daemon."""

import http.client
import csv
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
from pathlib import Path


GJL = os.environ.get("GJL_TEST_BINARY")
GJL_SOURCE = os.environ.get("GJL_TEST_SOURCE")
OBSERVER = Path(__file__).with_name("observe_connections.py")


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def command(binary, *args):
    result = subprocess.run([binary, *args], capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise AssertionError(f"gjl {' '.join(args[:2])} failed: {result.stderr[:1000]}")
    return json.loads(result.stdout)


def prepare_private_directory(path):
    if sys.platform == "win32":
        identity = subprocess.check_output(["whoami", "/user", "/fo", "csv", "/nh"], text=True)
        sid = next(csv.reader(io.StringIO(identity)))[1]
        for options in (
            ["/inheritance:r"],
            ["/remove:g", "*S-1-5-32-544", "*S-1-3-4"],
            ["/grant:r", f"*{sid}:(OI)(CI)F", "*S-1-5-18:(OI)(CI)F"],
        ):
            subprocess.run(["icacls", str(path), *options], capture_output=True, check=True)
    else:
        os.chmod(path, 0o700)


@unittest.skipUnless(GJL or GJL_SOURCE, "set GJL_TEST_BINARY or GJL_TEST_SOURCE")
class LiveGJLObserverTest(unittest.TestCase):
    def test_real_daemon_route_and_outbound_socket(self):
        with tempfile.TemporaryDirectory(prefix="gjl-observer-") as root:
            root_path = Path(root)
            prepare_private_directory(root_path)
            if GJL_SOURCE:
                binary = str(root_path / ("gjl.exe" if sys.platform == "win32" else "gjl"))
                subprocess.run(["go", "build", "-o", binary, "./cmd/gjl"],
                               cwd=GJL_SOURCE, capture_output=True, check=True, timeout=180)
            else:
                binary = str(Path(GJL).resolve())
            ipc = (rf"\\.\pipe\gjl-observer-{uuid.uuid4().hex}"
                   if sys.platform == "win32" else str(root_path / "management.sock"))
            config_path = root_path / "config.json"
            log_path = root_path / "daemon.log"
            with log_path.open("wb") as log:
                daemon = subprocess.Popen(
                    [binary, "daemon", "--config", str(config_path), "--ipc", ipc],
                    stdout=log, stderr=log,
                )
                try:
                    for _ in range(60):
                        if daemon.poll() is not None:
                            raise AssertionError(f"daemon exited early: {log_path.read_text(errors='replace')[:1000]}")
                        try:
                            status = command(binary, "status", "--ipc", ipc)
                            if status.get("config_revision") == 1:
                                break
                        except (AssertionError, subprocess.TimeoutExpired):
                            time.sleep(0.1)
                    else:
                        raise AssertionError("daemon did not start")

                    provider_port = free_port()
                    door_port = free_port()
                    route = {
                        "id": "observer-route", "role": "door", "provider_surface": "openai_api",
                        "target": "provider", "upstream": f"https://127.0.0.1:{provider_port}/v1",
                        "credential": {"source": "passthrough"},
                        "inbound_auth_policy": "mismatch_passthrough",
                        "masking_rules": [], "traffic_log_enabled": False,
                        "masking_audit_enabled": False, "usage_tracking_enabled": False,
                    }
                    route_file = root_path / "route.json"
                    route_file.write_text(json.dumps(route), encoding="utf-8")
                    command(binary, "route", "put", "--expected-revision", "1", "--ipc", ipc, str(route_file))
                    listener = {
                        "id": "observer-door", "role": "door", "network": "tcp",
                        "address": f"127.0.0.1:{door_port}",
                        "transport_mode": "door_loopback_plaintext", "route_id": "observer-route",
                    }
                    listener_file = root_path / "listener.json"
                    listener_file.write_text(json.dumps(listener), encoding="utf-8")
                    command(binary, "listener", "put", "--expected-revision", "2", "--ipc", ipc, str(listener_file))

                    accepted = threading.Event()

                    def mock_provider():
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            server.bind(("127.0.0.1", provider_port))
                            server.listen(1)
                            server.settimeout(5)
                            try:
                                peer, _ = server.accept()
                                with peer:
                                    accepted.set()
                                    time.sleep(1.5)  # Keep the TLS socket visible to the observer.
                            except socket.timeout:
                                pass

                    provider_thread = threading.Thread(target=mock_provider, daemon=True)
                    provider_thread.start()
                    observer = subprocess.Popen(
                        [sys.executable, str(OBSERVER), "--gjl", binary, "--ipc", ipc,
                         "--duration", "3", "--interval", "0.05"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    )

                    def request_door():
                        try:
                            client = http.client.HTTPConnection("127.0.0.1", door_port, timeout=3)
                            client.request("POST", "/v1/chat/completions", body=b"{}",
                                           headers={"Content-Type": "application/json",
                                                    "Authorization": "Bearer test-only"})
                            client.getresponse().read()
                            client.close()
                        except (OSError, http.client.HTTPException):
                            pass  # The mock server intentionally does not finish TLS.

                    time.sleep(0.7)
                    request_thread = threading.Thread(target=request_door, daemon=True)
                    request_thread.start()
                    output, errors = observer.communicate(timeout=8)
                    self.assertEqual(observer.returncode, 0, errors)
                    self.assertTrue(accepted.is_set(), "gjl did not contact the mock provider")
                    self.assertIn("config revision 3 read via local IPC", output)
                    self.assertIn(f"provider Route observer-route via observer-door (127.0.0.1:{provider_port})", output)
                finally:
                    daemon.terminate()
                    daemon.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
