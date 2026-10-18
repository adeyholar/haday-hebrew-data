"""Stress syllable from the main accent. §8."""

from builder.canon import clusters

FULL = set(range(0x05B4, 0x05BC)) | {0x05C7}
PATAH = 0x05B7
DAGESH = 0x05BC
HOLAM = 0x05B9
FURTIVE_LETTERS = set("חע")


def _nuclei(surface: str) -> list[int]:
    groups = clusters(surface)
    found: list[int] = []
    for index, (letter, marks) in enumerate(groups):
        cps = {ord(mark) for mark in marks}
        vowels = cps & FULL
        if letter == "ו" and DAGESH in cps and not (cps & (FULL | {0x05B0, 0x05B1, 0x05B2, 0x05B3})):
            found.append(index)
        elif vowels:
            found.append(index)
    if len(groups) >= 2 and found:
        letter, marks = groups[-1]
        cps = {ord(mark) for mark in marks}
        mappiq_he = letter == "ה" and DAGESH in cps
        if (letter in FURTIVE_LETTERS or mappiq_he) and PATAH in cps and found[-1] == len(groups) - 1:
            earlier = [n for n in found if n < len(groups) - 1]
            if earlier:
                found = earlier
    return found


def syll_from_end(surface: str, letter_index: int) -> int:
    after = sum(1 for n in _nuclei(surface) if n > letter_index)
    return 1 + after


def stress_for(surface: str, accents: list[dict], meteg: list[dict], proclitic: bool) -> dict | None:
    if proclitic:
        return None
    if not surface:
        return None
    mains = [row for row in accents if row.get("role") == "main"]
    main = mains[0] if mains else None
    groups = clusters(surface)
    last_letter = max(0, len(groups) - 1)

    if main and main["name"] == "pashta":
        pashtas = [row for row in accents if row["name"] == "pashta"]
        if len(pashtas) >= 2:
            index = pashtas[0]["letter_index"]
            return {"letter_index": index, "syll_from_end": syll_from_end(surface, index), "source": "doubled"}
        # OSHB writes the repeated pashta as qadma on the stress and pashta on the last letter.
        qadma = next((row for row in accents if row["name"] in ("qadma", "azla") and row["letter_index"] < main["letter_index"]), None)
        if qadma:
            index = qadma["letter_index"]
            return {"letter_index": index, "syll_from_end": syll_from_end(surface, index), "source": "doubled"}

    if main and main["name"] == "silluq":
        index = main["letter_index"]
        return {"letter_index": index, "syll_from_end": syll_from_end(surface, index), "source": "silluq"}

    if main and main["placement"] == "imp" and main["kind"] == "D":
        index = main["letter_index"]
        return {"letter_index": index, "syll_from_end": syll_from_end(surface, index), "source": "accent"}

    if main and main["kind"] == "C" and main["placement"] == "imp":
        index = main["letter_index"]
        return {"letter_index": index, "syll_from_end": syll_from_end(surface, index), "source": "accent"}

    # Single prepositive or postpositive: a conjunctive or a meteg in the word, else the ultima.
    conjunctive = next((row for row in accents if row["kind"] == "C" and row["placement"] == "imp"), None)
    if conjunctive:
        index = conjunctive["letter_index"]
        return {"letter_index": index, "syll_from_end": syll_from_end(surface, index), "source": "conjunctive"}
    plain = next((row for row in meteg if row["function"] == "meteg"), None)
    if plain:
        index = plain["letter_index"]
        return {"letter_index": index, "syll_from_end": syll_from_end(surface, index), "source": "meteg"}
    nuclei = _nuclei(surface)
    index = nuclei[-1] if nuclei else last_letter
    return {"letter_index": index, "syll_from_end": syll_from_end(surface, index), "source": "default-ultima"}
