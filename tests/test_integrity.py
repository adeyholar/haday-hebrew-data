"""Source pins and the explicit triage decision column."""

import collections
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from builder.overrides import DECISIONS, TriageError, row_decision  # noqa: E402
from builder.sources import SourceMismatch, pinned, verify_sources  # noqa: E402

TRIAGE = ROOT / "sources" / "uxlc-triage-v1.1.1.csv"


class Integrity(unittest.TestCase):
    def test_sources_match_the_pins(self):
        sums = verify_sources()
        self.assertIn("uxlc-triage-v1.1.1.csv", sums)
        self.assertIn("Tanach.xml.zip", sums)
        self.assertEqual(sum(1 for name in sums if name.startswith("morphhb-wlc/")), 39)

    def test_a_changed_source_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_bytes(b"one\n")
            (root / "SHA256SUMS").write_text("0" * 64 + "  a.txt\n", encoding="utf-8")
            with self.assertRaises(SourceMismatch):
                verify_sources(root)
            (root / "SHA256SUMS").write_text("", encoding="utf-8")
            with self.assertRaises(SourceMismatch):
                verify_sources(root)

    def test_sources_are_binary_in_git(self):
        rules = (ROOT / ".gitattributes").read_text(encoding="utf-8").split("\n")
        self.assertIn("sources/** -text", rules)
        self.assertNotIn(b"\r\n", TRIAGE.read_bytes())

    def test_decision_column(self):
        with TRIAGE.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        counts = collections.Counter(row_decision(row) for row in rows)
        self.assertEqual(set(counts) - set(DECISIONS), set())
        self.assertEqual(
            dict(counts),
            {"override": 567, "compare": 292, "uncertain": 147, "optional": 98, "leave": 51, "divide": 10, "join": 6},
        )

    def test_unknown_decision_fails(self):
        for value in ("", "apply", "Override", None):
            with self.assertRaises(TriageError):
                row_decision({"ref": "Gen.1.1", "word_id": "x", "decision": value, "recommended_action": "documented override candidate"})

    def test_pins_cover_every_file(self):
        names = set(pinned())
        files = {p.relative_to(ROOT / "sources").as_posix() for p in (ROOT / "sources").rglob("*") if p.is_file()}
        self.assertEqual(files - names, {"SHA256SUMS", "PINS.txt"})


if __name__ == "__main__":
    unittest.main()
