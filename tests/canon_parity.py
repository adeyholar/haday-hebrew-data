"""Write every distinct Hebrew string in a built dataset with its Python canon, for packages/canon/parity.ts.

python tests/canon_parity.py dist dist/canon-parity.json
node --experimental-strip-types packages/canon/parity.ts dist/canon-parity.json
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from builder.canon import canon  # noqa: E402


def main(out: Path, target: Path) -> None:
    db = sqlite3.connect(out / "hebrew-bible.sqlite")
    seen: set[str] = set()
    for (text,) in db.execute("select surface_src from word union select surface from word union select uxlc from word"):
        if text:
            seen.add(text)
    for (text,) in db.execute("select rdg from word_alt union select text_src from verse"):
        if text:
            seen.add(text)
    pairs = [[text, canon(text)] for text in sorted(seen)]
    target.write_text(json.dumps(pairs, ensure_ascii=False), encoding="utf-8")
    print(f"canon parity: {len(pairs)} strings written")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
