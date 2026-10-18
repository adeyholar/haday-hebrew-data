"""Stress syllable from the main accent. §8."""

from builder.canon import clusters

FULL = set(range(0x05B4, 0x05BC)) | {0x05C7}
PATAH = 0x05B7
DAGESH = 0x05BC
HOLAM = 0x05B9
SHEVA = {0x05B0, 0x05B1, 0x05B2, 0x05B3}
FURTIVE_LETTERS = set("חע")


def _marks(marks: list[str]) -> set[int]:
    return {ord(mark) for mark in marks}


def _vowel_letter_vav(letter: str, cps: set[int]) -> bool:
    """Holam male (וֹ) or shureq (וּ). The vowel belongs to the consonant before the vav."""
    if letter != "ו":
        return False
    vowels = cps & FULL
    if HOLAM in cps and not (vowels - {HOLAM}):
        return True
    if DAGESH in cps and not vowels and not (cps & SHEVA):
        return True
    return False


def _nuclei(surface: str) -> list[int]:
    groups = clusters(surface)
    owned: set[int] = set()
    skip: set[int] = set()
    for index in range(len(groups) - 1):
        _letter, marks = groups[index]
        if _marks(marks) & FULL:
            continue
        next_letter, next_marks = groups[index + 1]
        if _vowel_letter_vav(next_letter, _marks(next_marks)):
            owned.add(index)
            skip.add(index + 1)
    found: list[int] = []
    for index, (letter, marks) in enumerate(groups):
        if index in skip:
            continue
        if index in owned:
            found.append(index)
            continue
        cps = _marks(marks)
        if letter == "ו" and DAGESH in cps and not (cps & (FULL | SHEVA)):
            found.append(index)
        elif cps & FULL:
            found.append(index)
    if len(groups) >= 2 and found:
        letter, marks = groups[-1]
        cps = _marks(marks)
        mappiq_he = letter == "ה" and DAGESH in cps
        if (letter in FURTIVE_LETTERS or mappiq_he) and PATAH in cps and found[-1] == len(groups) - 1:
            earlier = [n for n in found if n < len(groups) - 1]
            if earlier:
                found = earlier
    return found


def _shewa_only(surface: str, index: int) -> bool:
    groups = clusters(surface)
    if index < 0 or index >= len(groups):
        return False
    cps = _marks(groups[index][1])
    return bool(cps & SHEVA) and not (cps & FULL)


def _quiescent_aleph(surface: str, index: int) -> bool:
    """A silent aleph is not its own syllable. וֹ and וּ owned by the aleph are not this case."""
    groups = clusters(surface)
    if index < 0 or index >= len(groups) or groups[index][0] != "א":
        return False
    if index in _nuclei(surface):
        return False
    return not (_marks(groups[index][1]) & FULL)


def _prepositive_blocks(accents: list[dict], index: int) -> bool:
    """Dechi, telisha gedola, and geresh muqdam are written early. They are not the tone."""
    return any(
        row.get("placement") == "pre" and row.get("letter_index") == index and row.get("name") != "yetiv"
        for row in accents
    )


def _prefer_tone(surface: str, index: int, accents: list[dict]) -> int:
    nuclei = _nuclei(surface)
    if _prepositive_blocks(accents, index) and any(n > index for n in nuclei):
        return nuclei[-1]
    if _quiescent_aleph(surface, index):
        earlier = [n for n in nuclei if n < index]
        if earlier:
            return earlier[-1]
    return index


def syll_from_end(surface: str, letter_index: int) -> int:
    after = sum(1 for n in _nuclei(surface) if n > letter_index)
    return 1 + after


def _pack(surface: str, index: int, accents: list[dict], source: str) -> dict:
    chosen = _prefer_tone(surface, index, accents)
    used = source if chosen == index else "default-ultima"
    return {"letter_index": chosen, "syll_from_end": syll_from_end(surface, chosen), "source": used}


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
            return _pack(surface, pashtas[0]["letter_index"], accents, "doubled")
        # OSHB writes the repeated pashta as qadma on the stress and pashta on the last letter.
        earlier = next(
            (
                row
                for row in accents
                if row["name"] in ("qadma", "azla", "pashta_first") and row["letter_index"] < main["letter_index"]
            ),
            None,
        )
        if earlier:
            return _pack(surface, earlier["letter_index"], accents, "doubled")

    if main and main["name"] == "silluq":
        return _pack(surface, main["letter_index"], accents, "silluq")

    if main and main["placement"] == "imp" and main["kind"] == "D":
        return _pack(surface, main["letter_index"], accents, "accent")

    if main and main["kind"] == "C" and main["placement"] == "imp":
        return _pack(surface, main["letter_index"], accents, "accent")

    # A prepositive or postpositive mark is not the tone. A conjunctive can be.
    # A meteg on shewa is not the tone either.
    conjunctive = next((row for row in accents if row["kind"] == "C" and row["placement"] == "imp"), None)
    if conjunctive and not _prepositive_blocks(accents, conjunctive["letter_index"]):
        return _pack(surface, conjunctive["letter_index"], accents, "conjunctive")
    plain = next(
        (
            row
            for row in meteg
            if row["function"] == "meteg" and not _shewa_only(surface, row["letter_index"]) and not _prepositive_blocks(accents, row["letter_index"])
        ),
        None,
    )
    if plain:
        return _pack(surface, plain["letter_index"], accents, "meteg")
    nuclei = _nuclei(surface)
    index = nuclei[-1] if nuclei else last_letter
    return _pack(surface, index, accents, "default-ultima")

