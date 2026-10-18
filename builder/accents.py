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
    0x059D: ("geresh_muqdam", "D", 3, "imp"),
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
    0x05AA: ("galgal", "C", "C", "imp"),
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
    0x059D: ("geresh_muqdam", "D", 3, "imp"),
    0x05A1: ("pazer", "D", 2, "imp"),
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

LEGARMEH_CPS = {0x05A3, 0x05A4, 0x05A8}
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


def classify_word(system: str, surface: str, trailer: str, is_last_unit: bool) -> dict:
    table = POETIC if system == "poetic" else PROSE
    placed = _placed(surface)
    accents_raw = [item for item in placed if item[0] in ACCENTS]
    metegs_raw = [item for item in placed if item[0] in METEG]
    cps = [cp for cp, _i, _o in accents_raw]
    has_paseq = PASEQ in trailer

    ole_here = 0x05AB in cps
    yored_here = 0x05A5 in cps and (ole_here or False)
    # yored-with-ole on the same word is decided here; ole on the previous unit is applied by the verse pass.

    rows: list[dict] = []
    unknown: list[int] = []
    for cp, index, order in accents_raw:
        if system == "poetic" and cp == 0x0597 and 0x059D in cps:
            name, kind, level, placement = "revia_mugrash", "D", 1, "imp"
        elif system == "poetic" and cp == 0x059D and 0x0597 in cps:
            continue
        elif system == "poetic" and ole_here and cp == 0x05A5:
            name, kind, level, placement = "ole_veyored", "D", 0, "imp"
        elif system == "poetic" and ole_here and cp == 0x05AB and 0x05A5 in cps:
            continue
        elif cp in table:
            name, kind, level, placement = table[cp]
        elif cp in PROSE:
            name, kind, level, placement = PROSE[cp]
            unknown.append(cp)
        else:
            name, kind, level, placement = "unknown", "C", "C", "imp"
            unknown.append(cp)
        if has_paseq and cp in LEGARMEH_CPS and cp == cps[-1]:
            level_n = 2 if system == "poetic" else 3
            name = "legarmeh"
            kind, level, placement = "D", level_n, "imp"
        if system == "prose" and cp == 0x0593 and not has_paseq:
            unknown.append(cp)
        rows.append(
            {
                "cp": _cp_hex(cp),
                "name": name,
                "name_he": HEBREW.get(name, ""),
                "role": "secondary",
                "kind": kind,
                "level": level,
                "letter_index": index,
                "placement": placement,
                "_order": order,
                "_cp": cp,
            }
        )

    silluq_index = None
    if is_last_unit and metegs_raw:
        silluq_index = metegs_raw[-1][1]
    meteg = []
    for _cp, index, _order in metegs_raw:
        meteg.append({"letter_index": index, "function": "silluq" if index == silluq_index else "meteg"})

    if silluq_index is not None:
        rows.append(
            {
                "cp": "U+05BD",
                "name": "silluq",
                "name_he": HEBREW["silluq"],
                "role": "secondary",
                "kind": "D",
                "level": 0,
                "letter_index": silluq_index,
                "placement": "imp",
                "_order": 10_000,
                "_cp": METEG,
            }
        )

    present = {row["name"] for row in rows}
    for row in rows:
        if row["name"] == "tipcha" and ("atnach" in present or silluq_index is not None):
            row["name"] = "mayela"
            row["name_he"] = HEBREW["mayela"]
            row["kind"] = "C"
            row["level"] = "C"
            row["role"] = "secondary"

    for row in rows:
        row["role"] = "secondary"
    disj = [row for row in rows if row["kind"] == "D"]
    if disj:
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
    level = main["level"] if main and main["kind"] == "D" and isinstance(main["level"], int) else None
    return {
        "accents": rows,
        "meteg": meteg,
        "main_accent": main["name"] if main else None,
        "level": level,
        "kind": main["kind"] if main else None,
        "unknown": unknown,
        "silluq_index": silluq_index,
    }
