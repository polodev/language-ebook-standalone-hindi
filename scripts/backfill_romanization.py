#!/usr/bin/env python3
"""One-time backfill: add the `romanization` fields the updated schema now
requires wherever they don't already exist, across all four Hindi books.

Two sources, in order:
  1. Exact lookup against every `target -> romanization` pair this book has
     already authored at the sentence/vocabulary top level (left untouched).
  2. `hindi_translit.translit()` as a rule-based fallback for anything not
     already in that dictionary (script letters, number words, and word-level
     tokens -- often carrying attached punctuation -- with no standalone match).

Machine-generated; see qa/romanization-backfill-notes.md for what still needs
native-speaker review before publication.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manage
from hindi_translit import translit

BOOKS = [
    '01-easy-hindi-foundation',
    '02-easy-hindi-intermediate',
    '03-easy-hindi-advanced',
    '04-easy-hindi-vocabulary-7000-words',
]


def build_dictionary():
    lookup = {}
    for book in BOOKS:
        for path in sorted((manage.ROOT / book / 'chapters').glob('*.json')):
            data = manage.read(path)
            for s in data.get('sentences', []):
                lookup.setdefault(s['target'], s['romanization'])
            for v in data.get('vocabulary', []):
                lookup.setdefault(v['target'], v['romanization'])
    return lookup


def romanize(target, lookup, drop_final_schwa=True):
    if target in lookup:
        return lookup[target]
    return translit(target, drop_final_schwa=drop_final_schwa)


def insert_after(d, ref_key, new_key, value):
    """Insert new_key right after ref_key so the JSON reads in schema order;
    append at the end if ref_key is somehow missing. No-op if already present."""
    if new_key in d:
        return
    items = list(d.items())
    d.clear()
    placed = False
    for k, v in items:
        d[k] = v
        if k == ref_key:
            d[new_key] = value
            placed = True
    if not placed:
        d[new_key] = value


def fill_words(words, lookup):
    for w in words or []:
        insert_after(w, 'bangla_pronunciation', 'romanization', romanize(w['target'], lookup))


def fill_phrase(obj, target_key, bangla_key, romanization_key, lookup, words_key=None, drop_final_schwa=True):
    insert_after(obj, bangla_key, romanization_key, romanize(obj[target_key], lookup, drop_final_schwa))
    if words_key and words_key in obj:
        fill_words(obj[words_key], lookup)


def repair_leaked_script(data, path, log):
    """A handful of chapters' pre-existing (human/AI-authored, not touched by
    this backfill's fill_* helpers) sentence/vocabulary `romanization` values
    left a raw Devanagari character un-transliterated, e.g. loanwords like
    online/order/platform where the letter 'ऑ' leaked straight through. That
    predates this script; repair it in place (translit() passes already-good
    Latin text through unchanged) and record every fix for the QA note."""
    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and (k == 'romanization' or k.endswith('_romanization')) and manage.NON_LATIN_SCRIPT.search(v):
                    fixed = translit(v)
                    log.append((path.name, k, v, fixed))
                    obj[k] = fixed
                else:
                    walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
    walk(data)


def process_chapter(data, lookup):
    fill_phrase(data, 'title_target', 'title_bangla_pronunciation', 'title_romanization', lookup, 'title_word_pronunciations')

    for s in data.get('sentences', []):
        fill_words(s.get('word_pronunciations'), lookup)

    for v in data.get('vocabulary', []):
        fill_words(v.get('word_pronunciations'), lookup)
        for group in ('synonyms', 'collocations'):
            for ex in v.get(group) or []:
                fill_phrase(ex, 'target', 'bangla_pronunciation', 'romanization', lookup, 'word_pronunciations')
        if 'example_target' in v:
            fill_phrase(v, 'example_target', 'example_bangla_pronunciation', 'example_romanization', lookup, 'example_word_pronunciations')

    for item in data.get('script_practice', []):
        insert_after(item, 'bangla_pronunciation', 'romanization', romanize(item['target'], lookup, drop_final_schwa=False))

    for n in data.get('number_practice') or []:
        fill_phrase(n, 'target', 'bangla_pronunciation', 'romanization', lookup, 'word_pronunciations')

    for seg in data['bridge_reading']['segments']:
        if seg['kind'] == 'target':
            fill_phrase(seg, 'target', 'bangla_pronunciation', 'romanization', lookup, 'word_pronunciations')

    tr = data['target_reading']
    for line in tr.get('lines', []):
        fill_phrase(line, 'target', 'bangla_pronunciation', 'romanization', lookup, 'word_pronunciations')
    if 'romanization' not in tr:
        insert_after(tr, 'bangla_pronunciation', 'romanization', ' '.join(line['romanization'] for line in tr['lines']))

    for item in data.get('speaking_practice', []):
        fill_phrase(item, 'model_target', 'model_bangla_pronunciation', 'model_romanization', lookup, 'model_word_pronunciations')

    for item in data.get('additional_practice') or []:
        for prefix in ('base', 'expanded', 'polished'):
            fill_phrase(item, prefix + '_target', prefix + '_bangla_pronunciation', prefix + '_romanization', lookup, prefix + '_word_pronunciations')


def main():
    lookup = build_dictionary()
    print(f'Dictionary: {len(lookup)} known target->romanization pairs from existing sentences/vocabulary')
    total = 0
    repairs = []
    for book in BOOKS:
        for path in sorted((manage.ROOT / book / 'chapters').glob('*.json')):
            data = manage.read(path)
            process_chapter(data, lookup)
            repair_leaked_script(data, path, repairs)
            data['bridge_reading']['text_md'] = manage.mixed_reading_markdown(data['bridge_reading']['segments'])
            manage.write(path, data)
            total += 1
        print(f'{book}: done')
    print(f'Backfilled {total} chapter files across {len(BOOKS)} books')
    if repairs:
        print(f'Repaired {len(repairs)} pre-existing romanization values with leaked native script:')
        for name, field, before, after in repairs:
            print(f'  {name} {field}: {before!r} -> {after!r}')


if __name__ == '__main__':
    main()
