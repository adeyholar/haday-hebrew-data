"""Re-review 6: the UXLC override layer, morphemes, text_src, and galgal."""

import csv
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from builder.accents import classify_word
from builder.canon import canon, clusters, consonants, multiset
from builder.oshb import NS
from builder.pins import oshb_dir, triage_path
from corpus import books as corpus_books
from builder.overrides import _strip, row_decision
from builder.stress import stress_for

ROOT = Path(__file__).resolve().parents[1]
TRIAGE = triage_path()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def oshb_verse_texts(path: Path) -> dict[str, str]:
    """Rebuild each verse straight from the OSIS file: words, maqaf, paseq, sof, and the source's own spaces."""
    out: dict[str, str] = {}
    root = ET.parse(path).getroot()
    for verse in root.iter(f"{NS}verse"):
        parts: list[str] = []
        for child in list(verse):
            tag = _local(child.tag)
            if tag == "w":
                parts.append("".join(child.itertext()).replace("/", ""))
            elif tag == "seg" and child.get("type") in ("x-maqqef", "x-paseq", "x-sof-pasuq"):
                parts.append(child.text or "")
            if child.tail:
                parts.append(child.tail)
        out[verse.get("osisID") or ""] = _squeeze("".join(parts))
    return out


def _squeeze(text: str) -> str:
    """One space per gap. A maqaf joins words, so a stray source space next to it (2 Sam 16:23,
    Jer 50:29, Song 6:12, where a note sits beside the maqaf) is not a word boundary."""
    return re.sub(r"\s*\u05be\s*", "\u05be", re.sub(r"\s+", " ", text)).strip()


class ReviewPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.books = corpus_books()
        cls.verses = {verse["ref"]: verse for book in cls.books for verse in book["verses"]}
        cls.words = {word["id"]: word for verse in cls.verses.values() for word in verse["words"]}
        with TRIAGE.open(encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_override_class_policy(self):
        counts = {"override": 0, "uncertain": 0, "optional": 0}
        for row in self.rows:
            how = row_decision(row)
            if how not in counts or not row["word_id"]:
                continue
            counts[how] += 1
            word = self.words[row["word_id"]]
            uxlc = canon(_strip(row["uxlc"]))
            if how == "override":
                self.assertEqual(word["surface"], uxlc, row["ref"])
                self.assertEqual(word["review_class"], "wlc_error", row["ref"])
                continue
            # Uncertain and optional rows never reach the main text.
            self.assertEqual(multiset(word["surface"]), multiset(word["surface_src"]), row["ref"])
            self.assertNotIn("review_class", word, row["ref"])
            note = "uxlc_uncertain" if how == "uncertain" else "uxlc_diplomatic"
            alts = [alt for alt in word["alternatives"] if alt["note_type"] == note]
            self.assertEqual(len(alts), 1, row["ref"])
            self.assertEqual(alts[0]["rdg"], uxlc)
            self.assertEqual(alts[0]["uncertain"], how == "uncertain")
            self.assertTrue(alts[0]["opt_in"])
        self.assertEqual(counts, {"override": 567, "uncertain": 146, "optional": 98})
        classes = {word.get("review_class") for word in self.words.values()}
        self.assertNotIn("l_uncertain", classes)
        self.assertNotIn("editorial", classes)

    def test_dechi_and_revia_cases(self):
        qoli = next(word for word in self.verses["Ps.3.5"]["words"] if word["id"] == "19YHH")
        self.assertEqual(qoli["surface"], "ק֭וֹלִי")
        self.assertEqual(qoli["main_accent"], "dechi")
        self.assertEqual(qoli["rhythm_path_computed"], "1.0")
        deshe = next(word for word in self.verses["Gen.1.11"]["words"] if word["id"] == "01fPi")
        self.assertEqual(deshe["main_accent"], "revia")
        self.assertEqual(deshe["review_class"], "wlc_error")

    def test_morphemes_follow_surface(self):
        for word in self.words.values():
            joined = "".join(word["morphemes"])
            self.assertEqual(multiset(joined), multiset(word["surface"]), word["id"])
            self.assertEqual(consonants(joined), word["consonants"], word["id"])
            self.assertFalse(any("/" in part for part in word["morphemes"]), word["id"])
        deshe = self.words["01fPi"]
        self.assertEqual(deshe["morphemes"], [deshe["surface"]])
        self.assertIn("\u0597", deshe["morphemes"][0])

    def test_text_src_is_oshb_byte_for_byte(self):
        checked = 0
        for path in sorted(oshb_dir().glob("*.xml")):
            for ref, text in oshb_verse_texts(path).items():
                self.assertEqual(_squeeze(self.verses[ref]["text_src"]), text, ref)
                checked += 1
        self.assertEqual(checked, 23213)

    # Spaces in the reading for every verse the triage lists under tokenization. The OSHB exegesis
    # splits are joined (no space in the source), the WLC word-division corrections follow L, and
    # the reading never gains a space the source and the review do not give it.
    TOKENIZATION_SPACES = {
        "Gen.14.17": 15, "Num.12.9": 3, "Josh.10.24": 24, "1Sam.17.17": 14, "1Sam.19.23": 14,
        "2Sam.3.30": 12, "2Sam.6.7": 11, "2Sam.8.1": 11, "2Sam.20.8": 21, "2Kgs.6.25": 15,
        "Isa.9.5": 14, "Jer.29.23": 18, "Ps.106.1": 7, "Ps.149.1": 8, "Ps.150.1": 6, "Job.39.30": 5,
        "Song.8.6": 14, "Dan.5.10": 17, "Ezra.3.5": 10, "Ezra.4.11": 11, "1Chr.15.13": 10,
        "1Chr.20.4": 13, "2Chr.20.1": 10, "2Chr.20.35": 9, "2Chr.24.4": 7, "2Chr.30.3": 12,
    }

    def test_the_twelve_spaces_stay_fixed(self):
        for ref, spaces in self.TOKENIZATION_SPACES.items():
            self.assertEqual(self.verses[ref]["text"].count(" "), spaces, ref)
        avi = [word for word in self.verses["Isa.9.5"]["words"] if word["trailer"] == "" and word.get("kq_role") != "qere"]
        self.assertTrue(avi)

    def test_galgal_naming(self):
        seen = {"prose": 0, "poetic": 0}
        for verse in self.verses.values():
            for word in verse["words"]:
                for row in word.get("accents") or []:
                    if row.get("cp") in ("U+05AA", "U+05A2"):
                        self.assertEqual(row["name"], "galgal", word["id"])
                        self.assertEqual(row["kind"], "C", word["id"])
                        seen[verse["system"]] += 1
        self.assertGreaterEqual(seen["prose"], 16)
        self.assertGreater(seen["poetic"], 0)
        for system in ("prose", "poetic"):
            rows = classify_word(system, "הָ֢יָה", " ", False)["accents"]
            self.assertEqual((rows[0]["name"], rows[0]["kind"]), ("galgal", "C"))

    def test_segolate_and_quiescent_aleph_stress(self):
        for system, word, expected in (
            ("poetic", "אֶ֝בֶן", 2),
            ("poetic", "שַּׁ֭חַת", 2),
            ("prose", "פֶּ֠תַח", 2),
            ("poetic", "קֹ֭דֶשׁ", 2),
            ("prose", "לָכֶ֠ם", 1),
            ("poetic", "אַ֭חַת", 1),
            ("poetic", "שָׂ֭דֶה", 1),
            ("prose", "יְר֣אוּ", 1),
            ("prose", "הוֹצִיא֖וּהָ", 2),
        ):
            info = classify_word(system, word, " ", False)
            stress = stress_for(word, info["accents"], info["meteg"], False)
            self.assertEqual(stress["syll_from_end"], expected, word)
        even = next(word for word in self.verses["Prov.26.27"]["words"] if word["consonants"] == "אבן")
        self.assertEqual((even["stress"]["syll_from_end"], even["stress"]["source"]), (2, "segolate"))


if __name__ == "__main__":
    unittest.main()
