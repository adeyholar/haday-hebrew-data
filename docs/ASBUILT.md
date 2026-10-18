# HaDay Hebrew Bible dataset — as built

Living picture of **what this dataset is today**. Not the class site. Not a wish list.

| | |
|---|---|
| **Snapshot** | 18 October 2026, after the Dev Desk review of v1.0.0 |
| **Repo** | https://github.com/adeyholar/haday-hebrew-data (`main`). Dataset version **1.1.0**. |
| **Release** | v1.0.0 was the first cut. v1.1.0 is the review fix. The class site is still not wired to either. |
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

Hashes are in `sources/SHA256SUMS`. A new UXLC build is a deliberate re-pin, then every test again. Do not call the UXLC text “WLC”.

## How to rebuild

```bash
python -m builder.build --out dist
python -m unittest discover -s tests
```

No network is required. The pins are already in `sources/`. Do not call Unicode NFC or NFD on the Hebrew. `builder/` has no `unicodedata.normalize` and no `str.normalize`.

`dist/` is not in git. The release holds the gzip of the SQLite file and a tar of the chapter JSON plus the review reports.

## What a word is

SQLite table `word`. The chapter JSON (`dist/json/<OSIS>/<chapter>.json`) is the slice the app is meant to load. Qere words are in SQLite and not in the chapter JSON.

| Field | What it is |
|---|---|
| `id` | OSHB word id, for example `01xeN`. Never renumber. |
| `surface_src` | The OSHB word with the morpheme slash removed. No reordering. |
| `surface` | The same marks, in HaDay order: shin/sin dot, dagesh, rafe, vowel, meteg, accents (accents keep their own order), upper/lower dots. |
| `pointed` | `surface` without the accents and without meteg. Vowels, dagesh, and shin/sin dots stay. |
| `consonants` | Letters only. |
| `morphemes` | The slash pieces, so בראשית is `בְּ` + `רֵאשִׁ֖ית`. |
| `trailer` | What follows the word: a space, maqaf `־`, paseq `׀`, sof pasuq `׃`, or nothing. |
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
| Main words | 305,507 |
| Qere words | 1,278 |
| Verses with sof pasuq | 23,192 (21 verses have none) |
| Unknown accent code points | 0 |

The spec’s arithmetic “306,774 words” does not add up (305,507 + 1,278 = 306,785). Trust the pin. The code-point totals in `tests/expected-histogram.json` are the pin, not the rounded figures in the spec.

Nine qere words have no ketiv in front of them (OSHB calls them adaptations). They are stored. Six variant notes have no `<w>` and are not words.

## Rhythm

Prose agrees with OSHB’s `n` on **99.69%** of verses (18,689 / 18,748). That clears the 98% bar. Genesis stays inside that bar. Poetry (Psalms, Proverbs, Job) agrees on **96.1%** (4,291 / 4,465). That clears the 95% bar. The poetic path follows Wickes as recorded in the OSHB accent catalog: the rightmost disjunctive in a domain is the near divider, a stronger one to its left is the remote divider, and a weaker one nests under the near divider. With no atnach, a revia gadol takes number 1 and ole veyored stays 2. With neither, ole veyored takes 1. A merkha after a word that already holds both ole and yored is not a second ole veyored.

A ketiv is read from its qere for accents, stress, and the pause tree. The written consonants stay the ketiv. Where they disagree with OSHB, `rhythm_path` stays OSHB’s value. The computed path is `rhythm_path_computed` in SQLite. Every miss is in `build-report/rhythm-mismatch.csv`.

Path numbers: silluq is `0`, atnach is `1`, ole veyored is `2`. A poetic verse with ole and no atnach gives `1` to the strongest king after the ole. A prose verse with no atnach does not.

Prose legarmeh is munach followed by paseq only. Mahpakh or qadma followed by paseq stays conjunctive. Poetry still treats munach, mehuppakh, and azla before paseq as legarmeh, because dropping that made the poetry match worse, not better.

A verse whose only pause is the final silluq still names silluq as its governor. If the last word has no U+05BD, the silluq row is marked `inferred` and the text is not given a fake meteg.

## Stress

Holam male (וֹ) and shureq (וּ) belong to the consonant before the vav. אוֹר, טוֹב, תְּהוֹם, and רוּחַ are one syllable from the end when the accent is on that consonant. After that fix, `default-ultima` is 23,263 words. That list is still for Dev Desk. The old 24,363 count was the bug.

## Stress and the other reports

`build-report/stress-review.csv` lists words whose stress fell back to the last syllable (`default-ultima`). Re-read it from the v1.1.0 build. The v1.0.0 count of 24,363 was wrong because וֹ and וּ were counted as their own syllables.

`build-report/legarmeh.csv` lists every munach, and in poetry every mehuppakh or azla, that is followed by paseq.

`build-report/uxlc-diff.csv` from v1.1.0 is the triage file. UXLC `<x>` markers are not part of the word. Doubled pashta and UXLC’s CGJ are normalized for the comparison only, and OSHB is not changed. The report is about 1,171 rows: about 1,139 mark differences, 26 tokenization differences, and 6 letter differences. The letter rows include 2 Samuel 13:37, 2 Samuel 14:7, Ezekiel 16:36, Amos 7:2, and 2 Chronicles 27:4. Dev Desk has not signed this list off.

`build-report/accent-unknown.csv` is empty.

The chapter JSON nests `qere` under the ketiv, with `kq_group`. Alternative accent readings and the exegesis notes are in the SQLite `word_alt` table and on the word as `alternatives`.

## What the class app still does

Nothing in `adeyholar/haday` reads this dataset. Listen → Tanakh still uses `public/tanakh/books/*.json`. Grading still uses `normalizeHebrewFull`, which throws the accents and the meteg away. That is still correct for the vocabulary games. It is not correct for a strict “every dot counts” reading grade. The shared function for that grade is `packages/canon/canon.ts` here and `builder/canon.py`. They are the same order. The app does not import them yet.

Do not replace the Tanakh JSON in the app by copying `surface` over the old files in the same pull request as a player change. The next step in the spec is a flagged reader for Genesis 1–3 only.

## Do not reverse

- Do not strip a mark to store the text.
- Do not run Unicode NFC or NFD on these strings.
- Do not build from the BHS scan, its OCR, or the BHS apparatus.
- Do not overwrite an OSHB word because UXLC differs. A correction is a patch file with a reason.
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
| `builder/uxlc.py` | Verse and word alignment. Report only. |
| `builder/build.py` | SQLite, chapter JSON, manifest, reports. |
| `builder/books.py` | The 39 books in Tanakh order, and which Job verses are prose. |
| `tests/test_accept.py` | Genesis 1:1, the five stress words, the word counts, Genesis rhythm ≥ 98%. |
| `packages/canon/canon.ts` | The same mark order, for the app later. Not imported by the class site. |

Job 3:2–42:6 is poetic. Job 1:1–3:1 and Job 42:7–17 are prose. Psalms and Proverbs are poetic. Everything else is prose.
