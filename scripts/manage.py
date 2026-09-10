"""Offline authoring handoff and validation; never creates lesson prose."""
import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def read(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_pairs)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def safe(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes book: {relative}')
    return path


def need(condition, message):
    if not condition:
        raise ValueError(message)


def filled(obj, fields):
    for field in fields:
        need(isinstance(obj.get(field), str) and obj[field].strip(), f'Missing text: {field}')
        if 'bengali' in field or field == 'bangla_pronunciation':
            need(re.search(r'[\u0980-\u09ff]', obj[field]), f'{field} requires Bangla script')


def walk(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)
    elif isinstance(value, str):
        yield value


def normalized(text):
    return ' '.join(unicodedata.normalize('NFC', text).casefold().split()).strip('.,!?।。！？')


def validate_chapter(book, plan, ch, profile):
    need(ch['chapter_id'] == plan['chapter_id'], 'Chapter ID mismatch')
    need(ch['status'] in ['drafted', 'reviewed'], 'Chapter must be a complete draft')
    filled(ch, ['title_target', 'title_bengali', 'goal_bengali_md'])
    for text in walk(ch):
        need(not re.search(r'<\s*/?\s*[A-Za-z][^>]*>', text), 'Raw HTML is forbidden')
        need(not re.search(r'\b(TODO|TBD|LOREM IPSUM)\b', text, re.I), 'Placeholder found')
    script = ch['script_practice']
    need(len(script) == 5, 'Exactly five script items required')
    need(len({x['item_id'] for x in script}) == 5, 'Duplicate script items within chapter')
    for item in script:
        filled(item, ['item_id', 'target', 'bangla_pronunciation', 'explanation_bengali_md', 'practice_bengali_md'])
        need(item['mode'] in ['new', 'review', 'application'], 'Invalid script mode')
    need(len(ch['number_practice']) == plan['number_items'], 'Wrong number-practice count')
    for item in ch['number_practice']:
        filled(item, ['display', 'target', 'bangla_pronunciation', 'meaning_bengali_md', 'system'])
    sentences = ch['sentences']
    need(len(sentences) == book['sentences_per_chapter'], 'Wrong essential-sentence count')
    need(len({x['id'] for x in sentences}) == len(sentences), 'Duplicate sentence IDs')
    for item in sentences:
        filled(item, ['id', 'target', 'romanization', 'bangla_pronunciation', 'meaning_bengali_md'])
        need(isinstance(item['learning_units'], list) and len(item['learning_units']) > 0, 'Missing segmentation')
        need(all(isinstance(x, str) and x.strip() for x in item['learning_units']), 'Empty learning unit')
        ceiling = plan.get('sentence_max_units')
        if ceiling:
            count = len(item['target'].split()) if profile['word_count_mode'] == 'space' else len(item['learning_units'])
            need(count <= ceiling, f'Sentence exceeds {ceiling} units: {item["id"]}')
    vocab = ch['vocabulary']
    need(len(vocab) == book['vocabulary_per_chapter'], 'Wrong vocabulary count')
    need(len({normalized(x['target']) for x in vocab}) == len(vocab), 'Duplicate vocabulary target')
    for item in vocab:
        filled(item, ['id', 'target', 'type', 'romanization', 'bangla_pronunciation', 'meaning_bengali_md'])
        if book['kind'] != 'vocabulary':
            need(item['source_sentence_id'] in {x['id'] for x in sentences}, 'Unknown source sentence')
        else:
            filled(item, ['example_target', 'example_bangla_pronunciation', 'example_meaning_bengali_md'])
            need(isinstance(item['synonyms'], list), 'Synonyms must be a list; empty is allowed when no true synonym exists')
            need(item['category'] in ['word', 'expression'], 'Invalid lexical category')
    if book['kind'] == 'vocabulary':
        need([x['id'] for x in vocab] == plan['reserved_item_ids'], 'Vocabulary IDs/order changed')
        for i, item in enumerate(vocab, 1):
            need(item['category'] == ('expression' if i % 6 == 0 else 'word'), 'Use 25 words + 5 expressions interleaved')
    for key in ['bridge_reading', 'target_reading']:
        reading = ch[key]
        need(reading['mode'] in ['story', 'article'], 'Reading mode must be story or article')
        filled(reading, ['title_bengali', 'text_md', 'scene_summary'])
        if key == 'target_reading':
            filled(reading, ['meaning_bengali_md'])
    need(normalized(ch['bridge_reading']['text_md']) != normalized(ch['target_reading']['text_md']), 'Readings cannot be identical')
    need(len(ch['speaking_practice']) == 6, 'Six speaking tasks required')
    for item in ch['speaking_practice']:
        filled(item, ['prompt_bengali_md', 'model_target', 'model_meaning_bengali_md'])
    prompts = ch['image_prompts']
    need(len(prompts) == 2, 'Two reading image prompts required')
    for prompt, reading in zip(prompts, ['bridge_reading', 'target_reading']):
        need(prompt['key'] == f'{plan["chapter_id"]}_{reading}_01', 'Image key mismatch')
        need(prompt['reading'] == reading, 'Image reading reference mismatch')
        filled(prompt, ['subject', 'style'])
        need('no readable text' in prompt['subject'].lower(), 'Prompt must forbid readable text')
    return vocab


def check_book(path, profile, complete=False):
    book = read(path / 'book.json')
    plans = book['chapters']
    need(len(plans) == book['chapter_count'], 'Wrong planned chapter count')
    need([x['chapter_number'] for x in plans] == list(range(1, len(plans)+1)), 'Noncontiguous chapter map')
    need(len({x['chapter_id'] for x in plans}) == len(plans), 'Duplicate planned IDs')
    need(len(book['expected_output_files']) == (12 if book['kind'] == 'vocabulary' else 8), 'Wrong output contract')
    declared = {safe(path, x['content_file']) for x in plans}
    need(all(p.resolve() in declared for p in (path / 'chapters').glob('*.json')), 'Unindexed chapter JSON found')
    chapters = []
    targets = set()
    roster_targets = set()
    seen_script = set()
    for plan in plans:
        need(plan['script_items'] == 5 and plan['number_items'] in [0, 2], 'Invalid learning-card plan')
        source = safe(path, plan['content_file'])
        roster = None
        if book['kind'] == 'vocabulary':
            roster_path = safe(path, plan['roster_file'])
            if roster_path.exists():
                roster = read(roster_path)
                need(roster['status'] in ['proposed', 'reviewed'], 'Invalid roster status')
                need([x['id'] for x in roster['items']] == plan['reserved_item_ids'], 'Roster IDs/order mismatch')
                for i, item in enumerate(roster['items'], 1):
                    filled(item, ['target', 'type', 'level_rationale'])
                    need(isinstance(item['sources'], list), 'Roster sources must be a list; record uncertainty in level_rationale')
                    need(item['category'] == ('expression' if i % 6 == 0 else 'word'), 'Roster category position mismatch')
                    key = normalized(item['target'])
                    need(key not in roster_targets, 'Duplicate target across vocabulary rosters')
                    roster_targets.add(key)
        if not source.exists():
            need(not complete, f'Missing authored chapter: {source.relative_to(ROOT)}')
            continue
        ch = read(source)
        try:
            vocab = validate_chapter(book, plan, ch, profile)
            if book['kind'] == 'vocabulary':
                need(roster is not None and roster['status'] == 'reviewed', 'Authored vocabulary requires a reviewed roster')
                need([x['target'] for x in vocab] == [x['target'] for x in roster['items']], 'Authored vocabulary differs from frozen roster')
            for item in ch['script_practice']:
                if item['mode'] == 'new':
                    need(item['item_id'] not in seen_script, 'Previously taught script item marked new')
                # A standalone Intermediate/Advanced book may review prerequisite script.
                seen_script.add(item['item_id'])
            if book['kind'] == 'vocabulary':
                for item in vocab:
                    key = normalized(item['target'])
                    need(key not in targets, 'Duplicate vocabulary headword across chapters')
                    targets.add(key)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'{source.relative_to(ROOT)}: {exc}') from exc
        chapters.append(ch)
    return book, chapters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'status', 'packet', 'assemble'])
    parser.add_argument('--book', help='Book directory name from courses.json')
    parser.add_argument('--chapter', type=int, default=1)
    parser.add_argument('--complete', action='store_true', help='Require every planned chapter; drafts never count as publication')
    args = parser.parse_args()
    profile = read(ROOT / 'language.json')
    catalog = read(ROOT / 'courses.json')
    entries = [x for x in catalog['courses'] if not args.book or x['directory'] == args.book]
    need(entries, 'Unknown book')
    if args.command in ['packet', 'assemble']:
        need(args.book is not None, '--book is required')
    for entry in entries:
        path = safe(ROOT, entry['directory'])
        if args.command == 'packet':
            book = read(path / 'book.json')
            need(1 <= args.chapter <= book['chapter_count'], 'Chapter outside plan')
            plan = book['chapters'][args.chapter - 1]
            previous = []
            for p in book['chapters'][:args.chapter - 1]:
                f = safe(path, p['content_file'])
                if f.exists():
                    d = read(f)
                    previous.append({'chapter_id': d['chapter_id'], 'script_practice': d['script_practice'], 'vocabulary': d['vocabulary']})
            packet = {'language': profile, 'book': {k: v for k, v in book.items() if k != 'chapters'}, 'plan': plan,
                      'prior_learning': previous, 'template': read(path / 'chapter-template.json'),
                      'instructions': {name: (ROOT / name).read_text() for name in ['AGENTS.md', 'docs/AUTHORING.md', 'docs/CONTENT-CONTRACT.md', 'docs/IMAGE-GUIDELINE.md']}}
            output = path / 'generated' / f'{plan["chapter_id"]}-authoring-packet.json'
            write(output, packet)
            print(output)
            continue
        book, chapters = check_book(path, profile, complete=args.complete or args.command == 'assemble')
        print(f'{entry["directory"]}: {len(chapters)}/{book["chapter_count"]} authored chapters structurally valid; publication not assessed')
        if args.command == 'assemble':
            write(path / 'generated' / 'assembled.json', {'book': book, 'chapters': chapters})
            images = read(path / 'global-images.json')['images']
            for image in images:
                filled(image, ['subject'])
            for ch in chapters:
                for image in ch['image_prompts']:
                    images.append({'key': image['key'], 'role': 'lesson-hero', 'subject': image['subject'],
                                   'style': image['style'], 'size': '1536x1024', 'quality': 'low', 'filename': image['key'] + '.png'})
            write(path / 'generated' / 'image-declaration.json', {'default_quality': 'low', 'images': images})


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise SystemExit(f'Validation failed: {exc}')
