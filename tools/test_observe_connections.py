"""Small cross-platform checks for the public connection observer."""

import os
import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import observe_connections as observer


class ObserverTests(unittest.TestCase):
    def test_packaged_process_names(self):
        self.assertTrue(observer.is_gjl_process(observer.process_name("gjl_desktop.exe")))
        self.assertTrue(observer.is_gjl_process(observer.process_name("gjl-linux-arm64")))
        self.assertTrue(observer.is_gjl_process(observer.process_name("gjl Desktop")))

    def test_route_matcher_and_remote_connection_labels(self):
        config = {
            "revision": 7,
            "listeners": [{"id": "gate-main", "role": "gate", "address": "127.0.0.1:9443",
                           "route_matchers": [{"route_id": "model-a"}]}],
            "routes": [{"id": "model-a", "target": "provider", "upstream": "https://api.example.test/v1"}],
        }
        connections = {"connections": [{"id": "vault-one", "kind": "vault",
                                         "endpoint": "https://vault.example.test:9555"}]}
        with patch.object(observer, "query_gjl", side_effect=[config, connections]):
            labels, listeners, notes = observer.labels_from_gjl("gjl", None)
        self.assertEqual(listeners[9443], "gate listener gate-main")
        self.assertTrue(any(item.host == "api.example.test" and "via gate-main" in item.label for item in labels))
        self.assertTrue(any(item.port == 9555 and "vault-one" in item.label for item in labels))
        self.assertTrue(any("revision 7" in note for note in notes))

    def test_unknown_stays_unknown(self):
        direction, label = observer.describe_peer(("203.0.113.4", 443), ("127.0.0.1", 50000), {}, {}, {})
        self.assertEqual((direction, label), ("UNKNOWN", "unknown destination"))

    def test_visible_child_is_included(self):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"])
        try:
            selected = observer.selected_processes({os.getpid()})
            self.assertIn(child.pid, selected)
        finally:
            child.terminate()
            child.wait(timeout=5)

    def test_live_loopback_socket_is_labeled(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]
            with socket.create_connection(("127.0.0.1", port)) as client:
                accepted, _ = server.accept()
                with accepted:
                    command = [sys.executable, str(Path(__file__).with_name("observe_connections.py")),
                               "--no-config", "--pid", str(os.getpid()),
                               "--label", f"Test peer=127.0.0.1:{port}",
                               "--duration", "0.7", "--interval", "0.05"]
                    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(f"Test peer (127.0.0.1:{port}) [exact IP]", result.stdout)
                    self.assertIn("INBOUND", result.stdout)


if __name__ == "__main__":
    unittest.main()
