"""Check the pinned sources against sources/SHA256SUMS before anything is built."""

import hashlib
from pathlib import Path

from builder.errors import SourceMismatch

SOURCES = Path(__file__).resolve().parents[1] / "sources"
UNPINNED = {"SHA256SUMS", "PINS.txt"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def pinned(root: Path = SOURCES) -> dict[str, str]:
    sums: dict[str, str] = {}
    for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        sums[name.strip().lstrip("*")] = digest.lower()
    return sums


def verify_sources(root: Path = SOURCES) -> dict[str, str]:
    """Raise SourceMismatch unless every file under sources/ matches its pin and every pin exists.

    On Windows a checkout with core.autocrlf would rewrite the XML and CSV line endings.
    .gitattributes marks sources/** -text so they arrive byte for byte; this check catches the rest.
    """
    sums = pinned(root)
    problems: list[str] = []
    for name, digest in sorted(sums.items()):
        path = root / name
        if not path.is_file():
            problems.append(f"missing {name}")
        elif _sha256(path) != digest:
            problems.append(f"hash differs {name}")
    for path in sorted(root.rglob("*")):
        if path.is_file():
            name = path.relative_to(root).as_posix()
            if name not in sums and name not in UNPINNED:
                problems.append(f"not pinned {name}")
    if problems:
        raise SourceMismatch("sources do not match sources/SHA256SUMS: " + "; ".join(problems[:10]))
    return sums
