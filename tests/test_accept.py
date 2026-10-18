import unittest
from pathlib import Path

from builder.canon import canon, multiset
from builder.oshb import load_oshb

ROOT = Path(__file__).resolve().parents[1]


class Accept(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.books = load_oshb(ROOT / "sources" / "morphhb-wlc")

    def test_gen_1_1(self):
        verse = self.books[0]["verses"][0]
        self.assertEqual(verse["ref"], "Gen.1.1")
        self.assertEqual(verse["word_count"], 7)
        accents = [row["name"] for word in verse["words"] for row in word["accents"] if row["name"] != "silluq"]
        self.assertEqual(accents, ["tipcha", "munach", "atnach", "merkha", "tipcha", "merkha"])
        last = verse["words"][-1]
        self.assertEqual(last["meteg"], [{"letter_index": 1, "function": "silluq"}])
        self.assertTrue(verse["text"].endswith("\u05C3"))
        self.assertEqual(sum(word["surface"].count("\u05C1") for word in verse["words"]), 2)
        self.assertEqual(verse["rhythm"]["split"], 3)
        self.assertEqual(verse["rhythm"]["governor"], "silluq")
        paths = [word.get("rhythm_path") for word in verse["words"]]
        self.assertEqual(paths, ["1.0", None, "1", None, "0.0", None, "0"])
        first = verse["words"][0]
        self.assertEqual(first["stress"]["letter_index"], 3)
        self.assertEqual(first["stress"]["syll_from_end"], 1)
        self.assertEqual(first["stress"]["source"], "accent")
        self.assertEqual(last["stress"]["source"], "silluq")
        self.assertEqual(last["stress"]["syll_from_end"], 2)

    def test_stress_vectors(self):
        gen = {verse["ref"]: verse for verse in self.books[0]["verses"][:3]}
        expect = {
            ("Gen.1.1", "בראשית"): (3, 1, "accent"),
            ("Gen.1.1", "הארץ"): (1, 2, "silluq"),
            ("Gen.1.2", "והארץ"): (2, 2, "accent"),
            ("Gen.1.2", "תהו"): (0, 2, "doubled"),
            ("Gen.1.3", "ויאמר"): (1, 2, "accent"),
        }
        for (ref, letters), (index, syll, source) in expect.items():
            word = next(word for word in gen[ref]["words"] if word["consonants"] == letters)
            self.assertEqual(word["stress"]["letter_index"], index, letters)
            self.assertEqual(word["stress"]["syll_from_end"], syll, letters)
            self.assertEqual(word["stress"]["source"], source, letters)

    def test_counts_and_marks(self):
        verses = [verse for book in self.books for verse in book["verses"]]
        words = [word for verse in verses for word in verse["words"]]
        main = [word for word in words if word.get("kq_role") != "qere"]
        qere = [word for word in words if word.get("kq_role") == "qere"]
        self.assertEqual(len(self.books), 39)
        self.assertEqual(len(verses), 23213)
        self.assertEqual(len(main), 305507)
        self.assertEqual(len(qere), 1278)
        self.assertEqual(sum(1 for verse in verses if verse["has_sof_pasuq"]), 23192)
        self.assertEqual(len({word["id"] for word in words}), len(words))
        for word in words:
            self.assertEqual(multiset(word["surface"]), multiset(word["surface_src"]))
            self.assertEqual(canon(word["surface"]), word["surface"])

    def test_prose_rhythm_on_genesis(self):
        ok = n = 0
        for verse in self.books[0]["verses"]:
            flags = [word["rhythm_match"] for word in verse["words"] if word.get("rhythm_match") in (True, False)]
            if not flags:
                continue
            n += 1
            ok += int(all(flags))
        self.assertGreaterEqual(ok / n, 0.98)


if __name__ == "__main__":
    unittest.main()
