"""Read the pinned OSHB OSIS files into verses and words."""

import xml.etree.ElementTree as ET
from pathlib import Path

from builder.accents import HEBREW, classify_word
from builder.books import BOOKS, verse_system
from builder.canon import MAQAF, PASEQ, SOF, canon, consonants, multiset, pointed
from builder.rhythm import build_tree, division_paths, poetic_paths
from builder.stress import stress_for

NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
PASEQ_TRAILER = f" {PASEQ} "


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _word_from(el: ET.Element) -> dict:
    raw = "".join(el.itertext())
    parts = raw.split("/")
    surface_src = raw.replace("/", "")
    surface = canon(surface_src)
    special: list[str] = []
    for child in list(el):
        if _local(child.tag) != "seg":
            continue
        kind = child.get("type") or ""
        if kind == "x-large":
            special.append("large")
        elif kind == "x-small":
            special.append("small")
        elif kind == "x-suspended":
            special.append("suspended")
    if "\u05C4" in surface_src:
        special.append("upper_dot")
    if "\u05C5" in surface_src:
        special.append("lower_dot")
    return {
        "id": el.get("id") or "",
        "surface_src": surface_src,
        "surface": surface,
        "morphemes": parts,
        "trailers": [],
        "trailer": "",
        "consonants": consonants(surface),
        "pointed": pointed(surface),
        "lemma": el.get("lemma") or "",
        "morph_oshb": el.get("morph") or "",
        "oshb_n": el.get("n") or "",
        "kq_role": None,
        "kq_group": None,
        "special": special,
        "pos": 0,
        "qere_words": [],
        "alternatives": [],
    }


def _append_trailer(word: dict, trailer: str) -> None:
    word["trailers"].append(trailer)
    word["trailer"] = "".join(word["trailers"])


def _apply_seg(word: dict, kind: str) -> str | None:
    """Attach a separator. Returns a paragraph mark, or None."""
    if kind == "x-maqqef":
        _append_trailer(word, MAQAF)
    elif kind == "x-paseq":
        piece = PASEQ_TRAILER
        if word["trailer"].endswith(" "):
            piece = f"{PASEQ} "
        _append_trailer(word, piece)
    elif kind == "x-sof-pasuq":
        _append_trailer(word, SOF)
    elif kind == "x-reversednun":
        word["special"].append("reversed_nun_after")
    elif kind == "x-pe":
        return "pe"
    elif kind == "x-samekh":
        return "samekh"
    return None


def _words_in(container: ET.Element) -> list[dict]:
    """Qere (or other reading) words, keeping maqaf and paseq that sit between them."""
    words: list[dict] = []
    for child in list(container):
        tag = _local(child.tag)
        if tag == "w":
            word = _word_from(child)
            word["kq_role"] = "qere"
            words.append(word)
            tail = child.tail or ""
            if tail and tail.strip() == "":
                _append_trailer(word, " ")
        elif tag == "seg" and words:
            _apply_seg(words[-1], child.get("type") or "")
        elif tag == "rdg":
            words.extend(_words_in(child))
    return words


def _rdg_text(note: ET.Element) -> str:
    parts: list[str] = []
    for el in note.iter(f"{NS}rdg"):
        parts.append("".join(el.itertext()).strip())
    return " ".join(part for part in parts if part)


def _blank(word: dict) -> None:
    word.setdefault("accents", [])
    word.setdefault("meteg", [])
    word.setdefault("main_accent", None)
    word.setdefault("level", None)
    word.setdefault("unknown_accents", [])
    word.setdefault("stress", None)
    word.setdefault("unit", None)
    word.setdefault("rhythm_path", None)
    word.setdefault("rhythm_path_computed", None)
    word.setdefault("rhythm_match", None)
    word.setdefault("silluq_inferred", False)


def parse_book(path: Path, osis: str) -> list[dict]:
    root = ET.parse(path).getroot()
    verses: list[dict] = []
    for chapter_el in root.iter(f"{NS}chapter"):
        chapter = int(str(chapter_el.get("osisID", "0")).rsplit(".", 1)[-1])
        for verse_el in chapter_el.findall(f"{NS}verse"):
            ref = verse_el.get("osisID") or ""
            verse_no = int(ref.rsplit(".", 1)[-1])
            system = verse_system(osis, chapter, verse_no)
            main: list[dict] = []
            stream: list[dict] = []
            attached: dict[str, list[dict]] = {}
            para = None
            has_sof = False
            open_ketiv: dict | None = None
            verse_alts: list[dict] = []
            for child in list(verse_el):
                tag = _local(child.tag)
                if tag == "w":
                    word = _word_from(child)
                    word["pos"] = len(main) + 1
                    if child.get("type") == "x-ketiv":
                        word["kq_role"] = "ketiv"
                        word["kq_group"] = f"{ref}:{word['id']}"
                        open_ketiv = word
                    main.append(word)
                    stream.append(word)
                elif tag == "seg":
                    kind = child.get("type") or ""
                    if kind == "x-sof-pasuq":
                        has_sof = True
                    # Verse separators belong to the written word. Qere-internal
                    # separators are handled inside the note, not here.
                    if main and kind in ("x-maqqef", "x-paseq", "x-sof-pasuq", "x-reversednun", "x-pe", "x-samekh"):
                        mark = _apply_seg(main[-1], kind)
                        if mark:
                            para = mark
                elif tag == "note" and child.get("type") == "variant":
                    qere = _words_in(child)
                    host = open_ketiv if open_ketiv is not None else (main[-1] if main else None)
                    if qere and host is not None:
                        group = host["kq_group"] or f"{ref}:qere:{qere[0]['id']}"
                        host["qere_words"] = qere
                        for item in qere:
                            item["pos"] = host["pos"]
                            item["kq_group"] = group if host.get("kq_role") == "ketiv" else f"{ref}:qere:{item['id']}"
                            item["ref"] = ref
                        if host.get("kq_role") == "ketiv" and stream and stream[-1] is host:
                            stream.pop()
                            stream.extend(qere)
                        else:
                            index = stream.index(host)
                            stream[index + 1 : index + 1] = qere
                        attached[host["id"]] = qere
                    open_ketiv = None
                elif tag == "note" and child.get("type") in ("alternative", "exegesis"):
                    alt = {"note_type": child.get("type"), "rdg": _rdg_text(child)}
                    if main:
                        main[-1]["alternatives"].append(alt)
                    else:
                        verse_alts.append(alt)
                    note_text = "".join(child.itertext())
                    if child.get("type") == "exegesis" and "divided for exegesis" in note_text and len(main) >= 2 and not main[-2]["trailers"]:
                        main[-2]["_join_next"] = True
            if verse_alts and main:
                main[0]["alternatives"] = verse_alts + main[0]["alternatives"]
                verse_alts = []
            for index, word in enumerate(main):
                if not word["trailers"] and index < len(main) - 1 and not word.get("_join_next"):
                    _append_trailer(word, " ")
                word["trailer"] = "".join(word["trailers"])
            for word in stream:
                word["trailer"] = "".join(word["trailers"])
            for word in main:
                if word.get("kq_role") == "ketiv" and word.get("qere_words") and MAQAF in word["trailer"]:
                    word["qere_words"][-1]["_reading_maqaf"] = True
            for word in main:
                _blank(word)
            _analyze(stream, system, has_sof)
            words: list[dict] = []
            for word in main:
                word["ref"] = ref
                words.append(word)
                words.extend(attached.get(word["id"], []))
            text_src = "".join(word["surface_src"] + word["trailer"] for word in main)
            text = "".join(word["surface"] + word["trailer"] for word in main)
            if has_sof and not text_src.endswith(SOF):
                text_src += SOF
                text += SOF
            units = _units(stream, system)
            verses.append(
                {
                    "ref": ref,
                    "book": osis,
                    "chapter": chapter,
                    "verse": verse_no,
                    "system": system,
                    "text_src": text_src,
                    "text": text,
                    "word_count": len(main),
                    "unit_count": len(units),
                    "para_after": para,
                    "has_sof_pasuq": 1 if has_sof else 0,
                    "rhythm": build_tree(units),
                    "words": words,
                    "verse_alts": verse_alts,
                    "uxlc_status": "unaligned",
                }
            )
    return verses


def _units(reading: list[dict], system: str = "prose") -> list[dict]:
    units: list[dict] = []
    bucket: list[dict] = []
    for word in reading:
        bucket.append(word)
        if MAQAF not in word["trailer"] and not word.get("_reading_maqaf"):
            _close_unit(units, bucket)
            bucket = []
    if bucket:
        _close_unit(units, bucket)
    _poetic_pairs(units)
    paths = poetic_paths(units) if system == "poetic" else division_paths(units)
    for unit in units:
        computed = paths.get(unit["unit"])
        governor = unit["words"][-1]
        oshb = governor.get("oshb_n") or ""
        for word in unit["words"]:
            word["rhythm_path_computed"] = computed if word is governor else None
            if word is governor and oshb:
                word["rhythm_path"] = oshb
                word["rhythm_match"] = oshb == (computed or "")
            elif word is governor:
                word["rhythm_path"] = computed
                word["rhythm_match"] = computed is None
            else:
                word["rhythm_path"] = None
                word["rhythm_match"] = None
            if MAQAF in word["trailer"]:
                word["main_accent"] = None
                word["stress"] = None
    return units


def _close_unit(units: list[dict], bucket: list[dict]) -> None:
    last = bucket[-1]
    units.append(
        {
            "unit": len(units) + 1,
            "level": last.get("level"),
            "accent": last.get("main_accent"),
            "words": bucket,
        }
    )
    number = len(units)
    for item in bucket:
        item["unit"] = number


def _poetic_pairs(units: list[dict]) -> None:
    for index, unit in enumerate(units):
        accents = unit["words"][-1].get("accents") or []
        names = {row["name"] for row in accents}
        prev = units[index - 1] if index else None
        prev_names = {row["name"] for row in (prev["words"][-1].get("accents") or [])} if prev else set()
        prev_bare_ole = "ole" in prev_names and "yored" not in prev_names and "ole_veyored" not in prev_names
        if "merkha" in names and prev_bare_ole and "ole_veyored" not in names and unit["accent"] != "ole_veyored":
            unit["accent"] = "ole_veyored"
            unit["level"] = 0
            unit["words"][-1]["main_accent"] = "ole_veyored"
            unit["words"][-1]["level"] = 0
            if prev is not None:
                prev["level"] = None
                prev["accent"] = "ole"
        if unit["accent"] == "ole_veyored" and prev is not None and prev.get("accent") in ("revia_gadol", "revia"):
            prev["accent"] = "revia_qatan"
            prev["level"] = 2
            prev["words"][-1]["main_accent"] = "revia_qatan"
            prev["words"][-1]["level"] = 2
            for row in prev["words"][-1].get("accents") or []:
                if row.get("role") == "main" and row["name"] in ("revia_gadol", "revia"):
                    row["name"] = "revia_qatan"
                    row["name_he"] = HEBREW["revia_qatan"]
                    row["level"] = 2


def _analyze(reading: list[dict], system: str, has_sof: bool) -> None:
    last_index = len(reading) - 1
    for index, word in enumerate(reading):
        info = classify_word(system, word["surface"], word["trailer"], index == last_index, has_sof)
        word["accents"] = info["accents"]
        word["meteg"] = info["meteg"]
        word["main_accent"] = info["main_accent"]
        word["level"] = info["level"]
        word["unknown_accents"] = info["unknown"]
        word["silluq_inferred"] = info["silluq_inferred"]
        proclitic = MAQAF in word["trailer"] or bool(word.get("_reading_maqaf"))
        word["stress"] = stress_for(word["surface"], word["accents"], word["meteg"], proclitic)
        if word.get("override"):
            if canon(word["surface"]) != word["surface"]:
                raise SystemExit(f"canon not stable {word['id']}")
        else:
            if multiset(word["surface"]) != multiset(word["surface_src"]):
                raise SystemExit(f"mark mismatch {word['id']}")
            if canon(word["surface"]) != word["surface"]:
                raise SystemExit(f"canon not stable {word['id']}")


def rebuild_verse(verse: dict) -> None:
    """Recompute accents, stress, and the pause tree after a review patch."""
    main = [word for word in verse["words"] if word.get("kq_role") != "qere"]
    for index, word in enumerate(main, start=1):
        word["pos"] = index
        for qere in word.get("qere_words") or []:
            qere["pos"] = index
    stream: list[dict] = []
    for word in main:
        if word.get("kq_role") == "ketiv" and word.get("qere_words"):
            stream.extend(word["qere_words"])
        else:
            stream.append(word)
    has_sof = bool(verse["has_sof_pasuq"])
    for word in stream:
        word["surface"] = canon(word["surface"])
        word["consonants"] = consonants(word["surface"])
        word["pointed"] = pointed(word["surface"])
        _blank(word)
    _analyze(stream, verse["system"], has_sof)
    for word in main:
        if word in stream or not word.get("override"):
            continue
        word["surface"] = canon(word["surface"])
        word["consonants"] = consonants(word["surface"])
        word["pointed"] = pointed(word["surface"])
        _blank(word)
        info = classify_word(verse["system"], word["surface"], word["trailer"], word is main[-1], has_sof)
        word["accents"] = info["accents"]
        word["meteg"] = info["meteg"]
        word["main_accent"] = info["main_accent"]
        word["level"] = info["level"]
        word["unknown_accents"] = info["unknown"]
        word["silluq_inferred"] = info["silluq_inferred"]
        word["stress"] = stress_for(word["surface"], word["accents"], word["meteg"], MAQAF in word["trailer"])
    verse["text_src"] = "".join(word["surface_src"] + word["trailer"] for word in main)
    verse["text"] = "".join(word["surface"] + word["trailer"] for word in main)
    if has_sof and not verse["text_src"].endswith(SOF):
        verse["text_src"] += SOF
        verse["text"] += SOF
    verse["word_count"] = len(main)
    units = _units(stream, verse["system"])
    verse["unit_count"] = len(units)
    verse["rhythm"] = build_tree(units)
    words: list[dict] = []
    for word in main:
        words.append(word)
        words.extend(word.get("qere_words") or [])
    verse["words"] = words


def load_oshb(root: Path) -> list[dict]:
    books = []
    for osis, _en, _he, _section, _uxlc, _system in BOOKS:
        path = root / f"{osis}.xml"
        books.append({"osis": osis, "verses": parse_book(path, osis)})
    from builder.overrides import apply_review

    apply_review(books, root.parent / "uxlc-triage-v1.1.1.csv", root.parent / "Tanach.xml.zip")
    return books
