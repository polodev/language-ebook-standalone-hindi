"""Synthetic structural fixtures; these markers are not learner content or linguistic QA."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'scripts/manage.py'
spec = importlib.util.spec_from_file_location('manager', MODULE)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


def annotation(target, prefix=''):
    parts = target.split(' ')
    return {prefix+'target': target, prefix+'bangla_pronunciation':'ক', prefix+'romanization':'TEST',
            prefix+'word_pronunciations':[{'target':word, 'bangla_pronunciation':'ক', 'romanization':'TEST', 'separator_after':' ' if i < len(parts)-1 else ''} for i,word in enumerate(parts)]}


def fixture(kind='foundation'):
    sentences = [dict(annotation(f'X{i} Y{i}'), id=f's{i}', romanization='TEST', meaning_bengali_md='ক') for i in range(20)]
    vocabulary = [dict(annotation('X0'), id='v0', type='test', romanization='TEST', meaning_bengali_md='ক', source_sentence_id='s0', source_form='X0')]
    chapter = {'chapter_id':'ch001', 'status':'drafted', 'title_target':'TEST', 'title_bangla_pronunciation':'ক', 'title_romanization':'TEST', 'title_word_pronunciations':annotation('TEST')['word_pronunciations'], 'title_bengali':'ক', 'goal_bengali_md':'ক',
               'script_practice':[{'item_id':str(i),'mode':'new','target':str(i),'bangla_pronunciation':'ক','romanization':'TEST','explanation_bengali_md':'ক','practice_bengali_md':'ক'} for i in range(5)],
               'number_practice':None, 'sentences':sentences, 'vocabulary':vocabulary,
               'bridge_reading':{'mode':'story','title_bengali':'ক','segments':[{'kind':'bangla','text':'ক'},dict(annotation('TEST'),kind='target')],'scene_summary':'TEST'},
               'target_reading':{'mode':'article','title_bengali':'ক','lines':[annotation(f'LINE{i}') for i in range(4)],'scene_summary':'TEST','bangla_pronunciation':'ক','romanization':'TEST','meaning_bengali_md':'ক'},
               'speaking_practice':[dict(annotation('TEST', 'model_'),prompt_bengali_md='ক',model_meaning_bengali_md='ক') for _ in range(6)],
               'image_prompts':[{'key':f'ch001_{key}_01','reading':key,'subject':'TEST. No readable text.','style':'TEST'} for key in ['bridge_reading','target_reading']]}
    book = {'kind':kind,'sentences_per_chapter':20,'pure_reading_max_units':12 if kind=='advanced' else 8}
    plan = {'chapter_id':'ch001','script_items':5,'number_items_allowed':[0,2,3],'sentence_max_units':4 if kind=='foundation' else None}
    if kind == 'vocabulary':
        plan['reserved_item_ids']=[f'v{i}' for i in range(30)]
        chapter['vocabulary']=[]
        for i in range(30):
            j=i//2
            target=f'{"X" if i%2==0 else "Y"}{j}'
            chapter['vocabulary'].append(dict(annotation(target),id=f'v{i}',type='test',romanization='TEST',meaning_bengali_md='ক',source_sentence_id=f's{j}',source_form=target,category='expression' if (i+1)%6==0 else 'word',synonyms=[],**annotation('TEST','example_'),example_meaning_bengali_md='ক'))
    chapter['bridge_reading']['text_md']=manager.mixed_reading_markdown(chapter['bridge_reading']['segments'])
    return book,plan,chapter,{'word_count_mode':'space'}


class ValidationTests(unittest.TestCase):
    def test_valid_all_four_book_kinds(self):
        for kind in ['foundation','intermediate','advanced','vocabulary']:
            with self.subTest(kind=kind): manager.validate_chapter(*fixture(kind))

    def test_every_book_requires_twenty_sentences(self):
        for kind in ['foundation','intermediate','advanced','vocabulary']:
            b,p,c,l=fixture(kind); c['sentences'].pop()
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError,'20 essential'): manager.validate_chapter(b,p,c,l)

    def test_missing_word_pronunciation_at_each_learner_location(self):
        for location in ['title','sentence','vocab','bridge','reading','task','number','example','synonym','collocation']:
            b,p,c,l=fixture('vocabulary')
            c['number_practice']=[dict(annotation(str(i)),display=str(i),meaning_bengali_md='ক',system='TEST') for i in range(2)]
            c['vocabulary'][0]['synonyms']=[annotation('OTHER')]
            c['vocabulary'][0]['collocations']=[annotation('OTHER')]
            item,key = {'title':(c,'title_word_pronunciations'),'sentence':(c['sentences'][0],'word_pronunciations'),'vocab':(c['vocabulary'][0],'word_pronunciations'),'bridge':(c['bridge_reading']['segments'][1],'word_pronunciations'),'reading':(c['target_reading']['lines'][0],'word_pronunciations'),'task':(c['speaking_practice'][0],'model_word_pronunciations'),'number':(c['number_practice'][0],'word_pronunciations'),'example':(c['vocabulary'][0],'example_word_pronunciations'),'synonym':(c['vocabulary'][0]['synonyms'][0],'word_pronunciations'),'collocation':(c['vocabulary'][0]['collocations'][0],'word_pronunciations')}[location]
            del item[key]
            with self.subTest(location=location), self.assertRaisesRegex(ValueError,'Word-by-word'): manager.validate_chapter(b,p,c,l)

    def test_prefixed_whole_pronunciation_requires_bangla(self):
        b,p,c,l=fixture(); c['title_bangla_pronunciation']='English'
        with self.assertRaisesRegex(ValueError,'Bangla script'): manager.validate_chapter(b,p,c,l)

    def test_reconstruction_catches_missing_wrong_reordered_words_and_spacing(self):
        for words in [[{'target':'A','bangla_pronunciation':'ক','romanization':'TEST','separator_after':''}],annotation('A C')['word_pronunciations'],annotation('B A')['word_pronunciations'],annotation('A B ')['word_pronunciations']]:
            with self.subTest(words=words), self.assertRaises(ValueError): manager.validate_words('A B',words)

    def test_sentence_cannot_hide_inside_one_pronunciation_unit(self):
        with self.assertRaisesRegex(ValueError,'one word'): manager.validate_words('A B',[{'target':'A B','bangla_pronunciation':'ক','romanization':'TEST','separator_after':''}])

    def test_segmented_script_preserves_unspaced_native_text(self):
        manager.validate_words('甲乙',[{'target':x,'bangla_pronunciation':'ক','romanization':'TEST','separator_after':''} for x in ['甲','乙']])

    def test_five_distinct_script_cards(self):
        for action in ['remove','duplicate']:
            b,p,c,l=fixture()
            if action=='remove': c['script_practice'].pop()
            else: c['script_practice'][1]=copy.deepcopy(c['script_practice'][0])
            with self.subTest(action=action), self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_numbers_are_null_or_two_or_three_any_chapter(self):
        for count in [None,0,1,2,3,4]:
            b,p,c,l=fixture()
            c['number_practice']=None if count is None else [dict(annotation(str(i)),display=str(i),meaning_bengali_md='ক',system='TEST') for i in range(count)]
            with self.subTest(count=count):
                if count in [None,2,3]: manager.validate_chapter(b,p,c,l)
                else:
                    with self.assertRaisesRegex(ValueError,'null or two/three'): manager.validate_chapter(b,p,c,l)

    def test_sentence_and_reading_ceilings(self):
        for location in ['sentence','reading']:
            b,p,c,l=fixture()
            item=c['sentences'][0] if location=='sentence' else c['target_reading']['lines'][0]
            item.update(annotation('A B C D E'))
            with self.subTest(location=location), self.assertRaisesRegex(ValueError,'exceeds'): manager.validate_chapter(b,p,c,l)

    def test_simple_reading_limits_and_advanced_intermediate_limit(self):
        for kind in ['foundation','intermediate','vocabulary','advanced']:
            b,p,c,l=fixture(kind); p['sentence_max_units']=None
            ceiling=12 if kind=='advanced' else 8
            c['target_reading']['lines'][0]=annotation(' '.join(['TEST']*ceiling))
            manager.validate_chapter(b,p,c,l)
            c['target_reading']['lines'][0]=annotation(' '.join(['TEST']*(ceiling+1)))
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'exceeds'): manager.validate_chapter(b,p,c,l)

    def test_pure_reading_four_to_eight_lines(self):
        for count in [0,3,4,8,9]:
            b,p,c,l=fixture(); c['target_reading']['lines']=[annotation('TEST') for _ in range(count)]
            with self.subTest(count=count):
                if count in [4,8]: manager.validate_chapter(b,p,c,l)
                else:
                    with self.assertRaisesRegex(ValueError,'four to eight'): manager.validate_chapter(b,p,c,l)

    def test_whole_article_pronunciation_required(self):
        b,p,c,l=fixture(); del c['target_reading']['bangla_pronunciation']
        with self.assertRaisesRegex(ValueError,'Missing text'): manager.validate_chapter(b,p,c,l)

    def test_mixed_reading_requires_both_segment_kinds(self):
        b,p,c,l=fixture(); c['bridge_reading']['segments'].pop()
        with self.assertRaisesRegex(ValueError,'both Bangla and target'): manager.validate_chapter(b,p,c,l)

    def test_mixed_markdown_bolds_each_repeated_word_with_its_own_cue(self):
        b,p,c,l=fixture()
        c['bridge_reading']['segments']=[{'kind':'bangla','text':'ক '},dict(annotation('X X'),kind='target')]
        c['bridge_reading']['text_md']=manager.mixed_reading_markdown(c['bridge_reading']['segments'])
        self.assertEqual(c['bridge_reading']['text_md'],'ক **X** (ক, TEST) **X** (ক, TEST)')
        manager.validate_chapter(b,p,c,l)

    def test_mixed_markdown_requires_bold_on_every_word(self):
        for bad in ['ক X (ক) X (ক)', 'ক **X** (ক) X (ক)']:
            b,p,c,l=fixture()
            c['bridge_reading']['segments']=[{'kind':'bangla','text':'ক '},dict(annotation('X X'),kind='target')]
            c['bridge_reading']['text_md']=bad
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'bold-word/pronunciation mirror'):
                manager.validate_chapter(b,p,c,l)

    def test_mixed_markdown_rejects_wrong_pronunciation(self):
        b,p,c,l=fixture(); c['bridge_reading']['text_md']='ক**TEST** (খ)'
        with self.assertRaisesRegex(ValueError,'bold-word/pronunciation mirror'): manager.validate_chapter(b,p,c,l)

    def test_mixed_markdown_rejects_divergent_narration_or_native_text(self):
        for bad in ['খ**TEST** (ক)', 'ক**OTHER** (ক)']:
            b,p,c,l=fixture(); c['bridge_reading']['text_md']=bad
            with self.subTest(bad=bad),self.assertRaisesRegex(ValueError,'bold-word/pronunciation mirror'):
                manager.validate_chapter(b,p,c,l)

    def test_mixed_markdown_requires_nonempty_stored_mirror(self):
        for absent in [False,True]:
            b,p,c,l=fixture()
            if absent: del c['bridge_reading']['text_md']
            else: c['bridge_reading']['text_md']=''
            with self.subTest(absent=absent),self.assertRaisesRegex(ValueError,'Missing text: text_md'):
                manager.validate_chapter(b,p,c,l)

    def test_mixed_markdown_escapes_narration_native_and_cue(self):
        b,p,c,l=fixture()
        target=annotation('X_*[!]')
        target['word_pronunciations'][0]['bangla_pronunciation']='ক_(খ)'
        c['bridge_reading']['segments']=[{'kind':'bangla','text':'ক [*]\\` '},dict(target,kind='target')]
        c['bridge_reading']['text_md']=manager.mixed_reading_markdown(c['bridge_reading']['segments'])
        self.assertEqual(c['bridge_reading']['text_md'],r'ক \[\*\]\\\` **X\_\*\[\!\]** (ক\_\(খ\), TEST)')
        manager.validate_chapter(b,p,c,l)

    def test_mixed_markdown_preserves_apostrophes_and_email_punctuation(self):
        b,p,c,l=fixture()
        c['bridge_reading']['segments']=[{'kind':'bangla','text':'ক: '},dict(annotation("l'amour name@example.com"),kind='target')]
        c['bridge_reading']['text_md']=manager.mixed_reading_markdown(c['bridge_reading']['segments'])
        self.assertEqual(c['bridge_reading']['text_md'],"ক: **l'amour** (ক, TEST) **name@example\\.com** (ক, TEST)")
        manager.validate_chapter(b,p,c,l)

    def test_legacy_prose_rejected(self):
        for key in ['text_md','text','words']:
            b,p,c,l=fixture(); c['target_reading'][key]='TEST'
            with self.subTest(key=key),self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_vocab_sources_exist_and_source_form_occurs(self):
        for kind in ['foundation','vocabulary']:
            for key in ['source_sentence_id','source_form']:
                b,p,c,l=fixture(kind); c['vocabulary'][0][key]='MISSING'
                with self.subTest(kind=kind,key=key),self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_ladder_vocabulary_is_variable_and_nonempty(self):
        b,p,c,l=fixture(); c['vocabulary']=[]
        with self.assertRaisesRegex(ValueError,'Select useful'): manager.validate_chapter(b,p,c,l)

    def test_vocab_companion_requires_thirty_and_frozen_order_categories(self):
        for fault in ['count','order','category']:
            b,p,c,l=fixture('vocabulary')
            if fault=='count': c['vocabulary'].pop()
            elif fault=='order': c['vocabulary'].reverse()
            else: c['vocabulary'][5]['category']='word'
            with self.subTest(fault=fault),self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_practice_count_and_optional_expansions(self):
        b,p,c,l=fixture(); c['speaking_practice'].pop()
        with self.assertRaisesRegex(ValueError,'Six practice'): manager.validate_chapter(b,p,c,l)
        b,p,c,l=fixture(); c['additional_practice']=[dict(annotation('A','base_'),**annotation('B','expanded_'),**annotation('C','polished_'),explanation_bengali_md='ক')]
        manager.validate_chapter(b,p,c,l)
        del c['additional_practice'][0]['expanded_word_pronunciations']
        with self.assertRaisesRegex(ValueError,'Word-by-word'): manager.validate_chapter(b,p,c,l)

    def test_image_key_and_no_text(self):
        for key,value in [('key','other'),('subject','TEST')]:
            b,p,c,l=fixture(); c['image_prompts'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ValueError): json.loads('{"a":1,"a":2}',object_pairs_hook=manager.unique_pairs)

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): manager.safe(Path(d),'../outside.json')

    def test_html_rejected(self):
        b,p,c,l=fixture(); c['goal_bengali_md']='ক <b>test</b>'
        with self.assertRaisesRegex(ValueError,'Raw HTML'): manager.validate_chapter(b,p,c,l)

    def test_complete_requires_every_one_of_sixty_chapters(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve(); bookpath=root/'book'; bookpath.mkdir()
            b,p,c,l=fixture()
            b.update(chapter_count=60,expected_output_files=[str(i) for i in range(8)],chapters=[])
            for i in range(1,61):
                plan=dict(p,chapter_id=f'ch{i:03}',chapter_number=i,content_file=f'chapters/ch{i:03}.json')
                b['chapters'].append(plan)
                chapter=copy.deepcopy(c); chapter['chapter_id']=plan['chapter_id']
                for card in chapter['script_practice']: card['mode']='review'
                for image in chapter['image_prompts']: image['key']=f'{plan["chapter_id"]}_{image["reading"]}_01'
                manager.write(bookpath/plan['content_file'],chapter)
            manager.write(bookpath/'book.json',b)
            with patch.object(manager,'ROOT',root):
                self.assertEqual(len(manager.check_book(bookpath,l,complete=True)[1]),60)
                (bookpath/'chapters/ch037.json').unlink()
                self.assertEqual(len(manager.check_book(bookpath,l)[1]),59)
                with self.assertRaisesRegex(ValueError,'Missing authored chapter.*ch037'):
                    manager.check_book(bookpath,l,complete=True)

    def test_packet_has_only_book_instruction_source(self):
        # A tiny isolated repo proves removed shared authoring files are never read.
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'scripts').mkdir(); (root/'scripts/manage.py').write_text(MODULE.read_text())
            book=root/'book'; book.mkdir()
            manager.write(root/'language.json',{'locale':'test'})
            manager.write(root/'courses.json',{'courses':[{'directory':'book'}]})
            manager.write(book/'book.json',{'chapter_count':1,'chapters':[{'chapter_id':'ch001'}]})
            manager.write(book/'chapter-template.json',{})
            (book/'INSTRUCTIONS.md').write_text('SINGLE AUTHORING SOURCE')
            result=subprocess.run([sys.executable,str(root/'scripts/manage.py'),'packet','--book','book'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            packet=manager.read(book/'generated/ch001-authoring-packet.json')
            self.assertEqual(packet['instructions'],{'INSTRUCTIONS.md':'SINGLE AUTHORING SOURCE'})


if __name__ == '__main__': unittest.main()
