"""Read a built dataset and check the chapter JSON against the SQLite file."""

import json
import sqlite3
import sys
from pathlib import Path


def main(out: Path) -> None:
    db = sqlite3.connect(out / "hebrew-bible.sqlite")
    version = db.execute("select value from meta where key = 'dataset_version'").fetchone()[0]
    if version != "1.1.1":
        raise SystemExit(f"dataset_version {version}")
    verses = db.execute("select count(*) from verse").fetchone()[0]
    words = db.execute("select count(*) from word").fetchone()[0]
    qere = db.execute("select count(*) from word where kq_role = 'qere'").fetchone()[0]
    no_sof = json.loads((out / "build-report" / "no-sof-pasuq.json").read_text(encoding="utf-8"))
    diffs = db.execute("select count(*) from uxlc_diff").fetchone()[0]
    if verses != 23213 or words != 306785 or qere != 1278:
        raise SystemExit(f"counts verses={verses} words={words} qere={qere}")
    if len(no_sof) != 21 or diffs != 1171:
        raise SystemExit(f"no_sof={len(no_sof)} uxlc={diffs}")
    chapter = json.loads((out / "json" / "Gen" / "1.json").read_text(encoding="utf-8"))
    for verse in chapter["verses"]:
        rows = db.execute(
            "select surface from word where ref = ? and ifnull(kq_role, '') != 'qere' order by pos",
            (verse["ref"],),
        ).fetchall()
        surfaces = [word["surface"] for word in verse["words"]]
        if surfaces != [row[0] for row in rows]:
            raise SystemExit(f"JSON differs from SQLite at {verse['ref']}")
    doubled = db.execute("select count(*) from word where trailer = ?", ("  \u05c0 ",)).fetchone()[0]
    if doubled:
        raise SystemExit(f"double-spaced paseq trailers: {doubled}")
    print(f"dist ok: {verses} verses, {words} words, UXLC rows {diffs}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
