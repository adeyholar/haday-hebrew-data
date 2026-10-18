"""Cross-check OSHB words against the pinned UXLC. OSHB is not overwritten."""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from builder.books import BOOKS
from builder.canon import MAQAF, PASEQ, SOF, canon, consonants

TRAIL = (MAQAF, PASEQ, SOF, " ")


def _split_trailer(text: str) -> tuple[str, str]:
    trailer = ""
    while text and text[-1] in TRAIL:
        trailer = text[-1] + trailer
        text = text[:-1]
    return text, trailer


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_uxlc(zip_path: Path) -> dict[str, dict[str, list[dict]]]:
    books: dict[str, dict[str, list[dict]]] = {}
    with zipfile.ZipFile(zip_path) as zipped:
        for osis, _en, _he, _section, filename, _system in BOOKS:
            root = ET.fromstring(zipped.read(f"Books/{filename}"))
            verses: dict[str, list[dict]] = {}
            chapter = 0
            for el in root.iter():
                tag = _local(el.tag)
                if tag == "c":
                    chapter = int(el.get("n") or "0")
                elif tag == "v":
                    verse = int(el.get("n") or "0")
                    ref = f"{osis}.{chapter}.{verse}"
                    words = []
                    for child in list(el):
                        kind = _local(child.tag)
                        if kind not in ("w", "k", "q"):
                            continue
                        raw = "".join(child.itertext())
                        body, _trailer = _split_trailer(raw.strip())
                        words.append({"role": "qere" if kind == "q" else "ketiv" if kind == "k" else "main", "text": body})
                    verses[ref] = words
            books[osis] = verses
    return books


def compare(oshb_books: list[dict], uxlc: dict[str, dict[str, list[dict]]]) -> list[dict]:
    diffs: list[dict] = []
    for book in oshb_books:
        theirs = uxlc.get(book["osis"], {})
        for verse in book["verses"]:
            ref = verse["ref"]
            if ref not in theirs:
                verse["uxlc_status"] = "diff"
                diffs.append({"ref": ref, "word_id": "", "oshb": "", "uxlc": "", "diff_type": "tokenization", "codepoints": ["missing-verse"]})
                continue
            ours = [word for word in verse["words"] if word.get("kq_role") != "qere"]
            theirs_main = [word for word in theirs[ref] if word["role"] != "qere"]
            if len(ours) != len(theirs_main) or [word["consonants"] for word in ours] != [consonants(word["text"]) for word in theirs_main]:
                verse["uxlc_status"] = "diff"
                diffs.append(
                    {
                        "ref": ref,
                        "word_id": "",
                        "oshb": " ".join(word["consonants"] for word in ours),
                        "uxlc": " ".join(consonants(word["text"]) for word in theirs_main),
                        "diff_type": "tokenization",
                        "codepoints": [len(ours), len(theirs_main)],
                    }
                )
                for word in ours:
                    word["uxlc"] = "unaligned"
                continue
            verse_diff = False
            for ours_word, their_word in zip(ours, theirs_main):
                left = canon(ours_word["surface_src"])
                right = canon(their_word["text"])
                if left == right:
                    ours_word["uxlc"] = "match"
                    continue
                verse_diff = True
                ours_word["uxlc"] = "diff"
                kind = "letters" if ours_word["consonants"] != consonants(their_word["text"]) else "marks"
                diffs.append(
                    {
                        "ref": ref,
                        "word_id": ours_word["id"],
                        "oshb": ours_word["surface_src"],
                        "uxlc": their_word["text"],
                        "diff_type": kind,
                        "codepoints": [left, right],
                    }
                )
            verse["uxlc_status"] = "diff" if verse_diff else "match"
    return diffs
