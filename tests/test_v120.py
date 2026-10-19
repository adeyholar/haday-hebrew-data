"""v1.2.0: postpositive-single stress, one pashta convention, morphology of split and merged words."""

import unittest

from corpus import books

PASHTA = "\u0599"
QADMA = "\u05a8"
CORRECTED_DOUBLE = ("034Jz", "09PN4", "10RES", "11RxS", "24CPS", "24A7r", "25K9E", "14T3b")


class V120(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.words = {}
        for book in books():
            for verse in book["verses"]:
                for word in verse["words"]:
                    cls.words[word["id"]] = (verse["ref"], word)

    def test_single_pashta_is_final_by_rule(self):
        sources = {}
        for _ref, word in self.words.values():
            stress = word.get("stress") or {}
            sources[stress.get("source")] = sources.get(stress.get("source"), 0) + 1
            if stress.get("source") == "default-ultima":
                self.assertNotEqual(word.get("main_accent"), "pashta", word["id"])
            if stress.get("source") == "postpositive-single":
                self.assertEqual(word["main_accent"], "pashta", word["id"])
                self.assertEqual(stress["syll_from_end"], 1, word["id"])
        self.assertEqual(sources["postpositive-single"], 14473)
        self.assertEqual(sources["default-ultima"], 8820)

    def test_one_pashta_convention(self):
        for _ref, word in self.words.values():
            self.assertLess(word["surface"].count(PASHTA), 2, word["id"])
        for wid in CORRECTED_DOUBLE:
            _ref, word = self.words[wid]
            self.assertEqual(word.get("review_class"), "wlc_error", wid)
            self.assertIn(QADMA, word["surface"], wid)
            self.assertEqual(word["stress"]["source"], "doubled", wid)
            self.assertEqual(word["main_accent"], "pashta", wid)

    def test_split_and_merged_words_keep_morphology(self):
        for wid in ("01h5C", "01h5Cb", "10wPX", "10wPXb"):
            _ref, word = self.words[wid]
            self.assertTrue(word["lemma"] and word["morph_oshb"], wid)
            self.assertIn("split from", word["morph_note"])
        self.assertEqual(self.words["01h5Cb"][1]["lemma"], "3540")
        _ref, num = self.words["04xji"]
        self.assertEqual((num["lemma"], num["morph_oshb"]), ("c/2734/639", "HC/Vqw3ms/Ta"))
        self.assertIn("merged 04xji+04AfZ", num["morph_note"])
        merged = [word for _ref, word in self.words.values() if (word.get("morph_note") or "").startswith("merged")]
        self.assertEqual(len(merged), 8)
        for word in merged:
            self.assertEqual(word["lemma"].count("/") + 1, len(word["morph_oshb"].split("/")), word["id"])


if __name__ == "__main__":
    unittest.main()
