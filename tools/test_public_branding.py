from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]


class PublicBrandingTest(unittest.TestCase):
    def test_tracked_public_files_exclude_internal_only_term(self) -> None:
        forbidden = ("geum" + "jul").casefold()
        result = subprocess.run(
            ["git", "-C", str(REPOSITORY), "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
        )
        failures: list[str] = []

        for encoded_name in result.stdout.split(b"\0"):
            if not encoded_name:
                continue
            relative = encoded_name.decode("utf-8")
            if forbidden in relative.casefold():
                failures.append(f"path: {relative}")

            path = REPOSITORY / relative
            try:
                raw = path.read_bytes()
            except FileNotFoundError:
                continue
            if b"\0" in raw:
                continue
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            offset = text.casefold().find(forbidden)
            if offset >= 0:
                line = text.count("\n", 0, offset) + 1
                failures.append(f"content: {relative}:{line}")

        self.assertEqual(
            failures,
            [],
            "The public repository must use only the official gjl brand:\n"
            + "\n".join(failures),
        )


if __name__ == "__main__":
    unittest.main()
