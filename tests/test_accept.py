import json
import unittest
from collections import Counter
from pathlib import Path

from builder.canon import MAQAF, PASEQ, canon, clusters, multiset
from corpus import books as corpus_books
from builder.stress import FULL, _marks, _nuclei, _vowel_letter_vav

ROOT = Path(__file__).resolve().parents[1]
ACCENT_RANGE = range(0x0591, 0x05B0)


class Accept(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.books = corpus_books()

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
        self.assertEqual(len(main), 305501)
        self.assertEqual(len(qere), 1278)
        self.assertEqual(sum(1 for verse in verses if verse["has_sof_pasuq"]), 23192)
        self.assertEqual(len({word["id"] for word in words}), len(words))
        for word in words:
            self.assertEqual(canon(word["surface"]), word["surface"])
            if word.get("override"):
                continue
            self.assertEqual(multiset(word["surface"]), multiset(word["surface_src"]))

    def test_prose_rhythm_on_genesis(self):
        ok = n = 0
        for verse in self.books[0]["verses"]:
            flags = [word["rhythm_match"] for word in verse["words"] if word.get("rhythm_match") in (True, False)]
            if not flags:
                continue
            n += 1
            ok += int(all(flags))
        self.assertGreaterEqual(ok / n, 0.98)

    def test_corpus_rhythm_floors(self):
        # Prose cleared 98% (18,689 / 18,748). Poetry cleared 95% after the near/remote
        # divider and the virtual atnach (revia gadol when atnach is absent).
        # Do not drop either floor to hide a regression.
        prose_ok = prose_n = poetic_ok = poetic_n = 0
        for book in self.books:
            for verse in book["verses"]:
                flags = [word["rhythm_match"] for word in verse["words"] if word.get("rhythm_match") in (True, False)]
                if not flags:
                    continue
                good = all(flags)
                if verse["system"] == "poetic":
                    poetic_n += 1
                    poetic_ok += int(good)
                else:
                    prose_n += 1
                    prose_ok += int(good)
        self.assertGreaterEqual(prose_ok / prose_n, 0.98)
        self.assertGreaterEqual(poetic_ok / poetic_n, 0.95)

    def test_vowel_letter_stress(self):
        gen = {verse["ref"]: verse for verse in self.books[0]["verses"][:5]}
        expect = [
            ("Gen.1.2", "תהום"),
            ("Gen.1.2", "ורוח"),
            ("Gen.1.3", "אור"),
            ("Gen.1.4", "טוב"),
            ("Gen.1.5", "יום"),
        ]
        for ref, letters in expect:
            words = [word for word in gen[ref]["words"] if word["consonants"] == letters and word.get("stress")]
            self.assertTrue(words, letters)
            for word in words:
                self.assertEqual(word["stress"]["syll_from_end"], 1, word["surface"])

    def test_vowel_letter_never_counts_as_a_following_syllable(self):
        for book in self.books:
            for verse in book["verses"]:
                for word in verse["words"]:
                    stress = word.get("stress")
                    if not stress:
                        continue
                    groups = clusters(word["surface"])
                    index = stress["letter_index"]
                    if index is None or index + 1 >= len(groups):
                        continue
                    if _marks(groups[index][1]) & FULL:
                        continue
                    if _vowel_letter_vav(groups[index][0], _marks(groups[index][1])):
                        continue
                    next_letter, next_marks = groups[index + 1]
                    if not _vowel_letter_vav(next_letter, _marks(next_marks)):
                        continue
                    nuclei = _nuclei(word["surface"])
                    self.assertIn(index, nuclei, word["id"])
                    self.assertNotIn(index + 1, nuclei, word["id"])
                    after = sum(1 for n in nuclei if n > index)
                    self.assertEqual(word["stress"]["syll_from_end"], 1 + after, word["id"])

    def test_separators_and_qere_trailers(self):
        words = [word for book in self.books for verse in book["verses"] for word in verse["words"]]
        main = [word for word in words if word.get("kq_role") != "qere"]
        qere = [word for word in words if word.get("kq_role") == "qere"]
        self.assertEqual(sum(word["trailer"].count(MAQAF) for word in main), 42568)
        self.assertEqual(sum(word["trailer"].count(MAQAF) for word in qere), 7)
        self.assertEqual(sum(word["trailer"].count(PASEQ) for word in main), 2273)
        self.assertEqual(sum(word["trailer"].count(PASEQ) for word in qere), 5)
        alts = [alt for word in words for alt in word.get("alternatives") or []]
        self.assertEqual(sum(1 for alt in alts if alt["note_type"] == "alternative"), 119)
        self.assertEqual(sum(1 for alt in alts if alt["note_type"] == "exegesis"), 21)

    def test_histogram_is_frozen_from_the_source(self):
        expected = json.loads((ROOT / "tests" / "expected-histogram.json").read_text(encoding="utf-8"))
        found: Counter[str] = Counter()
        for book in self.books:
            for verse in book["verses"]:
                for word in verse["words"]:
                    if word.get("kq_role") == "qere":
                        continue
                    for ch in word["surface_src"]:
                        found[f"U+{ord(ch):04X}"] += 1
        self.assertEqual(dict(found), expected)

    def test_every_accent_mark_is_a_row(self):
        for book in self.books:
            for verse in book["verses"]:
                for word in verse["words"]:
                    in_text = sum(1 for ch in word["surface"] if ord(ch) in ACCENT_RANGE)
                    in_rows = 0
                    for row in word.get("accents") or []:
                        cp = row.get("cp") or ""
                        if not cp.startswith("U+"):
                            continue
                        if int(cp[2:], 16) in ACCENT_RANGE:
                            in_rows += 1
                    self.assertEqual(in_text, in_rows, word["id"])

    def test_sof_verses_have_a_silluq_governor(self):
        for book in self.books:
            for verse in book["verses"]:
                if not verse["has_sof_pasuq"]:
                    continue
                self.assertIsNotNone(verse["rhythm"], verse["ref"])
                self.assertEqual(verse["rhythm"].get("governor"), "silluq", verse["ref"])

    def test_ketiv_final_silluq_comes_from_the_qere(self):
        verse = next(item for item in self.books[0]["verses"] if item["ref"] == "Gen.27.3")
        qere = [word for word in verse["words"] if word.get("kq_role") == "qere"]
        self.assertTrue(any(row["function"] == "silluq" for word in qere for row in word.get("meteg") or []))

    def test_paseq_is_spaced_and_prose_mahpakh_is_not_legarmeh(self):
        verse = next(item for item in self.books[0]["verses"] if item["ref"] == "Gen.1.5")
        self.assertIn(" \u05C0 ", verse["text"])
        word = next(word for word in verse["words"] if PASEQ in word["trailer"])
        self.assertNotIn("legarmeh", [row["name"] for row in word["accents"]])
        self.assertFalse(any(word.get("trailer") == "  \u05c0 " for book in self.books for verse in book["verses"] for word in verse["words"]))

    def test_no_sof_verse_is_not_given_a_silluq(self):
        verse = next(item for item in self.books[3]["verses"] if item["ref"] == "Num.25.19")
        self.assertEqual(verse["has_sof_pasuq"], 0)
        self.assertEqual(verse["rhythm"].get("governor"), "atnach")
        last = verse["words"][-1]
        self.assertEqual(last["rhythm_path_computed"], "0")
        self.assertTrue(last["rhythm_match"])
        for word in verse["words"]:
            self.assertFalse(word.get("silluq_inferred"))
            self.assertNotIn("silluq", [row["name"] for row in word.get("accents") or []])

    def test_revia_before_ole_is_revia_qatan(self):
        verse = next(item for item in self.books[26]["verses"] if item["ref"] == "Ps.1.2")
        word = next(word for word in verse["words"] if word["consonants"] == "יהוה")
        self.assertEqual(word["main_accent"], "revia_qatan")
        self.assertIn("revia_qatan", [row["name"] for row in word["accents"]])

    def test_poetic_munach_paseq_is_not_legarmeh(self):
        found = 0
        for book in self.books:
            for verse in book["verses"]:
                if verse["system"] != "poetic":
                    continue
                for word in verse["words"]:
                    if "\u05c0" not in (word.get("trailer") or ""):
                        continue
                    rows = word.get("accents") or []
                    if not any(row.get("cp") == "U+05A3" for row in rows):
                        continue
                    found += 1
                    self.assertNotIn("legarmeh", [row["name"] for row in rows], word["id"])
        self.assertGreater(found, 0)

    def test_meteg_on_shewa_is_not_the_tone(self):
        verse = next(item for item in self.books[4]["verses"] if item["ref"] == "Deut.4.19")
        word = next(word for word in verse["words"] if word.get("main_accent") == "telisha_gedola")
        self.assertNotEqual(word["stress"]["letter_index"], 0)
        self.assertNotEqual(word["stress"]["source"], "meteg")

    def test_qere_is_attached_for_the_reader(self):
        verse = next(item for item in self.books[0]["verses"] if item["ref"] == "Gen.8.17")
        ketiv = next(word for word in verse["words"] if word.get("kq_role") == "ketiv")
        self.assertEqual(len(ketiv["qere_words"]), 1)
        self.assertTrue(ketiv["qere_words"][0]["surface"])
        self.assertTrue(ketiv["qere_words"][0].get("accents") or ketiv["qere_words"][0].get("stress"))

    def test_signed_uxlc_review_is_on_the_reading(self):
        verses = {verse["ref"]: verse for book in self.books for verse in book["verses"]}
        deshe = next(word for word in verses["Gen.1.11"]["words"] if word["id"] == "01fPi")
        self.assertEqual(deshe["surface"], "דֶּ֗שֶׁא")
        self.assertEqual(deshe["main_accent"], "revia")
        avi = next(word for word in verses["Isa.9.5"]["words"] if word["consonants"] == "אבי")
        self.assertEqual(avi["trailer"], "")
        self.assertNotIn("אבי ", verses["Isa.9.5"]["text"])
        self.assertIn("ויחראף", [word["consonants"] for word in verses["Num.12.9"]["words"]])
        named = False
        for book in self.books:
            for verse in book["verses"]:
                if verse["system"] == "poetic":
                    continue
                for word in verse["words"]:
                    for row in word.get("accents") or []:
                        if row.get("cp") == "U+05AA":
                            self.assertEqual(row["name"], "galgal", word["id"])
                            self.assertEqual(row["kind"], "C", word["id"])
                            named = True
        self.assertTrue(named)

    def test_normalization_vectors(self):
        vectors = json.loads((ROOT / "tests" / "normalization-vectors.json").read_text(encoding="utf-8"))
        for row in vectors:
            text = "".join(chr(cp) for cp in row["cps"])
            self.assertEqual(canon(canon(text)), canon(text), row["name"])
            self.assertEqual(multiset(canon(text)), multiset(text), row["name"])


if __name__ == "__main__":
    unittest.main()
