"""Synthetic structural fixtures, not learner content or linguistic QA."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'scripts/manage.py'
spec = importlib.util.spec_from_file_location('manager', MODULE)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


def fixture():
    # Repeated test markers exercise contracts, never represent usable lessons.
    s = {'id':'s1', 'target':'TEST', 'romanization':'TEST', 'bangla_pronunciation':'ক', 'meaning_bengali_md':'ক', 'learning_units':['TEST']}
    v = {'id':'v1', 'target':'TEST', 'type':'test', 'romanization':'TEST', 'bangla_pronunciation':'ক', 'meaning_bengali_md':'ক', 'source_sentence_id':'s1'}
    chapter = {'chapter_id':'ch001', 'status':'drafted', 'title_target':'TEST', 'title_bengali':'ক', 'goal_bengali_md':'ক',
               'script_practice':[{'item_id':str(i),'mode':'new','target':str(i),'bangla_pronunciation':'ক','explanation_bengali_md':'ক','practice_bengali_md':'ক'} for i in range(5)],
               'number_practice':[], 'sentences':[s], 'vocabulary':[v],
               'bridge_reading':{'mode':'story','title_bengali':'ক','text_md':'TEST-A','scene_summary':'TEST'},
               'target_reading':{'mode':'article','title_bengali':'ক','text_md':'TEST-B','scene_summary':'TEST','meaning_bengali_md':'ক'},
               'speaking_practice':[{'prompt_bengali_md':'ক','model_target':'TEST','model_meaning_bengali_md':'ক'} for _ in range(6)],
               'image_prompts':[{'key':f'ch001_{key}_01','reading':key,'subject':'TEST. No readable text.','style':'TEST'} for key in ['bridge_reading','target_reading']]}
    book = {'kind':'foundation','sentences_per_chapter':1,'vocabulary_per_chapter':1}
    plan = {'chapter_id':'ch001','number_items':0,'sentence_max_units':4}
    profile = {'word_count_mode':'space'}
    return book, plan, chapter, profile


class ValidationTests(unittest.TestCase):
    def test_valid_shape(self):
        manager.validate_chapter(*fixture())

    def test_core_reading_cannot_be_replaced_by_builder(self):
        b,p,c,l = fixture()
        c['target_reading']['text_md'] = ''
        c['additional_practice'] = [{'base_target':'TEST'}]
        with self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_exact_five_script_items(self):
        b,p,c,l = fixture(); c['script_practice'].pop()
        with self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_number_schedule(self):
        b,p,c,l = fixture(); p['number_items'] = 2
        with self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_sentence_ceiling(self):
        b,p,c,l = fixture(); c['sentences'][0]['target'] = 'a b c d e'
        with self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_segmented_ceiling(self):
        b,p,c,l = fixture(); l['word_count_mode']='segmented'; c['sentences'][0]['learning_units']=['a']*5
        with self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_unknown_source(self):
        b,p,c,l = fixture(); c['vocabulary'][0]['source_sentence_id']='missing'
        with self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_image_key_mismatch(self):
        b,p,c,l = fixture(); c['image_prompts'][0]['key']='other'
        with self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ValueError): json.loads('{"a":1,"a":2}', object_pairs_hook=manager.unique_pairs)

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): manager.safe(Path(d), '../outside.json')

    def test_html_rejected(self):
        b,p,c,l = fixture(); c['goal_bengali_md']='ক <b>test</b>'
        with self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)

    def test_vocabulary_order_and_category(self):
        b,p,c,l = fixture(); b['kind']='vocabulary'; b['vocabulary_per_chapter']=30
        p['reserved_item_ids']=[f'v{i}' for i in range(30)]
        c['vocabulary']=[dict(c['vocabulary'][0],id=f'v{i}',target=f'TEST{i}', category='expression' if (i+1)%6==0 else 'word',example_target='TEST',example_bangla_pronunciation='ক',example_meaning_bengali_md='ক',synonyms=[]) for i in range(30)]
        manager.validate_chapter(b,p,c,l)
        c['vocabulary'][5]['category']='word'
        with self.assertRaises(ValueError): manager.validate_chapter(b,p,c,l)


if __name__ == '__main__': unittest.main()
