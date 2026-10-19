"""One parse of the pinned corpus per test run, shared by the test classes. Treat it as read-only."""

import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from builder.oshb import load_oshb  # noqa: E402
from builder.pins import uxlc_zip  # noqa: E402
from builder.uxlc import load_uxlc  # noqa: E402


@lru_cache(maxsize=None)
def uxlc() -> dict:
    return load_uxlc(uxlc_zip())


@lru_cache(maxsize=None)
def books() -> list[dict]:
    return load_oshb(uxlc=uxlc())
