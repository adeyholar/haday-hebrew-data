"""Pause tree and OSHB-style division paths. §7."""


def build_tree(units: list[dict]) -> dict | None:
    if not units:
        return None

    def rec(i: int, j: int) -> dict:
        inner = [k for k in range(i, j) if units[k]["level"] is not None]
        if not inner:
            return {"leaf": [units[i]["unit"], units[j]["unit"]], "accent": units[j]["accent"]}
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
    if atnach is not None:
        paths[atnach["unit"]] = "1"
    elif ole is not None:
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
