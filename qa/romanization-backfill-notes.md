# Romanization backfill — 2026-09-14

Scope: all 4 books (foundation, intermediate, advanced, vocabulary-7000-words).
Adds `romanization` everywhere the schema requires `romanization` alongside `bangla_pronunciation`.

Current status:
- `01-easy-hindi-foundation` (60 chapters): fully backfilled and verified.
- `02-easy-hindi-intermediate` (60 chapters): fully backfilled and verified.
- `03-easy-hindi-advanced` (60 chapters): fully backfilled and verified.
- `04-easy-hindi-vocabulary-7000-words` (214 authored chapters):
  - Chapters ch001–ch100 (80 existing chapters): backfilled and committed in `3c2e000`.
  - Chapters ch101–ch234 (134 chapters): pending backfill execution (currently missing word-level romanization and containing 74 leaked Devanagari matras in top-level fields).
  - Chapters ch021–ch030 and ch051–ch060 (20 chapters): unauthored.

This is a tooling/manager change, not lesson authoring: no target-language text, meaning,
or Bangla pronunciation was added or altered. Only the Latin-letter `romanization`
field is affected.

## How the values were produced

Run via `python3 scripts/backfill_romanization.py`:

1. **Exact reuse** for any word/phrase that already matches a `target` this book had
   already authored a `romanization` for at the sentence/vocabulary top level.
2. **Rule-based fallback** (`scripts/hindi_translit.py`) for the rest: script letters,
   number words, and word-level tokens with no standalone match elsewhere. It is a
   straightforward Devanagari→ASCII transliteration with one rule for schwa deletion —
   keep every medial inherent "a", drop only a bare word-final consonant's inherent "a".
   Medial schwa deletion or glide insertion are not attempted; see `docs/HINDI-BANGLA-NUANCES.md`
   for phonological rules requiring human review.

## Needs native-speaker review before publication

- Every fallback-tier value (not found in the existing sentence/vocabulary dictionary).
- 333 pre-existing sentence/vocabulary-level `romanization` values in Books 1–3 and Book 4
  (ch001–ch100) were repaired from leaked Devanagari characters (e.g. `'ऑ'`, `'ि'`, `'ी'`, `'ा'`).
  An additional 74 instances in Book 4 (ch101–ch234) are identified and will be resolved upon
  running the backfill on the remaining vocabulary chapters.

## Known, separate, pre-existing issues

1. `python3 scripts/manage.py validate --book 04-easy-hindi-vocabulary-7000-words --complete`
   fails with `Duplicate target across vocabulary rosters` (1,817 collisions across rosters).
   Confirmed present on `main` before the romanization backfill.
2. Missing chapters in Book 4: ch021–ch030 and ch051–ch060 are not yet authored.

