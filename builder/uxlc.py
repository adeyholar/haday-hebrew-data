"""Cross-check OSHB words against the pinned UXLC. OSHB is not overwritten."""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from builder.books import BOOKS
from builder.canon import MAQAF, PASEQ, SOF, canon, consonants

TRAIL = (MAQAF, PASEQ, SOF, " ")
CGJ = "\u034F"
PASHTA = "\u0599"
QADMA = "\u05A8"


def _split_trailer(text: str) -> tuple[str, str]:
    trailer = ""
    while text and text[-1] in TRAIL:
        trailer = text[-1] + trailer
        text = text[:-1]
    return text, trailer


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _plain(el: ET.Element) -> str:
    """Word text without UXLC <x> note markers. Those markers are Latin letters, not Hebrew."""
    parts: list[str] = []
    if el.text:
        parts.append(el.text)
    for child in list(el):
        if _local(child.tag) == "x":
            if child.tail:
                parts.append(child.tail)
            continue
        parts.append(_plain(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def compare_form(text: str) -> str:
    """Comparison only. Does not change the stored OSHB word.

    UXLC inserts CGJ. OSHB writes a doubled pashta as qadma + pashta; UXLC writes two pashtas.
    """
    text = text.replace(CGJ, "").replace("\u200d", "").replace("\u200c", "")
    if PASHTA in text and QADMA in text:
        text = text.replace(QADMA, PASHTA)
    return canon(text)


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
                        raw = _plain(child)
                        body, _trailer = _split_trailer(raw.strip())
                        role = "qere" if kind == "q" else "ketiv" if kind == "k" else "main"
                        words.append({"role": role, "text": body})
                    verses[ref] = words
            books[osis] = verses
    return books


def _pair(ref: str, ours: list[dict], theirs: list[dict], label: str) -> tuple[list[dict], bool]:
    diffs: list[dict] = []
    if len(ours) != len(theirs):
        diffs.append(
            {
                "ref": ref,
                "word_id": "",
                "oshb": " ".join(word["consonants"] for word in ours),
                "uxlc": " ".join(consonants(word["text"]) for word in theirs),
                "diff_type": "tokenization",
                "codepoints": [f"{label}:{len(ours)}", f"{label}:{len(theirs)}"],
            }
        )
        for word in ours:
            word["uxlc"] = "unaligned"
        return diffs, True
    verse_diff = False
    for ours_word, their_word in zip(ours, theirs):
        left_letters = ours_word["consonants"]
        right_letters = consonants(their_word["text"])
        left = compare_form(ours_word["surface_src"])
        right = compare_form(their_word["text"])
        if left == right and left_letters == right_letters:
            ours_word["uxlc"] = "match"
            continue
        verse_diff = True
        ours_word["uxlc"] = "diff"
        kind = "letters" if left_letters != right_letters else "marks"
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
    return diffs, verse_diff


def compare(oshb_books: list[dict], uxlc: dict[str, dict[str, list[dict]]]) -> list[dict]:
    diffs: list[dict] = []
    seen: set[str] = set()
    for book in oshb_books:
        theirs = uxlc.get(book["osis"], {})
        for verse in book["verses"]:
            ref = verse["ref"]
            seen.add(ref)
            if ref not in theirs:
                verse["uxlc_status"] = "diff"
                diffs.append({"ref": ref, "word_id": "", "oshb": "", "uxlc": "", "diff_type": "missing-in-uxlc", "codepoints": ["missing-verse"]})
                continue
            ours = [word for word in verse["words"] if word.get("kq_role") != "qere"]
            ours_q = [word for word in verse["words"] if word.get("kq_role") == "qere"]
            theirs_main = [word for word in theirs[ref] if word["role"] != "qere"]
            theirs_q = [word for word in theirs[ref] if word["role"] == "qere"]
            main_diffs, main_bad = _pair(ref, ours, theirs_main, "main")
            qere_diffs, qere_bad = _pair(ref, ours_q, theirs_q, "qere")
            diffs.extend(main_diffs)
            diffs.extend(qere_diffs)
            verse["uxlc_status"] = "diff" if main_bad or qere_bad else "match"
        for ref in theirs:
            if ref not in seen and ref.startswith(book["osis"] + "."):
                diffs.append({"ref": ref, "word_id": "", "oshb": "", "uxlc": "", "diff_type": "missing-in-oshb", "codepoints": ["extra-verse"]})
                seen.add(ref)
    return diffs
