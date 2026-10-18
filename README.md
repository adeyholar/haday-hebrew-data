# HaDay Hebrew Bible dataset

Reusable text of the Hebrew Bible for HaDay. Every written mark is kept: vowels, dagesh, shin and sin dots, the te‘amim, meteg, maqaf, paseq, and sof pasuq. A word is not one string. The accents and the rhythm are their own fields.

**As built:** [docs/ASBUILT.md](docs/ASBUILT.md). Read that before changing the builder. It is what this release actually does, including the gaps.

The printed BHS scan is not a source. Nothing in this repository is taken from it.

## Sources

| Role | Pin |
|---|---|
| Open Scriptures Hebrew Bible, `wlc/*.xml` | commit `3d15126fb1ef74867fc1434be1942e837932691f` |
| Unicode/XML Leningrad Codex | UXLC 2.6, build 27.7, zip SHA-256 `423469bdcc4bfe36d7666f8e76fbd02c1674d77469093c06cee9779c0fba83e3` |

The mirrors are in `sources/`. A build fails the tests if the word counts move. Re-pinning is a deliberate change.

## Build

```bash
python -m builder.build --out dist
python -m unittest discover -s tests
```

`dist/` holds `hebrew-bible.sqlite`, one JSON file per chapter, the accent table, and the build reports. The reports are the review queue: accent unknowns, rhythm mismatches, stress defaults, and UXLC differences. OSHB is never overwritten to match UXLC.

## Attribution

Hebrew text: Westminster Leningrad Codex (public domain), as encoded by the Open Scriptures Hebrew Bible. Lemma and morphology: "Original work of the Open Scriptures Hebrew Bible available at https://github.com/openscriptures/morphhb", licensed CC BY 4.0. Text cross-checked against the Unicode/XML Leningrad Codex: UXLC 2.6 (27.7), Tanach.us Inc., West Redding, CT, USA, Oct 2026.

The UXLC text is not called WLC. The ETCBC BHSA layer is not in this build.
