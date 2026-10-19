"""Apply the signed UXLC triage. OSHB stays in surface_src. The reading is surface.

A row marked none or document is not changed. A comparison-only row is not changed.
The patch file is sources/uxlc-triage-v1.1.1.csv.
"""

import csv
from pathlib import Path

from builder.canon import canon, clusters, consonants, pointed
from builder.oshb import rebuild_verse
from builder.uxlc import load_uxlc

CGJ = "\u034f"


def decision(action: str) -> str:
    if action.startswith("normalize"):
        return "compare"
    if "word division" in action:
        return "divide"
    if action.startswith("builder fix"):
        return "join"
    if action.startswith("documented override"):
        return "override"
    return "leave"


def _strip(text: str) -> str:
    return text.replace(CGJ, "").replace("\u200d", "").replace("\u200c", "").replace("/", "")


def _join_clusters(parts: list[tuple[str, list[str]]]) -> str:
    return "".join(letter + "".join(marks) for letter, marks in parts)


def _paint(word: dict, text: str, row: dict) -> None:
    word["surface"] = canon(_strip(text))
    word["consonants"] = consonants(word["surface"])
    word["pointed"] = pointed(word["surface"])
    word["override"] = {
        "action": decision(row["recommended_action"]),
        "note": row.get("uxlc_notes") or "",
        "verdict": row.get("verdict") or "",
    }


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
    }
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
    first["morphemes"] = list(word.get("morphemes") or [])
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
    second["morphemes"] = []
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
        raise SystemExit(f"paint length {words[0]['id']}")


def _reshape(verse: dict, theirs: list[dict], row: dict, how: str) -> None:
    words = _main(verse)
    ops = _align(words, theirs)
    if ops is None:
        raise SystemExit(f"cannot align {verse['ref']}")
    if how == "join":
        if "documented override" in row["recommended_action"]:
            for op, at, ux in ops:
                if op == "merge":
                    _paint_span([words[at], words[at + 1]], theirs[ux]["text"], row)
        return
    new: list[dict] = []
    for op, at, ux in ops:
        if op == "keep":
            if canon(_strip(theirs[ux]["text"])) != words[at]["surface"]:
                _paint(words[at], theirs[ux]["text"], row)
            new.append(words[at])
        elif op == "merge":
            if words[at].get("kq_role") == "ketiv" or words[at + 1].get("kq_role") == "ketiv":
                raise SystemExit(f"ketiv merge {verse['ref']}")
            new.append(_merge(words[at], words[at + 1], theirs[ux]["text"], row))
        else:
            if words[at].get("kq_role") == "ketiv":
                raise SystemExit(f"ketiv split {verse['ref']}")
            new.extend(_split(words[at], theirs[ux]["text"], theirs[ux + 1]["text"], row))
    verse["words"] = new


def apply_review(books: list[dict], csv_path: Path, uxlc_zip: Path) -> None:
    if not csv_path.exists():
        raise SystemExit(f"missing triage {csv_path}")
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
        if decision(row["recommended_action"]) != "override":
            continue
        word = by_id.get(row["word_id"])
        if word is None or not row.get("uxlc"):
            raise SystemExit(f"override missing word {row['ref']} {row['word_id']}")
        _paint(word, row["uxlc"], row)
        touched.add(row["ref"])
    divide_rows = [row for row in rows if decision(row["recommended_action"]) in ("divide", "join")]
    if divide_rows:
        uxlc = load_uxlc(uxlc_zip)
        for row in divide_rows:
            verse = by_ref[row["ref"]]
            osis = row["ref"].split(".")[0]
            theirs = [word for word in uxlc[osis][row["ref"]] if word["role"] != "qere"]
            _reshape(verse, theirs, row, decision(row["recommended_action"]))
            touched.add(row["ref"])
    for ref in touched:
        rebuild_verse(by_ref[ref])
