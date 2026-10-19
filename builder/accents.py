"""Accent classification for the prose and poetic systems. §5."""

from builder.canon import ACCENTS, METEG, clusters

# cp -> (name, kind, level, placement). Context rules override these.
PROSE: dict[int, tuple[str, str, int | str, str]] = {
    0x0591: ("atnach", "D", 0, "imp"),
    0x0592: ("segolta", "D", 1, "post"),
    0x0593: ("shalshelet", "D", 1, "imp"),
    0x0594: ("zaqef_qatan", "D", 1, "imp"),
    0x0595: ("zaqef_gadol", "D", 1, "imp"),
    0x0596: ("tipcha", "D", 1, "imp"),
    0x0597: ("revia", "D", 2, "imp"),
    0x0598: ("zarqa", "D", 2, "post"),
    0x0599: ("pashta", "D", 2, "post"),
    0x059A: ("yetiv", "D", 2, "pre"),
    0x059B: ("tevir", "D", 2, "imp"),
    0x059C: ("geresh", "D", 3, "imp"),
    0x059D: ("geresh_muqdam", "D", 3, "pre"),
    0x059E: ("gershayim", "D", 3, "imp"),
    0x059F: ("pazer_gadol", "D", 3, "imp"),
    0x05A0: ("telisha_gedola", "D", 3, "pre"),
    0x05A1: ("pazer", "D", 3, "imp"),
    0x05A2: ("atnach_hafukh", "D", 3, "imp"),
    0x05A3: ("munach", "C", "C", "imp"),
    0x05A4: ("mahpakh", "C", "C", "imp"),
    0x05A5: ("merkha", "C", "C", "imp"),
    0x05A6: ("merkha_kefula", "C", "C", "imp"),
    0x05A7: ("darga", "C", "C", "imp"),
    0x05A8: ("qadma", "C", "C", "imp"),
    0x05A9: ("telisha_qetana", "C", "C", "post"),
    # OSHB writes the prose atnach hafukh as U+05AA. UXLC writes U+05A2. Same mark. It stays conjunctive.
    0x05AA: ("atnach_hafukh", "C", "C", "imp"),
    0x05AB: ("ole", "D", 0, "imp"),
    0x05AC: ("illuy", "C", "C", "imp"),
    0x05AD: ("dechi", "D", 2, "pre"),
    0x05AE: ("zarqa", "D", 2, "post"),
}

POETIC: dict[int, tuple[str, str, int | str, str]] = {
    0x0591: ("atnach", "D", 0, "imp"),
    0x0593: ("shalshelet_qetanah", "C", "C", "imp"),
    0x0596: ("tarcha", "C", "C", "imp"),
    0x0597: ("revia_gadol", "D", 1, "imp"),
    0x0598: ("tsinnorit", "C", "C", "imp"),
    0x059C: ("geresh", "D", 3, "imp"),
    0x059D: ("geresh_muqdam", "D", 3, "pre"),
    0x05A1: ("pazer", "D", 2, "imp"),
    0x05A2: ("atnach_hafukh", "D", 3, "imp"),
    0x05A3: ("munach", "C", "C", "imp"),
    0x05A4: ("mehuppakh", "C", "C", "imp"),
    0x05A5: ("merkha", "C", "C", "imp"),
    0x05A8: ("azla", "C", "C", "imp"),
    0x05AA: ("galgal", "C", "C", "imp"),
    0x05AB: ("ole", "D", 0, "imp"),
    0x05AC: ("illuy", "C", "C", "imp"),
    0x05AD: ("dechi", "D", 2, "pre"),
    0x05AE: ("tsinnor", "D", 1, "post"),
}

HEBREW = {
    "atnach": "אֶתְנַחְתָּא",
    "segolta": "סְגוֹלְתָּא",
    "shalshelet": "שַׁלְשֶׁלֶת",
    "shalshelet_gedolah": "שַׁלְשֶׁלֶת גְּדוֹלָה",
    "shalshelet_qetanah": "שַׁלְשֶׁלֶת קְטַנָּה",
    "zaqef_qatan": "זָקֵף קָטֹן",
    "zaqef_gadol": "זָקֵף גָּדוֹל",
    "tipcha": "טִפְחָא",
    "tarcha": "טַרְחָא",
    "revia": "רְבִיעַ",
    "revia_gadol": "רְבִיעַ גָּדוֹל",
    "revia_qatan": "רְבִיעַ קָטֹן",
    "revia_mugrash": "רְבִיעַ מֻגְרָשׁ",
    "zarqa": "זַרְקָא",
    "pashta": "פַּשְׁטָא",
    "pashta_first": "פַּשְׁטָא",
    "yetiv": "יְתִיב",
    "tevir": "תְּבִיר",
    "geresh": "גֵּרֵשׁ",
    "geresh_muqdam": "גֵּרֵשׁ מֻקְדָּם",
    "gershayim": "גֵּרְשַׁיִם",
    "pazer": "פָּזֵר",
    "pazer_gadol": "פָּזֵר גָּדוֹל",
    "telisha_gedola": "תְּלִישָׁא גְדוֹלָה",
    "telisha_qetana": "תְּלִישָׁא קְטַנָּה",
    "legarmeh": "לְגַרְמֵהּ",
    "munach": "מֻנַּח",
    "mahpakh": "מַהְפַּךְ",
    "mehuppakh": "מְהֻפָּךְ",
    "merkha": "מֵרְכָא",
    "merkha_kefula": "מֵרְכָא כְפוּלָה",
    "darga": "דַּרְגָּא",
    "qadma": "קַדְמָא",
    "azla": "אַזְלָא",
    "galgal": "גַּלְגַּל",
    "ole": "עוֹלֶה",
    "ole_veyored": "עוֹלֶה וְיוֹרֵד",
    "illuy": "עִלּוּי",
    "dechi": "דְּחִי",
    "tsinnor": "צִנּוֹר",
    "tsinnorit": "צִנּוֹרִית",
    "mayela": "מָאיְלָא",
    "silluq": "סִלּוּק",
    "atnach_hafukh": "אֶתְנָח הָפוּךְ",
    "yored": "יוֹרֵד",
}

# Prose legarmeh is munach + paseq only. Poetry legarmeh is mehuppakh or azla + paseq.
# Poetic munach + paseq stays conjunctive (OSHB catalog). Ps 68:21 is the one OSHB numbers.
POETIC_LEGARMEH = {0x05A4, 0x05A8}
PROSE_LEGARMEH = {0x05A3}
PASEQ = "\u05C0"


def _cp_hex(cp: int) -> str:
    return f"U+{cp:04X}"


def _placed(surface: str) -> list[tuple[int, int, int]]:
    """(codepoint, letter_index, order) for accents and metegs."""
    found: list[tuple[int, int, int]] = []
    order = 0
    for index, (_letter, marks) in enumerate(clusters(surface)):
        for mark in marks:
            cp = ord(mark)
            if cp in ACCENTS or cp in METEG:
                found.append((cp, index, order))
                order += 1
    return found


def _row(cp: int, index: int, order: int, name: str, kind: str, level: int | str, placement: str, compound: str | None) -> dict:
    return {
        "cp": _cp_hex(cp) if cp else "",
        "name": name,
        "name_he": HEBREW.get(name, ""),
        "role": "secondary",
        "kind": kind,
        "level": level,
        "letter_index": index,
        "placement": placement,
        "compound": compound,
        "_order": order,
        "_cp": cp,
    }


def classify_word(system: str, surface: str, trailer: str, is_last_unit: bool, verse_has_sof: bool = True) -> dict:
    table = POETIC if system == "poetic" else PROSE
    placed = _placed(surface)
    accents_raw = [item for item in placed if item[0] in ACCENTS]
    metegs_raw = [item for item in placed if item[0] in METEG]
    cps = [cp for cp, _i, _o in accents_raw]
    has_paseq = PASEQ in trailer

    ole_here = 0x05AB in cps
    rows: list[dict] = []
    unknown: list[int] = []
    for cp, index, order in accents_raw:
        compound = None
        if system == "poetic" and cp == 0x0597 and 0x059D in cps:
            name, kind, level, placement = "revia_mugrash", "D", 1, "imp"
            compound = "revia_mugrash"
        elif system == "poetic" and cp == 0x059D and 0x0597 in cps:
            name, kind, level, placement = "geresh_muqdam", "C", "C", "imp"
            compound = "revia_mugrash"
        elif system == "poetic" and ole_here and cp == 0x05A5:
            name, kind, level, placement = "yored", "D", 0, "imp"
            compound = "ole_veyored"
        elif system == "poetic" and ole_here and cp == 0x05AB and 0x05A5 in cps:
            name, kind, level, placement = "ole", "C", "C", "imp"
            compound = "ole_veyored"
        elif cp in table:
            name, kind, level, placement = table[cp]
        elif cp in PROSE:
            name, kind, level, placement = PROSE[cp]
            unknown.append(cp)
        else:
            name, kind, level, placement = "unknown", "C", "C", "imp"
            unknown.append(cp)
        if system == "poetic" and cp == 0x0593 and has_paseq:
            name, kind, level, placement = "shalshelet_gedolah", "D", 1, "imp"
        if has_paseq and cp == cps[-1] and cp in (POETIC_LEGARMEH if system == "poetic" else PROSE_LEGARMEH):
            level_n = 2 if system == "poetic" else 3
            name = "legarmeh"
            kind, level, placement = "D", level_n, "imp"
        if system == "prose" and cp == 0x0593 and not has_paseq:
            unknown.append(cp)
        rows.append(_row(cp, index, order, name, kind, level, placement, compound))

    pashtas = [row for row in rows if row["name"] == "pashta"]
    if len(pashtas) == 1:
        earlier = next(
            (row for row in rows if row["name"] in ("qadma", "azla") and row["letter_index"] < pashtas[0]["letter_index"]),
            None,
        )
        if earlier:
            earlier["name"] = "pashta_first"
            earlier["name_he"] = HEBREW["pashta_first"]

    silluq_index = None
    inferred = False
    groups = clusters(surface)
    already_disjunctive = any(row["kind"] == "D" for row in rows)
    if is_last_unit and metegs_raw:
        silluq_index = metegs_raw[-1][1]
    elif is_last_unit and (verse_has_sof or not already_disjunctive):
        # No sof and the word already has its own disjunctive (Num 25:19 atnach): do not invent a silluq.
        inferred = True
        silluq_index = len(groups) - 1 if groups else 0
    meteg = []
    for _cp, index, _order in metegs_raw:
        meteg.append({"letter_index": index, "function": "silluq" if index == silluq_index and not inferred else "meteg"})

    if is_last_unit and not inferred and silluq_index is not None:
        rows.append(_row(0x05BD, silluq_index, 10_000, "silluq", "D", 0, "imp", None))
    elif inferred:
        rows.append(
            {
                **_row(0, silluq_index or 0, 10_000, "silluq", "D", 0, "imp", None),
                "cp": "",
                "inferred": True,
            }
        )

    present = {row["name"] for row in rows}
    for row in rows:
        if row["name"] == "tipcha" and ("atnach" in present or (silluq_index is not None and not inferred)):
            row["name"] = "mayela"
            row["name_he"] = HEBREW["mayela"]
            row["kind"] = "C"
            row["level"] = "C"
            row["role"] = "secondary"

    for row in rows:
        row["role"] = "secondary"
    disj = [row for row in rows if row["kind"] == "D"]
    if disj:
        silluq_rows = [row for row in disj if row["name"] == "silluq"]
        if is_last_unit and verse_has_sof and silluq_rows:
            best = silluq_rows[-1]
        else:
            best = min(disj, key=lambda row: (row["level"] if isinstance(row["level"], int) else 9, row["letter_index"]))
        best["role"] = "main"
        main = best
    elif rows:
        rows[-1]["role"] = "main"
        main = rows[-1]
    else:
        main = None
    for row in rows:
        row.pop("_order", None)
        row.pop("_cp", None)
        if not row.get("compound"):
            row.pop("compound", None)
        if not row.get("inferred"):
            row.pop("inferred", None)
    main_name = main["name"] if main else None
    if any(row.get("compound") == "ole_veyored" and row["kind"] == "D" for row in rows):
        main_name = "ole_veyored"
    level = main["level"] if main and main["kind"] == "D" and isinstance(main["level"], int) else None
    if main_name == "ole_veyored":
        level = 0
    return {
        "accents": rows,
        "meteg": meteg,
        "main_accent": main_name,
        "level": level,
        "kind": main["kind"] if main else None,
        "unknown": unknown,
        "silluq_index": silluq_index if not inferred else None,
        "silluq_inferred": inferred,
    }
