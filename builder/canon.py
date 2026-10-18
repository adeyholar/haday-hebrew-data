"""HaDay canonical mark order. Never call Unicode NFC/NFD on Hebrew."""

SHIN = {0x05C1, 0x05C2}
DAGESH = {0x05BC}
RAFE = {0x05BF}
VOWELS = set(range(0x05B0, 0x05BC)) | {0x05C7}
METEG = {0x05BD}
ACCENTS = set(range(0x0591, 0x05B0))
DOTS = {0x05C4, 0x05C5}
HARD = {0x034F, 0x200D, 0x200C}
MAQAF = "\u05BE"
PASEQ = "\u05C0"
SOF = "\u05C3"
STOPS = set(" \t\n\r" + MAQAF + PASEQ + SOF)


def is_letter(cp: int) -> bool:
    return 0x05D0 <= cp <= 0x05EA


def _rank(cp: int) -> int:
    if cp in SHIN:
        return 1
    if cp in DAGESH:
        return 2
    if cp in RAFE:
        return 3
    if cp in VOWELS:
        return 4
    if cp in METEG:
        return 5
    if cp in ACCENTS:
        return 6
    if cp in DOTS:
        return 7
    return 8


def canon(text: str) -> str:
    """Stable cluster order. Accents keep their source order. Idempotent."""
    chars = list(text)
    out: list[str] = []
    i = 0
    n = len(chars)
    while i < n:
        cp = ord(chars[i])
        if cp in HARD or not is_letter(cp):
            out.append(chars[i])
            i += 1
            continue
        j = i + 1
        marks: list[tuple[int, int, str]] = []
        while j < n:
            cp2 = ord(chars[j])
            if cp2 in HARD or is_letter(cp2) or chars[j] in STOPS:
                break
            marks.append((_rank(cp2), j, chars[j]))
            j += 1
        marks.sort(key=lambda item: (item[0], item[1]))
        out.append(chars[i])
        out.extend(item[2] for item in marks)
        i = j
    return "".join(out)


def consonants(text: str) -> str:
    return "".join(ch for ch in text if is_letter(ord(ch)))


def pointed(text: str) -> str:
    """Vowels, dagesh, shin/sin, rafe, upper/lower dots. No accents, no meteg."""
    drop = ACCENTS | METEG
    return "".join(ch for ch in text if ord(ch) not in drop and ch not in (MAQAF, PASEQ, SOF) and not ch.isspace())


def clusters(text: str) -> list[tuple[str, list[str]]]:
    """(letter, marks) for each consonant. Hard boundaries are skipped."""
    chars = list(text)
    out: list[tuple[str, list[str]]] = []
    i = 0
    n = len(chars)
    while i < n:
        cp = ord(chars[i])
        if not is_letter(cp):
            i += 1
            continue
        marks: list[str] = []
        j = i + 1
        while j < n and not is_letter(ord(chars[j])) and ord(chars[j]) not in HARD and chars[j] not in STOPS:
            marks.append(chars[j])
            j += 1
        out.append((chars[i], marks))
        i = j
    return out


def multiset(text: str) -> dict[str, int]:
    bag: dict[str, int] = {}
    for ch in text:
        bag[ch] = bag.get(ch, 0) + 1
    return bag
