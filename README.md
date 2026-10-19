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

## Re-pin

1. Replace `sources/morphhb-wlc/*.xml` or `sources/Tanach.xml.zip` with the new pin. Do not take anything from a BHS scan.
2. `cd sources && sha256sum morphhb-wlc/*.xml Tanach.xml.zip > SHA256SUMS` and sort that file the way the old one is sorted.
3. Write the new OSHB commit in `builder/build.py` (`OSHB_COMMIT`) and in this README. For a new UXLC zip, write the new SHA-256 there too.
4. Run `python -m unittest discover -s tests`. If a count moved, change the test on purpose and say why in the as-built. Do not let the build rewrite `tests/expected-histogram.json`.
5. Run `python -m builder.build --out dist` and read `dist/build-report/summary.json` before tagging a release.

## Build

```bash
python -m builder.build --out dist
python -m unittest discover -s tests
```

`dist/` holds `hebrew-bible.sqlite`, one JSON file per chapter, the accent table, and the build reports. The reports are the review queue: accent unknowns, rhythm mismatches, stress defaults, and UXLC differences. OSHB is never overwritten to match UXLC.

A release tar includes this README, `LICENSE-DATA.md` and `LICENSE` next to the data. The database is a separate `.sqlite.gz`, and `SHA256SUMS` covers all three files. Release assets are made by `scripts/package.sh`. The tag workflow that runs it is in `docs/ci/release.yml` until it is installed into `.github/workflows/` (see `docs/ci/README.md`); it refuses a tag whose commit is behind `main` or whose version differs from `sources/PINS.txt`. The code is MIT (`LICENSE`); the data terms are in `LICENSE-DATA.md`.

## Attribution

Hebrew text: Westminster Leningrad Codex (public domain), as encoded by the Open Scriptures Hebrew Bible. Lemma and morphology: "Original work of the Open Scriptures Hebrew Bible available at https://github.com/openscriptures/morphhb", licensed CC BY 4.0. Text cross-checked against the Unicode/XML Leningrad Codex: UXLC 2.6 (27.7), Tanach.us Inc., West Redding, CT, USA, Oct 2026.

The UXLC text is not called WLC. The ETCBC BHSA layer is not in this build.
