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
        if 'bengali' in field or 'bangla_pronunciation' in field:
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


def validate_words(target, words):
    need(isinstance(target, str) and target.strip(), 'Target text is required')
    need(isinstance(words, list) and words, 'Word-by-word pronunciation is required')
    reconstructed = ''
    for word in words:
        need(isinstance(word, dict), 'Pronunciation unit must be an object')
        filled(word, ['target', 'bangla_pronunciation'])
        need(not any(c.isspace() for c in word['target']), 'A pronunciation unit must be one word, not a sentence')
        separator = word.get('separator_after')
        need(isinstance(separator, str) and (not separator or separator.isspace()), 'separator_after must be whitespace or empty')
        reconstructed += word['target'] + separator
    need(reconstructed == target, 'Word pronunciations must cover the exact target text in order, including spacing')


def annotated(item, target='target', pronunciation='bangla_pronunciation', words='word_pronunciations'):
    filled(item, [target, pronunciation])
    validate_words(item[target], item.get(words))


def escape_inline_markdown(text):
    """Escape Python Markdown's supported literal characters; preserve apostrophes."""
    escaped_chars = "\\`*_{}[]()>#+-.!"
    return ''.join('\\' + char if char in escaped_chars else char for char in text)


def mixed_reading_markdown(segments):
    """Derive stored Markdown: bold each native word, immediately add its Bangla cue."""
    pieces = []
    for segment in segments:
        if segment['kind'] == 'bangla':
            filled(segment, ['text'])
            pieces.append(escape_inline_markdown(segment['text']))
        else:
            need(segment['kind'] == 'target', 'Invalid mixed-reading segment kind')
            annotated(segment)
            for word in segment['word_pronunciations']:
                target = escape_inline_markdown(word['target'])
                cue = escape_inline_markdown(word['bangla_pronunciation'])
                pieces.append(f'**{target}** ({cue})' + word['separator_after'])
    return ''.join(pieces)


def validate_chapter(book, plan, ch, profile):
    need(ch['chapter_id'] == plan['chapter_id'], 'Chapter ID mismatch')
    need(ch['status'] in ['drafted', 'reviewed'], 'Chapter must be a complete draft')
    filled(ch, ['title_target', 'title_bengali', 'goal_bengali_md'])
    annotated(ch, 'title_target', 'title_bangla_pronunciation', 'title_word_pronunciations')
    for text in walk(ch):
        need(not re.search(r'<\s*/?\s*[A-Za-z][^>]*>', text), 'Raw HTML is forbidden')
        need(not re.search(r'\b(TODO|TBD|LOREM IPSUM)\b', text, re.I), 'Placeholder found')
    script = ch['script_practice']
    need(isinstance(script, list) and len(script) == 5, 'Exactly five script items required')
    need(len({x['item_id'] for x in script}) == 5, 'Duplicate script items within chapter')
    for item in script:
        filled(item, ['item_id', 'target', 'bangla_pronunciation', 'explanation_bengali_md', 'practice_bengali_md'])
        need(item['mode'] in ['new', 'review', 'application'], 'Invalid script mode')
    numbers = ch['number_practice']
    need(numbers is None or (isinstance(numbers, list) and len(numbers) in [2, 3]), 'Number practice must be null or two/three cards')
    if numbers:
        need(len({x['display'] for x in numbers}) == len(numbers), 'Duplicate number cards')
        for item in numbers:
            filled(item, ['display', 'meaning_bengali_md', 'system'])
            annotated(item)
    sentences = ch['sentences']
    need(book['sentences_per_chapter'] == 20, 'Every book requires 20 sentences per chapter')
    need(isinstance(sentences, list) and len(sentences) == 20, 'Exactly 20 essential sentences required')
    need(len({x['id'] for x in sentences}) == 20, 'Duplicate sentence IDs')
    need(len({normalized(x['target']) for x in sentences}) == 20, 'Duplicate essential sentences')
    for item in sentences:
        filled(item, ['id', 'romanization', 'meaning_bengali_md'])
        annotated(item)
        ceiling = plan.get('sentence_max_units')
        if ceiling:
            count = len(item['word_pronunciations'])
            need(count <= ceiling, f'Sentence exceeds {ceiling} words/learning units: {item["id"]}')
    vocab = ch['vocabulary']
    if book['kind'] == 'vocabulary':
        need(len(vocab) == 30, 'Vocabulary companion requires 30 entries per chapter')
    else:
        need(isinstance(vocab, list) and len(vocab) >= 1, 'Select useful vocabulary from the 20 sentences')
    need(len({x['id'] for x in vocab}) == len(vocab), 'Duplicate vocabulary IDs')
    need(len({normalized(x['target']) for x in vocab}) == len(vocab), 'Duplicate vocabulary target')
    by_id = {x['id']: x['target'] for x in sentences}
    for item in vocab:
        filled(item, ['id', 'type', 'romanization', 'meaning_bengali_md', 'source_sentence_id', 'source_form'])
        annotated(item)
        need(item['source_sentence_id'] in by_id, 'Unknown source sentence')
        need(item['source_form'] in by_id[item['source_sentence_id']], 'Vocabulary source_form does not occur in its source sentence')
        # source_form is editorial metadata, not an unannotated learner-facing line.
        for group in ['collocations', 'synonyms']:
            if group in item:
                need(isinstance(item[group], list), f'{group} must be a list')
                for example in item[group]:
                    annotated(example)
        if book['kind'] == 'vocabulary':
            filled(item, ['example_meaning_bengali_md'])
            annotated(item, 'example_target', 'example_bangla_pronunciation', 'example_word_pronunciations')
            need(isinstance(item['synonyms'], list), 'Synonyms must be a list; empty is allowed')
            need(item['category'] in ['word', 'expression'], 'Invalid lexical category')
    if book['kind'] == 'vocabulary':
        need([x['id'] for x in vocab] == plan['reserved_item_ids'], 'Vocabulary IDs/order changed')
        for i, item in enumerate(vocab, 1):
            need(item['category'] == ('expression' if i % 6 == 0 else 'word'), 'Use 25 words + 5 expressions interleaved')
    bridge = ch['bridge_reading']
    reading = ch['target_reading']
    for item in [bridge, reading]:
        need(item['mode'] in ['story', 'article'], 'Reading mode must be story or article')
        filled(item, ['title_bengali', 'scene_summary'])
    need('text_md' not in reading, 'Pure reading uses annotated lines, not legacy text_md')
    segments = bridge['segments']
    need(isinstance(segments, list) and segments, 'Mixed reading requires structured segments')
    need({x['kind'] for x in segments} == {'bangla', 'target'}, 'Mixed reading must include both Bangla and target-language segments')
    mixed = ''
    for segment in segments:
        if segment['kind'] == 'bangla':
            filled(segment, ['text'])
            need(re.search(r'[\u0980-\u09ff]', segment['text']), 'Bangla segment requires Bangla script')
            mixed += segment['text']
        else:
            annotated(segment)
            mixed += segment['target']
    filled(bridge, ['text_md'])
    need(bridge['text_md'] == mixed_reading_markdown(segments), 'Mixed reading text_md must match the exact bold-word/pronunciation mirror of segments')
    filled(reading, ['meaning_bengali_md', 'bangla_pronunciation'])
    need(not any(key in reading for key in ['text', 'word_pronunciations', 'words']), 'Pure reading uses annotated lines, not legacy root text/words')
    lines = reading['lines']
    need(isinstance(lines, list) and 4 <= len(lines) <= 8, 'Pure reading requires four to eight short lines')
    ceiling = book['pure_reading_max_units']
    if book['kind'] == 'foundation' and plan.get('sentence_max_units'):
        ceiling = min(ceiling, plan['sentence_max_units'])
    for line in lines:
        annotated(line)
        need('\n' not in line['target'] and '\r' not in line['target'], 'Each reading line must be a single line')
        need(len(line['word_pronunciations']) <= ceiling, 'Pure reading line exceeds its learning-unit limit')
    pure_text = ' '.join(line['target'] for line in lines)
    need(normalized(mixed) != normalized(pure_text), 'Readings cannot be identical')
    tasks = ch['speaking_practice']
    need(isinstance(tasks, list) and len(tasks) == 6, 'Six practice tasks required')
    for item in tasks:
        filled(item, ['prompt_bengali_md', 'model_meaning_bengali_md'])
        annotated(item, 'model_target', 'model_bangla_pronunciation', 'model_word_pronunciations')
    for item in ch.get('additional_practice', []):
        filled(item, ['explanation_bengali_md'])
        for key in ['base', 'expanded', 'polished']:
            annotated(item, key+'_target', key+'_bangla_pronunciation', key+'_word_pronunciations')
    prompts = ch['image_prompts']
    need(len(prompts) == 2, 'Two reading image prompts required')
    for prompt, key in zip(prompts, ['bridge_reading', 'target_reading']):
        need(prompt['key'] == f'{plan["chapter_id"]}_{key}_01', 'Image key mismatch')
        need(prompt['reading'] == key, 'Image reading reference mismatch')
        filled(prompt, ['subject', 'style'])
        need('no readable text' in prompt['subject'].lower(), 'Prompt must forbid readable text')
    return vocab


def check_book(path, profile, complete=False):
    book = read(path / 'book.json')
    need(book['sentences_per_chapter'] == 20, 'Every book requires 20 sentences per chapter')
    need(book['pure_reading_max_units'] == (12 if book['kind'] == 'advanced' else 8), 'Invalid pure-reading word limit')
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
        need(plan['script_items'] == 5 and plan['number_items_allowed'] == [0, 2, 3], 'Invalid learning-card plan')
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
                      'instructions': {'INSTRUCTIONS.md': (path / 'INSTRUCTIONS.md').read_text(encoding='utf-8')}}
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
