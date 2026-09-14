# Romanization backfill — 2026-09-14

Scope: all 4 books (foundation, intermediate, advanced, vocabulary-7000-words), all 260
authored chapters. Adds `romanization` everywhere the schema previously only required
`bangla_pronunciation` (word-by-word breakdowns, script letters, number cards, mixed/pure
reading full text and lines, speaking/additional practice, synonyms/collocations),
matching the updated `INSTRUCTIONS.md` and `scripts/manage.py`.

This is a tooling/manager change, not lesson authoring: no target-language text, meaning,
or Bangla pronunciation was added or altered. Only the new Latin-letter `romanization`
field was filled in.

## How the values were produced

Run via `python3 scripts/manage.py packet` → no; actual tool: `python3 scripts/backfill_romanization.py`.

1. **Exact reuse** for any word/phrase that already matches a `target` this book had
   already authored a `romanization` for at the sentence/vocabulary top level (6,985
   such pairs across the 4 books). This covered roughly half of all word-level tokens
   (~30k of ~58k).
2. **Rule-based fallback** (`scripts/hindi_translit.py`) for the rest: script letters,
   number words, and word-level tokens with no standalone match elsewhere (~2k unique
   tokens). It is a straightforward Devanagari→ASCII transliteration with one rule for
   schwa deletion — keep every medial inherent "a", drop only a bare word-final
   consonant's inherent "a". It reproduces the existing corpus's own style on common
   cases (`namaste!`, `kameez`, `subah`, `ek`) but does **not** attempt medial schwa
   deletion or glide insertion, both genuinely hard, well-known problems in Hindi
   romanization. Expect occasional non-native-feeling output on less common words
   (e.g. "chalate" rather than "chalte").

## Needs native-speaker review before publication

- Every fallback-tier value (not found in the existing sentence/vocabulary dictionary)
  — flagged above as a simplification, not a native check.
- 333 **pre-existing** sentence/vocabulary-level `romanization` values (authored before
  this change, untouched by the fill-in logic) turned out to already contain a leaked,
  un-transliterated Devanagari character — mostly the "ऑ"/"ॉ" vowel sign in loanwords
  like online/order/office/platform (e.g. `'ऑnalaain'` for अनलाइन-style words), plus a
  handful of other matras (`'sabzिyaan'`, `'gharी'`, `'kaparा'`, ...). These were
  mechanically repaired by running the *existing* string through the same transliterator
  (which passes already-correct Latin text through unchanged) rather than left broken,
  since the new stricter validator now rejects raw native script in a `romanization`
  field. This is the only change made to previously-authored `romanization` text; see
  `scripts/backfill_romanization.py`'s `repair_leaked_script()` for the exact list (also
  printed by the script on every run).

## Known, separate, pre-existing issue (not touched by this change)

`python3 scripts/manage.py validate --book 04-easy-hindi-vocabulary-7000-words --complete`
fails with `Duplicate target across vocabulary rosters`. Confirmed present on `main`
before this backfill (checked via `git stash`) — unrelated to romanization, not
introduced or fixed here.
