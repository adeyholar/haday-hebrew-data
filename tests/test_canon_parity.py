"""canon.ts must agree with canon.py on every distinct Hebrew string in the corpus.

Runs packages/canon/parity.ts under Node (22.6+ for --experimental-strip-types). Set NODE to pick
a binary. Without a capable Node the test is skipped locally and fails on CI (CI=true).
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from builder.canon import canon
from corpus import books, uxlc

ROOT = Path(__file__).resolve().parents[1]


def _node() -> str | None:
    node = os.environ.get("NODE") or shutil.which("node")
    if not node:
        return None
    probe = subprocess.run([node, "--experimental-strip-types", "-e", ""], capture_output=True)
    return node if probe.returncode == 0 else None


class CanonParity(unittest.TestCase):
    def test_canon_ts_matches_canon_py(self):
        node = _node()
        if node is None:
            if os.environ.get("CI"):
                self.fail("CI needs Node with --experimental-strip-types for the canon parity check")
            self.skipTest("no Node with --experimental-strip-types")
        seen: set[str] = set()
        for book in books():
            for verse in book["verses"]:
                seen.update((verse["text_src"], verse["text"]))
                for word in verse["words"]:
                    seen.update((word["surface_src"], word["surface"]))
                    seen.update(alt["rdg"] for alt in word.get("alternatives") or [])
        for verses in uxlc().values():
            for words in verses.values():
                seen.update(word["text"] for word in words)
        seen.discard("")
        pairs = [[text, canon(text)] for text in sorted(seen)]
        self.assertGreater(len(pairs), 100000)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pairs.json"
            path.write_text(json.dumps(pairs, ensure_ascii=False), encoding="utf-8")
            run = subprocess.run(
                [node, "--experimental-strip-types", str(ROOT / "packages" / "canon" / "parity.ts"), str(path)],
                capture_output=True,
                text=True,
            )
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        self.assertIn("canon parity ok", run.stdout)


if __name__ == "__main__":
    unittest.main()
