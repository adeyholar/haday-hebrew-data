"""Build the HaDay Hebrew Bible dataset from the pinned sources."""

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from builder.accents import HEBREW, POETIC, PROSE
from builder.books import BOOKS
from builder.oshb import load_oshb
from builder.uxlc import compare, load_uxlc

VERSION = "1.0.0"
OSHB_COMMIT = "3d15126fb1ef74867fc1434be1942e837932691f"
UXLC_SHA = "423469bdcc4bfe36d7666f8e76fbd02c1674d77469093c06cee9779c0fba83e3"
ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _json_ready(word: dict) -> dict:
    return {
        "id": word["id"],
        "pos": word["pos"],
        "unit": word.get("unit"),
        "surface": word["surface"],
        "trailer": word["trailer"],
        "pointed": word["pointed"],
        "consonants": word["consonants"],
        "morphemes": word["morphemes"],
        "accents": word.get("accents") or [],
        "meteg": word.get("meteg") or [],
        "stress": word.get("stress"),
        "kq_role": word.get("kq_role"),
        "lemma": word.get("lemma") or "",
        "morph": word.get("morph_oshb") or "",
        "rhythm_path": word.get("rhythm_path"),
    }


def _accent_rows() -> list[dict]:
    rows = []
    for system, table in (("prose", PROSE), ("poetic", POETIC)):
        for cp, (name, kind, level, placement) in sorted(table.items()):
            rows.append(
                {
                    "system": system,
                    "cp": f"U+{cp:04X}",
                    "context": "",
                    "name": name,
                    "name_he": HEBREW.get(name, ""),
                    "kind": kind,
                    "level": level,
                    "placement": placement,
                }
            )
    return rows


def build(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    report = out / "build-report"
    report.mkdir(exist_ok=True)
    json_root = out / "json"
    json_root.mkdir(exist_ok=True)
    books = load_oshb(ROOT / "sources" / "morphhb-wlc")
    diffs = compare(books, load_uxlc(ROOT / "sources" / "Tanach.xml.zip"))
    db_path = out / "hebrew-bible.sqlite"
    if db_path.exists():
        db_path.unlink()
    db = sqlite3.connect(db_path)
    db.executescript(
        """
        create table meta (key text primary key, value text);
        create table book (osis text primary key, ord integer, name_en text, name_he text, section text, uxlc_file text, default_system text);
        create table verse (ref text primary key, book text, chapter integer, verse integer, system text, text_src text, text text, word_count integer, unit_count integer, para_after text, has_sof_pasuq integer, rhythm text, uxlc_status text);
        create table word (id text primary key, ref text, pos integer, unit integer, surface_src text, surface text, morphemes text, trailer text, consonants text, pointed text, accents text, main_accent text, meteg text, stress text, kq_role text, kq_group text, special text, lemma text, morph_oshb text, oshb_n text, rhythm_path text, rhythm_path_computed text, uxlc text);
        create table uxlc_diff (ref text, word_id text, oshb text, uxlc text, diff_type text, codepoints text);
        create index word_ref_pos on word(ref, pos);
        create index word_lemma on word(lemma);
        create index word_consonants on word(consonants);
        create index word_morph on word(morph_oshb);
        create index verse_place on verse(book, chapter);
        """
    )
    built = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = {
        "dataset_version": VERSION,
        "built_at": built,
        "oshb_commit": OSHB_COMMIT,
        "uxlc_version": "2.6",
        "uxlc_build": "27.7",
        "uxlc_sha256": UXLC_SHA,
        "bhsa_version": "",
        "normalization_version": "1",
        "accent_table_version": "1",
    }
    db.executemany("insert into meta values (?, ?)", meta.items())
    db.executemany(
        "insert into book values (?, ?, ?, ?, ?, ?, ?)",
        [(osis, index, en, he, section, uxlc, system) for index, (osis, en, he, section, uxlc, system) in enumerate(BOOKS, start=1)],
    )
    histogram: Counter[str] = Counter()
    unknown_rows = []
    stress_rows = []
    rhythm_rows = []
    legarmeh_rows = []
    no_sof = []
    prose_n = prose_ok = poetic_n = poetic_ok = 0
    for book in books:
        osis = book["osis"]
        by_chapter: dict[int, list[dict]] = {}
        for verse in book["verses"]:
            by_chapter.setdefault(verse["chapter"], []).append(verse)
            if not verse["has_sof_pasuq"]:
                no_sof.append(verse["ref"])
            matched = True
            saw = False
            for word in verse["words"]:
                if word.get("kq_role") == "qere":
                    continue
                for ch in word["surface_src"]:
                    histogram[f"U+{ord(ch):04X}"] += 1
                for cp in word.get("unknown_accents") or []:
                    unknown_rows.append((verse["ref"], word["id"], f"U+{cp:04X}"))
                if word.get("stress") and word["stress"].get("source") == "default-ultima":
                    stress_rows.append((verse["ref"], word["id"], word["surface"]))
                for accent in word.get("accents") or []:
                    if accent["name"] == "legarmeh":
                        legarmeh_rows.append((verse["ref"], word["id"], word["surface"]))
                if word.get("rhythm_match") is True or word.get("rhythm_match") is False:
                    saw = True
                    if word["rhythm_match"] is False:
                        matched = False
                        rhythm_rows.append((verse["ref"], word["id"], word.get("oshb_n"), word.get("rhythm_path_computed")))
            if saw:
                if verse["system"] == "poetic":
                    poetic_n += 1
                    poetic_ok += int(matched)
                else:
                    prose_n += 1
                    prose_ok += int(matched)
            db.execute(
                "insert into verse values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    verse["ref"],
                    verse["book"],
                    verse["chapter"],
                    verse["verse"],
                    verse["system"],
                    verse["text_src"],
                    verse["text"],
                    verse["word_count"],
                    verse["unit_count"],
                    verse["para_after"],
                    verse["has_sof_pasuq"],
                    json.dumps(verse["rhythm"], ensure_ascii=False),
                    verse["uxlc_status"],
                ),
            )
            db.executemany(
                "insert into word values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        word["id"],
                        verse["ref"],
                        word["pos"],
                        word.get("unit"),
                        word["surface_src"],
                        word["surface"],
                        json.dumps(word["morphemes"], ensure_ascii=False),
                        word["trailer"],
                        word["consonants"],
                        word["pointed"],
                        json.dumps(word.get("accents") or [], ensure_ascii=False),
                        word.get("main_accent"),
                        json.dumps(word.get("meteg") or [], ensure_ascii=False),
                        json.dumps(word.get("stress"), ensure_ascii=False),
                        word.get("kq_role"),
                        word.get("kq_group"),
                        json.dumps(word.get("special") or [], ensure_ascii=False),
                        word.get("lemma"),
                        word.get("morph_oshb"),
                        word.get("oshb_n"),
                        word.get("rhythm_path"),
                        word.get("rhythm_path_computed"),
                        word.get("uxlc"),
                    )
                    for word in verse["words"]
                ],
            )
        for chapter, verses in by_chapter.items():
            folder = json_root / osis
            folder.mkdir(exist_ok=True)
            payload = {
                "book": osis,
                "chapter": chapter,
                "dataset_version": VERSION,
                "verses": [
                    {
                        "ref": verse["ref"],
                        "system": verse["system"],
                        "para_after": verse["para_after"],
                        "text": verse["text"],
                        "rhythm": verse["rhythm"],
                        "words": [_json_ready(word) for word in verse["words"] if word.get("kq_role") != "qere"],
                    }
                    for verse in verses
                ],
            }
            (folder / f"{chapter}.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    db.executemany(
        "insert into uxlc_diff values (?, ?, ?, ?, ?, ?)",
        [(row["ref"], row["word_id"], row["oshb"], row["uxlc"], row["diff_type"], json.dumps(row["codepoints"], ensure_ascii=False)) for row in diffs],
    )
    db.commit()
    db.close()

    def dump(path: Path, header: list[str], rows: list[tuple]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

    dump(report / "accent-unknown.csv", ["ref", "word_id", "cp"], unknown_rows)
    dump(report / "stress-review.csv", ["ref", "word_id", "surface"], stress_rows)
    dump(report / "rhythm-mismatch.csv", ["ref", "word_id", "oshb_n", "computed"], rhythm_rows)
    dump(report / "legarmeh.csv", ["ref", "word_id", "surface"], legarmeh_rows)
    dump(report / "uxlc-diff.csv", ["ref", "word_id", "oshb", "uxlc", "diff_type"], [(r["ref"], r["word_id"], r["oshb"], r["uxlc"], r["diff_type"]) for r in diffs])
    (report / "no-sof-pasuq.json").write_text(json.dumps(no_sof, ensure_ascii=False, indent=2), encoding="utf-8")
    accents = _accent_rows()
    (json_root / "accents.json").write_text(json.dumps(accents, ensure_ascii=False, indent=2), encoding="utf-8")
    (json_root / "books.json").write_text(
        json.dumps(
            [
                {"osis": osis, "ord": index, "name_en": en, "name_he": he, "section": section, "default_system": system}
                for index, (osis, en, he, section, _uxlc, system) in enumerate(BOOKS, start=1)
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    counts = {
        "books": len(books),
        "verses": sum(len(book["verses"]) for book in books),
        "prose_rhythm": [prose_ok, prose_n, round(prose_ok / prose_n, 4) if prose_n else 0],
        "poetic_rhythm": [poetic_ok, poetic_n, round(poetic_ok / poetic_n, 4) if poetic_n else 0],
        "uxlc_diffs": len(diffs),
        "unknown_accents": len(unknown_rows),
        "stress_default_ultima": len(stress_rows),
        "no_sof_pasuq": len(no_sof),
    }
    files = {}
    for path in sorted(json_root.rglob("*")):
        if path.is_file():
            files[str(path.relative_to(out))] = _sha(path)
    files["hebrew-bible.sqlite"] = _sha(db_path)
    manifest = {
        "dataset_version": VERSION,
        "built_at": built,
        "oshb_commit": OSHB_COMMIT,
        "uxlc_version": "2.6",
        "uxlc_build": "27.7",
        "uxlc_sha256": UXLC_SHA,
        "counts": counts,
        "attribution": "Hebrew text: Westminster Leningrad Codex (public domain), as encoded by the Open Scriptures Hebrew Bible. Lemma and morphology: Original work of the Open Scriptures Hebrew Bible available at https://github.com/openscriptures/morphhb, licensed CC BY 4.0. Text cross-checked against the Unicode/XML Leningrad Codex: UXLC 2.6 (27.7), Tanach.us Inc., West Redding, CT, USA, Oct 2026.",
        "sha256": files,
    }
    (json_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    # The manifest hashes itself last, after the file exists, and records every other file.
    files["json/manifest.json"] = _sha(json_root / "manifest.json")
    manifest["sha256"] = files
    (json_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (report / "summary.json").write_text(json.dumps({"counts": counts, "histogram_size": len(histogram)}, indent=2), encoding="utf-8")
    (ROOT / "tests" / "expected-histogram.json").write_text(json.dumps(dict(sorted(histogram.items())), indent=2), encoding="utf-8")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "dist"))
    args = parser.parse_args()
    counts = build(Path(args.out))
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
