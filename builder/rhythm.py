"""Pause tree and OSHB-style division paths. §7."""


def build_tree(units: list[dict]) -> dict | None:
    if not units:
        return None

    def rec(i: int, j: int) -> dict:
        inner = [k for k in range(i, j) if units[k]["level"] is not None]
        if not inner:
            return {
                "governor": units[j]["accent"],
                "leaf": [units[i]["unit"], units[j]["unit"]],
                "accent": units[j]["accent"],
            }
        strongest = min(units[k]["level"] for k in inner)
        split = next(k for k in inner if units[k]["level"] == strongest)
        return {
            "governor": units[j]["accent"],
            "span": [units[i]["unit"], units[j]["unit"]],
            "split": units[split]["unit"],
            "left": rec(i, split),
            "right": rec(split + 1, j),
        }

    return rec(0, len(units) - 1)


def division_paths(units: list[dict]) -> dict[int, str]:
    """Silluq is 0, atnach is 1, ole veyored is 2. A verse with no atnach is split by its strongest king."""
    disj = [unit for unit in units if unit["level"] is not None]
    if not disj:
        return {}
    paths: dict[int, str] = {disj[-1]["unit"]: "0"}
    ole = next((unit for unit in disj if unit["accent"] == "ole_veyored"), None)
    atnach = next((unit for unit in disj if unit["accent"] == "atnach"), None)
    if ole is not None:
        paths[ole["unit"]] = "2"
    # Atnach is 1 only when a silluq stands after it. An atnach that ends the verse is 0.
    if atnach is not None and atnach is not disj[-1]:
        paths[atnach["unit"]] = "1"
    elif atnach is None and ole is not None:
        # Poetic verse with ole veyored and no atnach: the strongest king on the silluq side takes the "1" half.
        pool = [unit for unit in disj[:-1] if unit["unit"] > ole["unit"]]
        if pool:
            strongest = min(unit["level"] for unit in pool)
            chosen = next(unit for unit in pool if unit["level"] == strongest)
            paths[chosen["unit"]] = "1"

    def domain(start: int, end: int, path: str) -> None:
        inner = [unit for unit in disj if start < unit["unit"] < end and unit["unit"] not in paths]
        if not inner:
            return
        strongest = min(unit["level"] for unit in inner)
        subs = [unit for unit in inner if unit["level"] == strongest]
        for offset, unit in enumerate(reversed(subs)):
            paths[unit["unit"]] = f"{path}.{offset}"
        prev = start
        for unit in subs:
            domain(prev, unit["unit"], paths[unit["unit"]])
            prev = unit["unit"]

    prev = 0
    for unit in sorted((unit for unit in disj if unit["unit"] in paths), key=lambda item: item["unit"]):
        domain(prev, unit["unit"], paths[unit["unit"]])
        prev = unit["unit"]
    return paths


# Poetic division ranks. Lower is stronger. These follow the OSHB accent catalog
# (Wickes), not the stored `level`, which still names the accent's own class.
# Revia outranks dechi and tsinnor. Those outrank legarmeh.
_POETIC_RANK = {
    "silluq": 0,
    "atnach": 0,
    "ole_veyored": 0,
    "revia_gadol": 1,
    "revia_mugrash": 1,
    "revia": 1,
    "pazer": 1,
    "shalshelet_gedolah": 1,
    "tsinnor": 2,
    "dechi": 2,
    "revia_qatan": 2,
    "legarmeh": 3,
    "geresh": 3,
    "geresh_muqdam": 3,
    "gershayim": 3,
}


def _poetic_rank(unit: dict) -> int:
    accent = unit.get("accent") or ""
    if accent in _POETIC_RANK:
        return _POETIC_RANK[accent]
    level = unit.get("level")
    return level if isinstance(level, int) else 9


def poetic_paths(units: list[dict]) -> dict[int, str]:
    """OSHB `n` for poetry.

    Silluq is 0. Atnach is 1. Ole veyored is 2 beside an atnach. With no atnach, a
    revia gadol in the second half takes 1 and ole stays 2. With neither, ole
    takes 1. Inside a domain the rightmost disjunctive is the near divider (.0).
    A stronger disjunctive to its left is the remote divider (.1). A weaker one
    to the left nests under the near divider.
    """
    disj = [unit for unit in units if unit["level"] is not None]
    if not disj:
        return {}
    paths: dict[int, str] = {disj[-1]["unit"]: "0"}
    atnach = next((unit for unit in disj if unit["accent"] == "atnach"), None)
    ole = next((unit for unit in disj if unit["accent"] == "ole_veyored"), None)
    anchors = [disj[-1]]
    if atnach is not None and atnach is not disj[-1]:
        paths[atnach["unit"]] = "1"
        anchors.append(atnach)
        if ole is not None:
            paths[ole["unit"]] = "2"
            anchors.append(ole)
    elif atnach is None:
        # No atnach. A revia gadol stands in for it and keeps number 1, so ole stays 2.
        # With neither, ole itself is the major divider and takes 1.
        ole_at = ole["unit"] if ole is not None else 0
        stand_in = [
            unit
            for unit in disj
            if unit["accent"] == "revia_gadol" and unit["unit"] > ole_at and unit is not disj[-1]
        ]
        if stand_in:
            chosen = max(stand_in, key=lambda unit: unit["unit"])
            paths[chosen["unit"]] = "1"
            anchors.append(chosen)
            if ole is not None:
                paths[ole["unit"]] = "2"
                anchors.append(ole)
        elif ole is not None:
            paths[ole["unit"]] = "1"
            anchors.append(ole)
    anchors.sort(key=lambda unit: unit["unit"])

    def domain(start: int, end: int, path: str) -> None:
        inner = [unit for unit in disj if start < unit["unit"] < end and unit["unit"] not in paths]
        if not inner:
            return
        near = max(inner, key=lambda unit: unit["unit"])
        best = min(_poetic_rank(unit) for unit in inner)
        remote = max((unit for unit in inner if _poetic_rank(unit) == best), key=lambda unit: unit["unit"])
        if remote["unit"] != near["unit"] and _poetic_rank(near) > _poetic_rank(remote):
            paths[near["unit"]] = f"{path}.0"
            paths[remote["unit"]] = f"{path}.1"
            domain(start, remote["unit"], paths[remote["unit"]])
            domain(remote["unit"], near["unit"], paths[near["unit"]])
            return
        paths[near["unit"]] = f"{path}.0"
        domain(start, near["unit"], paths[near["unit"]])

    prev = 0
    for anchor in anchors:
        domain(prev, anchor["unit"], paths[anchor["unit"]])
        prev = anchor["unit"]
    return paths

