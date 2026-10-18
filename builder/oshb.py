"""Read the pinned OSHB OSIS files into verses and words."""

import xml.etree.ElementTree as ET
from pathlib import Path

from builder.accents import classify_word
from builder.books import BOOKS, verse_system
from builder.canon import MAQAF, PASEQ, SOF, canon, consonants, multiset, pointed
from builder.rhythm import build_tree, division_paths
from builder.stress import stress_for

NS = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"


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
    }


def _qere_words(note: ET.Element) -> list[dict]:
    found: list[dict] = []
    for el in note.iter(f"{NS}w"):
        parent = None
        word = _word_from(el)
        word["kq_role"] = "qere"
        found.append(word)
        _ = parent
    return found


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
            attached: dict[str, list[dict]] = {}
            para = None
            has_sof = False
            open_ketiv: dict | None = None
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
                elif tag == "seg":
                    kind = child.get("type")
                    if kind == "x-maqqef" and main:
                        main[-1]["trailer"] = MAQAF
                    elif kind == "x-paseq" and main:
                        main[-1]["trailer"] = PASEQ
                    elif kind == "x-sof-pasuq":
                        has_sof = True
                        if main:
                            main[-1]["trailer"] = SOF
                    elif kind == "x-pe":
                        para = "pe"
                    elif kind == "x-samekh":
                        para = "samekh"
                    elif kind == "x-reversednun" and main:
                        main[-1]["special"].append("reversed_nun_after")
                elif tag == "note" and child.get("type") == "variant":
                    qere = _qere_words(child)
                    host = open_ketiv if open_ketiv is not None else (main[-1] if main else None)
                    if qere and host is not None:
                        group = host["kq_group"] or f"{ref}:qere:{qere[0]['id']}"
                        if host.get("kq_role") != "ketiv":
                            host["kq_group"] = None
                        for item in qere:
                            item["pos"] = host["pos"]
                            item["kq_group"] = group if host.get("kq_role") == "ketiv" else f"{ref}:qere:{item['id']}"
                            item["ref"] = ref
                            item["unit"] = None
                            info = classify_word(system, item["surface"], item["trailer"], False)
                            item["accents"] = info["accents"]
                            item["meteg"] = info["meteg"]
                            item["main_accent"] = info["main_accent"]
                            item["level"] = info["level"]
                            item["unknown_accents"] = info["unknown"]
                            item["stress"] = stress_for(item["surface"], item["accents"], item["meteg"], False)
                            item["rhythm_path"] = None
                            item["rhythm_path_computed"] = None
                            item["rhythm_match"] = None
                        attached.setdefault(host["id"], []).extend(qere)
                    open_ketiv = None
            for index, word in enumerate(main):
                if word["trailer"] == "" and index < len(main) - 1:
                    word["trailer"] = " "
            _analyze(main, system)
            words: list[dict] = []
            for word in main:
                word["ref"] = ref
                words.append(word)
                words.extend(attached.get(word["id"], []))
            text_src = "".join(word["surface_src"] + word["trailer"] for word in main)
            text = "".join(word["surface"] + word["trailer"] for word in main)
            units = _units(main)
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
                    "uxlc_status": "unaligned",
                }
            )
    return verses


def _units(main: list[dict]) -> list[dict]:
    units: list[dict] = []
    bucket: list[dict] = []
    for word in main:
        bucket.append(word)
        if word["trailer"] != MAQAF:
            last = bucket[-1]
            units.append(
                {
                    "unit": len(units) + 1,
                    "level": last.get("level"),
                    "accent": last.get("main_accent"),
                    "words": bucket,
                }
            )
            for item in bucket:
                item["unit"] = len(units)
            bucket = []
    if bucket:
        last = bucket[-1]
        units.append({"unit": len(units) + 1, "level": last.get("level"), "accent": last.get("main_accent"), "words": bucket})
        for item in bucket:
            item["unit"] = len(units)
    _poetic_pairs(units)
    paths = division_paths(units)
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
            if word["trailer"] == MAQAF:
                word["main_accent"] = None
                word["stress"] = None
    return units


def _poetic_pairs(units: list[dict]) -> None:
    for index, unit in enumerate(units):
        accents = unit["words"][-1].get("accents") or []
        names = {row["name"] for row in accents}
        prev = units[index - 1] if index else None
        prev_names = {row["name"] for row in (prev["words"][-1].get("accents") or [])} if prev else set()
        if "merkha" in names and "ole" in prev_names and "ole_veyored" not in names:
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


def _analyze(main: list[dict], system: str) -> None:
    # Units are not known until trailers are set. Last unit is the last word that does not continue a maqaf, which is the last word.
    last_index = len(main) - 1
    # A maqaf chain's last word is the one whose trailer is not maqaf. The verse's last unit ends at the last word.
    for index, word in enumerate(main):
        info = classify_word(system, word["surface"], word["trailer"], index == last_index)
        word["accents"] = info["accents"]
        word["meteg"] = info["meteg"]
        word["main_accent"] = info["main_accent"]
        word["level"] = info["level"]
        word["unknown_accents"] = info["unknown"]
        proclitic = word["trailer"] == MAQAF
        word["stress"] = stress_for(word["surface"], word["accents"], word["meteg"], proclitic)
        if multiset(word["surface"]) != multiset(word["surface_src"]):
            raise SystemExit(f"mark mismatch {word['id']}")
        if canon(word["surface"]) != word["surface"]:
            raise SystemExit(f"canon not stable {word['id']}")


def load_oshb(root: Path) -> list[dict]:
    books = []
    for osis, _en, _he, _section, _uxlc, _system in BOOKS:
        path = root / f"{osis}.xml"
        books.append({"osis": osis, "verses": parse_book(path, osis)})
    return books
