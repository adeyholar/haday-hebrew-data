# HaDay Hebrew Bible dataset — as built

Living picture of **what this dataset is today**. Not the class site. Not a wish list.

| | |
|---|---|
| **Snapshot** | 18 October 2026, after the Dev Desk v1.1.2 fixes (Re-review 6) |
| **Repo** | https://github.com/adeyholar/haday-hebrew-data (`main`). Dataset version **1.1.3**. |
| **Release** | v1.0.0 was the first cut. v1.1.0 was the first review fix. v1.1.1 is the poetic rhythm, stress, and trailer fix. v1.1.2 applies the signed UXLC triage, layered by class. v1.1.3 pins the triage and checks every source hash before a build, with no data change. Nothing on the class site reads this build yet (see the next row). |
| **Spec** | https://app.notion.com/p/3fd058f607b1816e8bcbde360c1a546d |
| **Class site** | Not wired. https://hebrewmentor.haday.app still reads `public/tanakh/books/*.json`, which drops the accents. |
| **BHSA** | Off. Do not turn it on without the license note in the spec. |

If this file and the Notion spec disagree about a rule, the spec wins. If the spec disagrees with the code, correct the spec the same day.

## What was built

One record per word of the Hebrew Bible, from the pinned Open Scriptures Hebrew Bible, with every written mark kept. The verse also has a pause tree (the accent rhythm).

A quiz may hide the accents by reading the `pointed` field. It must not strip marks off `surface` and then save that stripped string back.

The BHS scan on the Chairman’s PC was not opened, not copied, and not used. The OCR of that scan has no accents.

## Sources (do not float)

| Role | What is pinned | Where |
|---|---|---|
| Text, word ids, lemma, morphology, accent paths | OSHB `morphhb` commit `3d15126fb1ef74867fc1434be1942e837932691f` | `sources/morphhb-wlc/*.xml` |
| Cross-check only | UXLC 2.6, build 27.7, zip SHA-256 `423469bdcc4bfe36d7666f8e76fbd02c1674d77469093c06cee9779c0fba83e3` | `sources/Tanach.xml.zip` |

Hashes are in `sources/SHA256SUMS`, including the signed triage `sources/uxlc-triage-v1.1.1.csv`. `python -m builder.build` checks every file against it before it reads anything, and stops if a file is changed, missing, or not listed. `.gitattributes` marks `sources/** -text`, so a Windows checkout with `core.autocrlf` does not rewrite the XML or CSV line endings. A new UXLC build or a triage edit is a deliberate re-pin, then every test again. Do not call the UXLC text “WLC”.

## How to rebuild

```bash
python -m builder.build --out dist
python -m unittest discover -s tests
```

No network is required. The pins are already in `sources/`. Do not call Unicode NFC or NFD on the Hebrew. `builder/` has no `unicodedata.normalize` and no `str.normalize`.

`dist/` is not in git. The release holds the gzip of the SQLite file, a tar of the chapter JSON, a tar of the review reports, and a `SHA256SUMS` for the three. README.md, LICENSE-DATA.md and LICENSE are inside both tars.

**Pins.** `sources/PINS.txt` is the one place for the dataset version, the OSHB commit, the UXLC version, build and hash, and the source file names (`builder/pins.py` reads it). The build fails if its UXLC hash disagrees with `SHA256SUMS`.

**Reproducible.** `built_at` is `SOURCE_DATE_EPOCH` if set, otherwise the builder commit's date. The same commit gives the same SQLite file and JSON byte for byte (checked locally; `docs/ci/build.yml` adds the two-build check to CI). `scripts/package.sh dist release` makes the release assets with fixed tar order, owner and mtime and `gzip -n`.

**Releasing.** Set `DATASET_VERSION` in `PINS.txt`, write `docs/releases/v<version>.md`, merge to `main`, then tag `v<version>` on `main`. The tag workflow (`docs/ci/release.yml`, waiting to be installed in `.github/workflows/` by someone with a workflow-scoped token) checks the tag matches the version and is not behind `main`, runs the tests, builds, runs `check_dist` and the canon parity check, packages, and uploads the assets and `SHA256SUMS`. Until it is installed, build from the tagged commit with `SOURCE_DATE_EPOCH` set to its commit date, run `check_dist`, and upload what `scripts/package.sh` writes, including `SHA256SUMS`.

**Errors.** The builder raises `builder.errors.BuildError` subclasses (`SourceMismatch`, `PinError`, `TriageError`, `MarkError`); only the command line turns them into an exit code.

## What a word is

SQLite table `word`. Indexes: `word(ref, pos)`, `word(lemma)`, `word(consonants)`, `word(morph_oshb)`, `verse(book, chapter)`, `accent(word_id)`, `word_alt(host_id)`, `unit(ref)`. The chapter JSON (`dist/json/<OSIS>/<chapter>.json`) is the slice the app is meant to load. Qere words are rows of their own in SQLite. In the chapter JSON they are nested under the ketiv as `qere`.

| Field | What it is |
|---|---|
| `id` | OSHB word id, for example `01xeN`. Never renumber. |
| `surface_src` | The OSHB word with the morpheme slash removed. No reordering. |
| `surface` | The same marks, in HaDay order: shin/sin dot, dagesh, rafe, vowel, meteg, accents (accents keep their own order), upper/lower dots. |
| `pointed` | `surface` without the accents and without meteg. Vowels, dagesh, and shin/sin dots stay. |
| `consonants` | Letters only. |
| `morphemes` | The slash pieces, so בראשית is `בְּ` + `רֵאשִׁ֖ית`. They are in the same mark order as `surface` and join back to it exactly. On a reviewed word they are cut from the final `surface` at the OSHB morpheme boundaries. Where that cut cannot be made, the word keeps one piece and its id is listed in `build-report/summary.json` under `morpheme_fallbacks`. |
| `review`, `review_class` | Set only on a word the signed triage changed. `review_class` is `wlc_error`, `word_division`, `exegesis_join`, or `oshb_convention`. |
| `trailer` | What follows the word: a space, maqaf `־`, paseq `׀`, sof pasuq `׃`, or nothing. |
| `trailers` | JSON only. The trailer pieces in source order, for example `[" "]`, `["־"]`, or `[" ׀ "]`. `trailer` is their join. A word that ends the verse with sof pasuq keeps `׃` here. An exegesis split has `[]` and `trailer` `""`. |
| `accents` | Each te‘am, with its name, level, and the consonant it sits on (`letter_index`, counting from 0). |
| `meteg` | Each U+05BD. On the last word of the verse the rightmost one is `silluq`. The others are `meteg`. |
| `stress` | `{letter_index, syll_from_end, source}`. Empty on a word that is only leaning on the next word through a maqaf. |
| `lemma`, `morph` | OSHB. SQLite calls the morph column `morph_oshb`. |
| `rhythm_path` | OSHB’s `n` path when OSHB wrote one. Otherwise the path this builder computed. |
| `kq_role` | Empty, `ketiv`, or `qere`. |

`letter_index` is the consonant, starting at 0. In בראשית the tipcha is on ש, index 3. The sample in the spec that said 4 was an illustration, not the count.

## Genesis 1:1 (the acceptance verse)

Seven words. Six accents in the accent range, in this order: tipcha, munach, atnach, merkha, tipcha, merkha. One silluq (the meteg on אָ in הָאָֽרֶץ). One sof pasuq. Two shin dots. The pause tree splits at the atnach, unit 3. OSHB paths on the disjunctive words: `1.0`, `1`, `0.0`, `0`.

Stress checks that must keep passing:

| Word | Where | Expect |
|---|---|---|
| בְּרֵאשִׁ֖ית | Gen 1:1 | shin, one syllable from the end, source `accent` |
| הָאָֽרֶץ | Gen 1:1 | silluq on alef, two from the end |
| וְהָאָ֗רֶץ | Gen 1:2 | revia on alef, two from the end |
| תֹ֨הוּ֙ | Gen 1:2 | doubled pashta on tav, two from the end, source `doubled`. OSHB has no dagesh in תֹהוּ |
| וַיֹּאמֶר | Gen 1:3 | stress on yod, two from the end |

OSHB writes a doubled pashta as qadma on the stressed letter and pashta on the last letter. UXLC writes two pashta marks. We keep the OSHB spelling and label the stress `doubled`.

## Counts from this pin

| | |
|---|---|
| Books | 39, Hebrew canon order |
| Verses | 23,213 |
| Main words | 305,501 (305,507 in v1.1.1, before the L word divisions) |
| Qere words | 1,278 |
| Verses with sof pasuq | 23,192 (21 verses have none) |
| Unknown accent code points | 0 |

The spec’s arithmetic “306,774 words” does not add up (305,507 + 1,278 = 306,785). Trust the pin. The code-point totals in `tests/expected-histogram.json` are the pin, not the rounded figures in the spec.

Nine qere words have no ketiv in front of them (OSHB calls them adaptations). They are stored. Six variant notes have no `<w>` and are not words.

## Rhythm

Prose agrees with OSHB’s `n` on **99.38%** of verses (18,632 / 18,748). That clears the 98% bar. Genesis stays inside that bar. Poetry (Psalms, Proverbs, Job) agrees on **95.9%** (4,282 / 4,465). That clears the 95% bar. Psalms is 94.3%. Every verse that agrees less than in v1.1.1 holds a WLC-error correction: OSHB’s `n` was written for the WLC accents, so it no longer describes the corrected word. On the verses the review did not touch, the figures are the v1.1.1 ones exactly (prose 99.80%, poetry 96.36%, Psalms 94.95%). The poetic path follows Wickes as recorded in the OSHB accent catalog: the rightmost disjunctive in a domain is the near divider, a stronger one to its left is the remote divider, and a weaker one nests under the near divider. With no atnach, a revia gadol takes number 1 and ole veyored stays 2. With neither, ole veyored takes 1. A merkha after a word that already holds both ole and yored is not a second ole veyored.

A ketiv is read from its qere for accents, stress, and the pause tree. The written consonants stay the ketiv. Where they disagree with OSHB, `rhythm_path` stays OSHB’s value. The computed path is `rhythm_path_computed` in SQLite. Every miss is in `build-report/rhythm-mismatch.csv`.

Path numbers: silluq is `0`, atnach is `1`, ole veyored is `2` when atnach is there. With no atnach, a revia gadol takes `1` and ole stays `2`. With neither, ole takes `1`. The poetic `verse.rhythm` tree is still the older level split. Use `rhythm_path` and `rhythm_path_computed` for poetry. Do not treat the tree as the same thing.

Prose legarmeh is munach followed by paseq only. Mahpakh or qadma followed by paseq stays conjunctive. Poetry legarmeh is mehuppakh or azla followed by paseq. Poetic munach followed by paseq stays conjunctive. A revia gadol just before ole veyored is `revia_qatan` on both `main_accent` and the accent row.

A verse with sof pasuq names silluq as its governor. If that last word has no U+05BD, the silluq row is marked `inferred` and the text is not given a fake meteg. A verse with no sof pasuq, such as Numbers 25:19, keeps its real governor. It is not given a silluq.

## Stress

Holam male (וֹ) and shureq (וּ) belong to the consonant before the vav. אוֹר, טוֹב, תְּהוֹם, and רוּחַ are one syllable from the end when the accent is on that consonant. A meteg on shewa is not the tone. A prepositive mark (dechi, telisha gedola, geresh muqdam) is not the tone. Yetiv is, because its tone is the first syllable. A silent aleph is not a syllable of its own. When an aleph has no vowel and the letter before it has none either, that letter owns a following וּ or וֹ, so יְראוּ is one syllable.

A word whose only accent is prepositive (pashta, telisha gedola, dechi, geresh muqdam) has no tone mark. If it is a segolate (closed last syllable, segol or a guttural patach after segol, tsere, holam, qamats, or patach), the stress is the penult and the source is `segolate`. אֶ֝בֶן in Prov 26:27 is two from the end. A dagesh in the last onset, a final ה or י, and the -כֶם/-הֶם suffixes are not segolates. Anything else still falls back to `default-ultima`.

## Stress and the other reports

`build-report/stress-review.csv` lists words whose stress fell back to the last syllable (`default-ultima`). Re-read it from the v1.1.0 build. The v1.0.0 count of 24,363 was wrong because וֹ and וּ were counted as their own syllables.

`build-report/legarmeh.csv` lists every munach, and in poetry every mehuppakh or azla, that is followed by paseq.

`build-report/uxlc-diff.csv` is what the signed triage did not change. The builder applies `sources/uxlc-triage-v1.1.1.csv` from its `decision` column only (`override`, `uncertain`, `optional`, `divide`, `join`, `compare`, `leave`). A join row that also takes UXLC's signed mark correction (only Ps 106:1) has `apply_uxlc_marks` = `yes`. The `class` column only names `review_class`; `recommended_action` and `verdict` are for people, and rewording them changes nothing. Any other `decision` or `apply_uxlc_marks` value stops the build. By class:

| Triage class | Rows | What the build does |
|---|---|---|
| WLC error | 567 | `surface` is the UXLC reading. `review_class` is `wlc_error`. |
| Real unresolved (L uncertain) | 146 | Main text stays OSHB. The UXLC reading is a `word_alt` row, `note_type` `uxlc_uncertain`, `uncertain` 1. |
| Editorial, diplomatic layer | 98 | Main text stays OSHB. The UXLC reading is a `word_alt` row, `note_type` `uxlc_diplomatic`, `opt_in` 1. An app shows it only if the reader asks. |
| Word division (L) | 10 | Two words become one or one becomes two. `review_class` is `word_division`. |
| OSHB exegesis split | 6 | Both words stay. The space the builder used to insert is dropped. `review_class` is `exegesis_join`. |
| Word division, L uncertain | 1 | Ezra 3:5 is not merged. It keeps the two OSHB words, with no space between them because OSHB writes none. |

`surface_src` and `verse.text_src` are always the OSHB characters and the OSHB word division. Only `surface` and `verse.text` change. Galgal is `galgal` and conjunctive in both systems: U+05AA in prose, U+05A2 in poetry. U+05AA and U+05A2 compare as the same mark. A double accentuation stays on `word_alt` and is not a diff. Rows marked none or document are not changed. The diff report should be 44 rows (Gen 14:17 אַחֲרֵ֣י is listed now, because the builder no longer repaints a word the triage did not sign). Do not overwrite `surface_src` to hide the OSHB pin.

`build-report/accent-unknown.csv` is empty.

The chapter JSON nests `qere` under the ketiv, with `kq_group`. Alternative accent readings and the exegesis notes are in the SQLite `word_alt` table and on the word as `alternatives`.

## What the class app still does

Nothing in `adeyholar/haday` reads this dataset. Listen → Tanakh still uses `public/tanakh/books/*.json`. Grading still uses `normalizeHebrewFull`, which throws the accents and the meteg away. That is still correct for the vocabulary games. It is not correct for a strict “every dot counts” reading grade. The shared function for that grade is `packages/canon/canon.ts` here and `builder/canon.py`. They are the same order. The app does not import them yet.

Do not replace the Tanakh JSON in the app by copying `surface` over the old files in the same pull request as a player change. The next step in the spec is a flagged reader for Genesis 1–3 only.

## Do not reverse

- Do not strip a mark to store the text.
- Do not run Unicode NFC or NFD on these strings.
- Do not build from the BHS scan, its OCR, or the BHS apparatus.
- Do not overwrite `surface_src`. A correction changes `surface` and records the review row. The OSHB characters stay the pin.
- Do not merge BHSA into this public file. Its license is not cleared.
- Do not point the live Tanakh player at this dataset until the flagged Genesis 1–3 reader has been reviewed.

## Where the code lives

| File | Owns |
|---|---|
| `builder/canon.py` | Mark order. `pointed` and `consonants` are derived and never written back over `surface`. |
| `builder/accents.py` | Prose and poetic accent tables, silluq, mayela, legarmeh. |
| `builder/rhythm.py` | Pause tree and the `0` / `1` / `2` paths. |
| `builder/stress.py` | Which consonant is stressed, and `syll_from_end`. |
| `builder/oshb.py` | OSIS reader, ketiv/qere, units, maqaf chains. |
| `builder/uxlc.py` | Verse and word alignment. Report only. Comparison treats U+05AA as U+05A2, and a `word_alt` row as already stored. |
| `builder/overrides.py` | Applies `sources/uxlc-triage-v1.1.1.csv` by class: corrections onto `surface`, uncertain and diplomatic readings onto `word_alt`. |
| `builder/build.py` | SQLite, chapter JSON, manifest, reports. Checks the source hashes first. |
| `builder/pins.py`, `builder/sources.py` | `PINS.txt` and the `SHA256SUMS` check. |
| `builder/errors.py` | The exceptions the builder raises. |
| `scripts/package.sh` | Release assets and their `SHA256SUMS`. |
| `packages/canon/parity.ts`, `tests/test_canon_parity.py` | canon.ts against canon.py on every distinct string in the corpus and UXLC (over 100,000). Runs in the unit tests; needs Node 22.6+, and fails on CI without it. `tests/canon_parity.py` does the same from a built `dist/`. |
| `builder/books.py` | The 39 books in Tanakh order, and which Job verses are prose. |
| `tests/test_accept.py` | Genesis 1:1, the five stress words, the word counts, Genesis rhythm ≥ 98%. |
| `tests/test_review_policy.py` | The triage class policy, morphemes against surface, `text_src` against the OSHB XML for every verse, the word-division spaces, galgal, and the segolate and aleph stress words. |
| `tests/check_dist.py` | Every chapter JSON against SQLite, word by word, and the words rebuilding each verse. |
| `packages/canon/canon.ts` | The same mark order, for the app later. Not imported by the class site. |

Job 3:2–42:6 is poetic. Job 1:1–3:1 and Job 42:7–17 are prose. Psalms and Proverbs are poetic. Everything else is prose.
