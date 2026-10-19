"""The one place the pins live: sources/PINS.txt (KEY=value lines)."""

from functools import lru_cache
from pathlib import Path

from builder.errors import PinError

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
REQUIRED = ("DATASET_VERSION", "OSHB_COMMIT", "UXLC_SHA256", "UXLC_VERSION", "UXLC_BUILD", "UXLC_ZIP", "OSHB_DIR", "TRIAGE_FILE")


@lru_cache(maxsize=None)
def pins(path: Path = SOURCES / "PINS.txt") -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or not key.strip():
            raise PinError(f"{path.name} line {number}: {line!r}")
        values[key.strip()] = value.strip()
    missing = [key for key in REQUIRED if not values.get(key)]
    if missing:
        raise PinError(f"{path.name} lacks {', '.join(missing)}")
    return values


def pin(key: str) -> str:
    return pins()[key]


def triage_path() -> Path:
    return SOURCES / pin("TRIAGE_FILE")


def uxlc_zip() -> Path:
    return SOURCES / pin("UXLC_ZIP")


def oshb_dir() -> Path:
    return SOURCES / pin("OSHB_DIR")
