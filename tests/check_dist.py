"""Read a built dataset and check every chapter JSON against the SQLite file, word by word."""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from builder.canon import canon  # noqa: E402
from builder.pins import pin  # noqa: E402

SOF = "\u05c3"
WORD_FIELDS = ("surface", "trailer", "morphemes", "main_accent", "stress", "review", "review_class", "kq_role")


def _db_word(row: sqlite3.Row) -> dict:
    return {
        "surface": row["surface"],
        "trailer": row["trailer"],
        "morphemes": json.loads(row["morphemes"]),
        "main_accent": row["main_accent"],
        "stress": json.loads(row["stress"]),
        "review": row["review"],
        "review_class": row["review_class"],
        "kq_role": row["kq_role"],
        "accents": [{k: v for k, v in a.items() if k != "name_he"} for a in json.loads(row["accents"])],
    }


def _json_word(word: dict) -> dict:
    out = {field: word.get(field) for field in WORD_FIELDS}
    out["review"] = out["review"] or None
    out["accents"] = word.get("accents") or []
    return out


def main(out: Path) -> None:
    db = sqlite3.connect(out / "hebrew-bible.sqlite")
    db.row_factory = sqlite3.Row
    version = db.execute("select value from meta where key = 'dataset_version'").fetchone()[0]
    if version != pin("DATASET_VERSION"):
        raise SystemExit(f"dataset_version {version}")
    verses = db.execute("select count(*) from verse").fetchone()[0]
    words = db.execute("select count(*) from word").fetchone()[0]
    qere = db.execute("select count(*) from word where kq_role = 'qere'").fetchone()[0]
    no_sof = json.loads((out / "build-report" / "no-sof-pasuq.json").read_text(encoding="utf-8"))
    diffs = db.execute("select count(*) from uxlc_diff").fetchone()[0]
    if verses != 23213 or words != 306779 or qere != 1278:
        raise SystemExit(f"counts verses={verses} words={words} qere={qere}")
    if len(no_sof) != 21 or diffs != 44:
        raise SystemExit(f"no_sof={len(no_sof)} uxlc={diffs}")

    indexes = {row[0] for row in db.execute("select name from sqlite_master where type = 'index'")}
    if not {"accent_word", "word_alt_host", "unit_ref"} <= indexes:
        raise SystemExit(f"missing indexes: {sorted(indexes)}")
    db_words = {row["id"]: row for row in db.execute("select * from word")}
    db_verses = {row["ref"]: row for row in db.execute("select * from verse")}
    db_alts: dict[str, list] = {}
    for row in db.execute("select * from word_alt"):
        db_alts.setdefault(row["host_id"], []).append((row["note_type"], row["rdg"], row["review_class"], row["uncertain"], row["opt_in"]))

    seen_verses = seen_words = seen_alts = 0
    for path in sorted((out / "json").glob("*/*.json")):
        chapter = json.loads(path.read_text(encoding="utf-8"))
        for verse in chapter["verses"]:
            ref = verse["ref"]
            row = db_verses.get(ref)
            if row is None or row["text"] != verse["text"] or row["system"] != verse["system"]:
                raise SystemExit(f"verse JSON differs from SQLite at {ref}")
            seen_verses += 1
            # Round trip: the reading is the words and their trailers, plus sof pasuq.
            joined = "".join(word["surface"] + word["trailer"] for word in verse["words"]).rstrip()
            if row["has_sof_pasuq"] and not joined.endswith(SOF):
                joined += SOF
            if joined != verse["text"].rstrip():
                raise SystemExit(f"words do not rebuild the reading at {ref}")
            positions = [word["pos"] for word in verse["words"]]
            if positions != list(range(1, len(positions) + 1)):
                raise SystemExit(f"positions out of order at {ref}")
            for word in verse["words"]:
                for item in [word, *(word.get("qere") or [])]:
                    db_row = db_words.get(item["id"])
                    if db_row is None or db_row["ref"] != ref:
                        raise SystemExit(f"word {item['id']} missing from SQLite at {ref}")
                    if _json_word(item) != _db_word(db_row):
                        raise SystemExit(f"word JSON differs from SQLite at {ref} {item['id']}")
                    if "".join(item["morphemes"]) != item["surface"]:
                        raise SystemExit(f"morphemes do not make the surface at {ref} {item['id']}")
                    seen_words += 1
                    alts = [
                        (a["note_type"], a["rdg"], a.get("review_class"), int(bool(a.get("uncertain"))), int(bool(a.get("opt_in"))))
                        for a in item.get("alternatives") or []
                    ]
                    if alts != db_alts.get(item["id"], []):
                        raise SystemExit(f"alternatives differ at {ref} {item['id']}")
                    seen_alts += len(alts)
    if seen_verses != verses or seen_words != words:
        raise SystemExit(f"JSON covers {seen_verses} verses and {seen_words} words")
    if seen_alts != db.execute("select count(*) from word_alt").fetchone()[0]:
        raise SystemExit("word_alt rows outside the JSON")

    # An uncertain or diplomatic UXLC reading is an alternative only. The host keeps the OSHB reading.
    hosts = db.execute(
        "select w.id, w.surface, w.surface_src, w.review_class from word w join word_alt a on a.host_id = w.id"
        " where a.note_type in ('uxlc_uncertain', 'uxlc_diplomatic')"
    ).fetchall()
    applied = [row["id"] for row in hosts if row["surface"] != canon(row["surface_src"]) or row["review_class"]]
    if len(hosts) != 146 + 98 or applied:
        raise SystemExit(f"uncertain or optional readings: {len(hosts)} hosts, in the main text {applied[:5]}")
    doubled = db.execute("select count(*) from word where trailer = ?", ("  \u05c0 ",)).fetchone()[0]
    if doubled:
        raise SystemExit(f"double-spaced paseq trailers: {doubled}")
    print(f"dist ok: {verses} verses, {words} words, {seen_alts} alternatives, UXLC rows {diffs}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
