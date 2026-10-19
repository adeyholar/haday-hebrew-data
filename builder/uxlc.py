"""Cross-check OSHB words against the pinned UXLC. OSHB is not overwritten."""

import csv
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from builder.books import BOOKS
from builder.canon import ACCENTS, MAQAF, PASEQ, SOF, canon, consonants
from builder.pins import triage_path

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
    # Galgal: OSHB writes U+05AA, UXLC writes U+05A2 (see builder/accents.py). Comparison only.
    text = text.replace("\u05AA", "\u05A2")
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


def _bags(text: str) -> tuple[str, dict[str, int], dict[str, int]]:
    text = compare_form(text).replace("/", "")
    letters = consonants(text)
    accents: dict[str, int] = {}
    other: dict[str, int] = {}
    for ch in text:
        if 0x05D0 <= ord(ch) <= 0x05EA:
            continue
        bag = accents if ord(ch) in ACCENTS else other
        bag[ch] = bag.get(ch, 0) + 1
    return letters, accents, other


def _alt_covers(word: dict, uxlc_text: str) -> bool:
    """UXLC sometimes stacks both accent systems. OSHB keeps the second on word_alt."""
    letters, ux_acc, ux_other = _bags(uxlc_text)
    src_letters, src_acc, src_other = _bags(word.get("surface") or word.get("surface_src") or "")
    if letters != src_letters or ux_other != src_other:
        return False
    have = dict(src_acc)
    for alt in word.get("alternatives") or []:
        if alt.get("note_type") != "alternative":
            continue
        _letters, acc, _other = _bags(alt.get("rdg") or "")
        for ch, n in acc.items():
            have[ch] = have.get(ch, 0) + n
    return have == ux_acc


def _joined(words: list[dict]) -> list[dict]:
    """An exegesis split has an empty trailer. Compare it as the one written word."""
    out: list[dict] = []
    pending: dict | None = None
    for word in words:
        if pending is None:
            pending = word
            continue
        if not pending.get("_join_next"):
            out.append(pending)
            pending = word
            continue
        pending = {
            "id": pending["id"],
            "surface_src": pending["surface_src"] + word["surface_src"],
            "surface": pending["surface"] + word["surface"],
            "consonants": pending["consonants"] + word["consonants"],
            "trailer": word.get("trailer") or "",
            "alternatives": (pending.get("alternatives") or []) + (word.get("alternatives") or []),
        }
    if pending is not None:
        out.append(pending)
    return out


def _pair(ref: str, ours: list[dict], theirs: list[dict], label: str, explained: set[tuple[str, str]]) -> tuple[list[dict], bool]:
    diffs: list[dict] = []
    ours = _joined(ours)
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
            if "uxlc" in word:
                word["uxlc"] = "unaligned"
        return diffs, True
    verse_diff = False
    for ours_word, their_word in zip(ours, theirs):
        left_letters = ours_word["consonants"]
        right_letters = consonants(their_word["text"])
        left = compare_form(ours_word.get("surface") or ours_word.get("surface_src") or "")
        right = compare_form(their_word["text"])
        if (ref, ours_word.get("id") or "") in explained or (left == right and left_letters == right_letters) or _alt_covers(ours_word, their_word["text"]):
            if "id" in ours_word:
                ours_word["uxlc"] = "match"
            continue
        verse_diff = True
        if "id" in ours_word:
            ours_word["uxlc"] = "diff"
        kind = "letters" if left_letters != right_letters else "marks"
        diffs.append(
            {
                "ref": ref,
                "word_id": ours_word.get("id") or "",
                "oshb": ours_word.get("surface") or "",
                "uxlc": their_word["text"],
                "diff_type": kind,
                "codepoints": [left, right],
            }
        )
    return diffs, verse_diff


def _explained(root: Path | None = None) -> set[tuple[str, str]]:
    """Word ids the signed review says are the same mark, or already stored on word_alt."""
    from builder.overrides import row_decision

    path = root or triage_path()
    if not path.exists():
        return set()
    found: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            # compare rows are the same mark; uncertain and optional rows are kept on word_alt.
            if row_decision(row) in ("compare", "uncertain", "optional") and row.get("word_id"):
                found.add((row["ref"], row["word_id"]))
    return found


def compare(oshb_books: list[dict], uxlc: dict[str, dict[str, list[dict]]]) -> list[dict]:
    explained = _explained()
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
            main_diffs, main_bad = _pair(ref, ours, theirs_main, "main", explained)
            qere_diffs, qere_bad = _pair(ref, ours_q, theirs_q, "qere", explained)
            diffs.extend(main_diffs)
            diffs.extend(qere_diffs)
            verse["uxlc_status"] = "diff" if main_bad or qere_bad else "match"
        for ref in theirs:
            if ref not in seen and ref.startswith(book["osis"] + "."):
                diffs.append({"ref": ref, "word_id": "", "oshb": "", "uxlc": "", "diff_type": "missing-in-oshb", "codepoints": ["extra-verse"]})
                seen.add(ref)
    return diffs
