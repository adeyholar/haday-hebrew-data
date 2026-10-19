"""Apply the signed UXLC triage. OSHB stays in surface_src. The reading is surface.

The triage is layered by class (Re-review 6):

- WLC 4.20 transcription errors (UXLC corrected against L): applied to surface by default.
- Real unresolved cases (L uncertain, UXLC note t): never on surface. Stored as an
  alternative with note_type "uxlc_uncertain" and uncertain = true.
- Optional diplomatic rows (UXLC notes c/d/m): never on surface. Stored as an opt-in
  alternative with note_type "uxlc_diplomatic".
- Word division and exegesis joins: applied, except a division UXLC itself marks uncertain.

A row marked none or document is not changed. A comparison-only row is not changed.
Every changed word carries review_class. text_src is never touched: it stays OSHB.
The patch file is sources/<TRIAGE_FILE from PINS.txt>. Its `decision` column is the only policy input;
`apply_uxlc_marks` (yes or empty, join rows only) says a join also takes UXLC's signed mark correction.
The class column only names `review_class`; recommended_action and verdict are prose for people.
An unknown decision or apply_uxlc_marks value stops the build.
"""

import csv
from pathlib import Path

from builder.canon import canon, clusters, consonants, pointed
from builder.errors import TriageError
from builder.oshb import rebuild_verse
from builder.pins import uxlc_zip
from builder.uxlc import load_uxlc

CGJ = "\u034f"


WLC_ERROR = "WLC 4.20 transcription error inherited by OSHB (UXLC corrected against L)"
UNCERTAIN = "Real unresolved case (L uncertain)"
EDITORIAL = "Known WLC/UXLC editorial difference"

CLASS_KEY = {
    WLC_ERROR: "wlc_error",
    UNCERTAIN: "l_uncertain",
    EDITORIAL: "editorial",
    "UXLC encoding convention": "uxlc_convention",
    "OSHB encoding convention (no textual difference)": "oshb_convention",
}


DECISIONS = ("override", "uncertain", "optional", "divide", "join", "compare", "leave")


def row_decision(row: dict) -> str:
    """What the builder does with one triage row. Read from the explicit `decision` column only.

    override  -> paint UXLC onto surface (WLC errors)
    uncertain -> alternative, flagged uncertain, never on surface
    optional  -> opt-in alternative, never on surface
    divide    -> word division per UXLC (L)
    join      -> exegesis split written with no space
    compare   -> comparison only
    leave     -> nothing
    """
    value = (row.get("decision") or "").strip()
    if value not in DECISIONS:
        raise TriageError(f"unknown triage decision {value!r} at {row.get('ref')} {row.get('word_id')}")
    return value


def paints_marks(row: dict) -> bool:
    """A join row that also carries a signed UXLC mark correction (column apply_uxlc_marks = yes)."""
    value = (row.get("apply_uxlc_marks") or "").strip()
    if value not in ("", "yes"):
        raise TriageError(f"apply_uxlc_marks must be yes or empty at {row.get('ref')}: {value!r}")
    if value and row_decision(row) != "join":
        raise TriageError(f"apply_uxlc_marks is only for join rows at {row.get('ref')}")
    return value == "yes"


def class_key(row: dict) -> str:
    return CLASS_KEY.get(row.get("class") or "", "other")


def _cut_parts(parts: list[str], cut: int) -> tuple[list[str], list[str]]:
    """Split morpheme strings after `cut` letters."""
    left: list[str] = []
    right: list[str] = []
    seen = 0
    for part in parts:
        groups = clusters(part)
        if seen >= cut:
            right.append(part)
        elif seen + len(groups) <= cut:
            left.append(part)
        else:
            k = cut - seen
            left.append(_join_clusters(groups[:k]))
            right.append(_join_clusters(groups[k:]))
        seen += len(groups)
    return [p for p in left if p], [p for p in right if p]


def resegment(word: dict) -> None:
    """Morphemes follow the final surface, cut where the OSHB morphemes were cut."""
    parts = word.get("morphemes_src") or word.get("morphemes") or [word["surface_src"]]
    sizes = [len(clusters(part)) for part in parts]
    groups = clusters(word["surface"])
    if sum(sizes) != len(groups):
        # Reported in build-report/summary.json as morpheme_fallbacks.
        word["morphemes"] = [word["surface"]]
        word["morpheme_fallback"] = len(parts) > 1
        return
    out: list[str] = []
    at = 0
    for size in sizes:
        out.append(_join_clusters(groups[at : at + size]))
        at += size
    word["morphemes"] = out


def _strip(text: str) -> str:
    return text.replace(CGJ, "").replace("\u200d", "").replace("\u200c", "").replace("/", "")


def _join_clusters(parts: list[tuple[str, list[str]]]) -> str:
    return "".join(letter + "".join(marks) for letter, marks in parts)


def _paint(word: dict, text: str, row: dict) -> None:
    word.setdefault("morphemes_src", list(word.get("morphemes") or []))
    word["surface"] = canon(_strip(text))
    word["consonants"] = consonants(word["surface"])
    word["pointed"] = pointed(word["surface"])
    word["override"] = {
        "action": row_decision(row),
        "note": row.get("uxlc_notes") or "",
        "verdict": row.get("verdict") or "",
    }
    word["review_class"] = class_key(row)


def _alternative(word: dict, row: dict, how: str) -> None:
    alt = {
        "note_type": "uxlc_uncertain" if how == "uncertain" else "uxlc_diplomatic",
        "rdg": canon(_strip(row["uxlc"])),
        "review_class": class_key(row),
        "uncertain": how == "uncertain",
        "opt_in": True,
        "uxlc_note": row.get("uxlc_notes") or "",
    }
    word.setdefault("alternatives", []).append(alt)


def _main(verse: dict) -> list[dict]:
    return [word for word in verse["words"] if word.get("kq_role") != "qere"]


def _align(words: list[dict], theirs: list[dict]) -> list[tuple] | None:
    i = 0
    j = 0
    ops: list[tuple] = []
    while i < len(words) or j < len(theirs):
        if i < len(words) and j < len(theirs) and words[i]["consonants"] == consonants(theirs[j]["text"]):
            ops.append(("keep", i, j))
            i += 1
            j += 1
        elif (
            i + 1 < len(words)
            and j < len(theirs)
            and words[i]["consonants"] + words[i + 1]["consonants"] == consonants(theirs[j]["text"])
        ):
            ops.append(("merge", i, j))
            i += 2
            j += 1
        elif (
            i < len(words)
            and j + 1 < len(theirs)
            and words[i]["consonants"] == consonants(theirs[j]["text"]) + consonants(theirs[j + 1]["text"])
        ):
            ops.append(("split", i, j))
            i += 1
            j += 2
        else:
            return None
    return ops


def _merge(a: dict, b: dict, text: str, row: dict) -> dict:
    word = {
        "id": a["id"],
        "surface_src": a["surface_src"] + b["surface_src"],
        "surface": canon(_strip(text)),
        "morphemes": list(a.get("morphemes") or []) + list(b.get("morphemes") or []),
        "trailers": list(b.get("trailers") or []),
        "trailer": b.get("trailer") or "",
        "consonants": "",
        "pointed": "",
        "lemma": a.get("lemma") or b.get("lemma") or "",
        "morph_oshb": a.get("morph_oshb") or "",
        "oshb_n": b.get("oshb_n") or a.get("oshb_n") or "",
        "kq_role": a.get("kq_role"),
        "kq_group": a.get("kq_group"),
        "special": list(a.get("special") or []) + list(b.get("special") or []),
        "pos": a.get("pos") or 0,
        "qere_words": list(a.get("qere_words") or []) + list(b.get("qere_words") or []),
        "alternatives": list(a.get("alternatives") or []) + list(b.get("alternatives") or []),
        "override": {
            "action": "divide",
            "note": row.get("uxlc_notes") or "",
            "verdict": row.get("verdict") or "",
            "ids": [a["id"], b["id"]],
        },
        "review_class": "word_division",
    }
    word["morphemes_src"] = list(a.get("morphemes_src") or a.get("morphemes") or []) + list(b.get("morphemes_src") or b.get("morphemes") or [])
    word["consonants"] = consonants(word["surface"])
    word["pointed"] = pointed(word["surface"])
    for qere in word["qere_words"]:
        qere["pos"] = word["pos"]
    return word


def _split(word: dict, left: str, right: str, row: dict) -> tuple[dict, dict]:
    parts = clusters(word["surface_src"])
    cut = len(consonants(_strip(left)))
    first = dict(word)
    first["surface_src"] = _join_clusters(parts[:cut])
    first["surface"] = canon(_strip(left))
    first["trailers"] = [" "]
    first["trailer"] = " "
    left_parts, right_parts = _cut_parts(list(word.get("morphemes_src") or word.get("morphemes") or []), cut)
    first["morphemes_src"] = left_parts
    first["morphemes"] = list(left_parts)
    first["review_class"] = "word_division"
    first["special"] = list(word.get("special") or [])
    first["alternatives"] = list(word.get("alternatives") or [])
    first["qere_words"] = list(word.get("qere_words") or [])
    first["oshb_n"] = ""
    first["override"] = {"action": "divide", "note": row.get("uxlc_notes") or "", "verdict": row.get("verdict") or "", "part": 1}
    second = dict(word)
    second["id"] = word["id"] + "b"
    second["surface_src"] = _join_clusters(parts[cut:])
    second["surface"] = canon(_strip(right))
    second["trailers"] = list(word.get("trailers") or [])
    second["trailer"] = word.get("trailer") or ""
    second["morphemes_src"] = right_parts
    second["morphemes"] = list(right_parts)
    second["review_class"] = "word_division"
    second["lemma"] = ""
    second["morph_oshb"] = ""
    second["special"] = []
    second["alternatives"] = []
    second["qere_words"] = []
    second["kq_role"] = word.get("kq_role")
    second["kq_group"] = None
    second["override"] = {"action": "divide", "note": row.get("uxlc_notes") or "", "verdict": row.get("verdict") or "", "part": 2}
    for item in (first, second):
        item["consonants"] = consonants(item["surface"])
        item["pointed"] = pointed(item["surface"])
    return first, second


def _paint_span(words: list[dict], text: str, row: dict) -> None:
    parts = clusters(_strip(text))
    offset = 0
    for word in words:
        count = len(word["consonants"])
        _paint(word, _join_clusters(parts[offset : offset + count]), row)
        offset += count
    if offset != len(parts):
        raise TriageError(f"paint length {words[0]['id']}")


def _reshape(verse: dict, theirs: list[dict], row: dict, how: str) -> None:
    words = _main(verse)
    ops = _align(words, theirs)
    if ops is None:
        raise TriageError(f"cannot align {verse['ref']}")
    if how == "join":
        for op, at, ux in ops:
            if op == "merge":
                if paints_marks(row):
                    _paint_span([words[at], words[at + 1]], theirs[ux]["text"], row)
                for item in (words[at], words[at + 1]):
                    item["review_class"] = item.get("review_class") or "exegesis_join"
        return
    new: list[dict] = []
    for op, at, ux in ops:
        if op == "keep":
            # A word the division row does not cover keeps its own reading. Its UXLC
            # difference (if any) was never triaged, so it stays visible in uxlc-diff.
            new.append(words[at])
        elif op == "merge":
            if words[at].get("kq_role") == "ketiv" or words[at + 1].get("kq_role") == "ketiv":
                raise TriageError(f"ketiv merge {verse['ref']}")
            new.append(_merge(words[at], words[at + 1], theirs[ux]["text"], row))
        else:
            if words[at].get("kq_role") == "ketiv":
                raise TriageError(f"ketiv split {verse['ref']}")
            new.extend(_split(words[at], theirs[ux]["text"], theirs[ux + 1]["text"], row))
    verse["words"] = new


def apply_review(books: list[dict], csv_path: Path, uxlc: "dict | Path | None" = None) -> None:
    """Apply the triage. `uxlc` is the parsed UXLC, or a zip path to parse only if a row needs it."""
    if not csv_path.exists():
        raise TriageError(f"missing triage {csv_path}")
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_id: dict[str, dict] = {}
    by_ref: dict[str, dict] = {}
    for book in books:
        for verse in book["verses"]:
            by_ref[verse["ref"]] = verse
            for word in verse["words"]:
                by_id[word["id"]] = word
    touched: set[str] = set()
    for row in rows:
        how = row_decision(row)
        if how not in ("override", "uncertain", "optional") or not row.get("word_id"):
            continue
        word = by_id.get(row["word_id"])
        if word is None or not row.get("uxlc"):
            raise TriageError(f"override missing word {row['ref']} {row['word_id']}")
        if how == "override":
            _paint(word, row["uxlc"], row)
            touched.add(row["ref"])
        else:
            _alternative(word, row, how)
    divide_rows = [row for row in rows if row_decision(row) in ("divide", "join")]
    if divide_rows:
        if not isinstance(uxlc, dict):
            uxlc = load_uxlc(uxlc or uxlc_zip())
        for row in divide_rows:
            verse = by_ref[row["ref"]]
            osis = row["ref"].split(".")[0]
            theirs = [word for word in uxlc[osis][row["ref"]] if word["role"] != "qere"]
            _reshape(verse, theirs, row, row_decision(row))
            touched.add(row["ref"])
    for ref in touched:
        rebuild_verse(by_ref[ref])
    for ref in touched:
        for word in by_ref[ref]["words"]:
            if word.get("review_class"):
                resegment(word)
            word.pop("morphemes_src", None)
