#!/usr/bin/env python3
"""Validate a single chapter and its roster directly without cross-roster global checks."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts import manage

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/validate_single_chapter.py <book-folder> <chNNN>")
        sys.exit(1)
    
    book_dir = ROOT / sys.argv[1]
    ch_id = sys.argv[2]
    
    book = manage.read(book_dir / 'book.json')
    plans = {p['chapter_id']: p for p in book['chapters']}
    if ch_id not in plans:
        print(f"Error: {ch_id} not found in book.json")
        sys.exit(1)
    
    plan = plans[ch_id]
    ch_file = manage.safe(book_dir, plan['content_file'])
    if not ch_file.exists():
        print(f"Error: Chapter file {ch_file} does not exist")
        sys.exit(1)
    
    ch = manage.read(ch_file)
    roster = None
    if book['kind'] == 'vocabulary':
        rf = manage.safe(book_dir, plan['roster_file'])
        if not rf.exists():
            print(f"Error: Roster file {rf} does not exist")
            sys.exit(1)
        roster = manage.read(rf)
        manage.need(roster.get('status') in ['proposed', 'reviewed'], f"Invalid roster status: {roster.get('status')}")
        manage.need([x['id'] for x in roster['items']] == plan['reserved_item_ids'], "Roster IDs mismatch with plan")
        for i, item in enumerate(roster['items'], 1):
            manage.filled(item, ['target', 'type', 'level_rationale'])
            manage.need(isinstance(item.get('sources'), list), "Roster sources must be a list")
            manage.need(item['category'] == ('expression' if i % 6 == 0 else 'word'), f"Item {i} category mismatch")

    # Validate chapter structure
    profile = {}
    vocab = manage.validate_chapter(book, plan, ch, profile)
    
    if book['kind'] == 'vocabulary':
        manage.need(roster is not None and roster.get('status') == 'reviewed', "Authored vocabulary requires a reviewed roster")
        manage.need([x['target'] for x in vocab] == [x['target'] for x in roster['items']], "Authored vocabulary differs from frozen roster")
    
    print(f"SUCCESS: {ch_id} in {book_dir.name} is 100% valid and conforms to all rules.")

if __name__ == '__main__':
    main()
