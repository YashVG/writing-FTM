import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from generation_quality import repetition_metrics


class RepetitionTests(unittest.TestCase):
    def test_loop_detected(self):
        text='The paragraph does not state the sample does not establish regional preferences. '
        self.assertTrue(repetition_metrics(text*10)['repetition_flag'])

    def test_short_and_normal_feedback_not_flagged(self):
        self.assertFalse(repetition_metrics('')['repetition_flag'])
        self.assertFalse(repetition_metrics('The sample only includes weekend visitors. Restrict the claim to that sample.')['repetition_flag'])

    def test_official_template_does_not_supervise_thinking(self):
        try:
            from transformers import AutoTokenizer
        except ImportError:self.skipTest('Local tokenizer dependencies absent')
        import json
        info=Path('runs/pilot/model.json')
        if not info.exists():self.skipTest('Local model unavailable')
        tok=AutoTokenizer.from_pretrained(json.loads(info.read_text())['path'],local_files_only=True)
        tok.chat_template=Path('configs/chat_templates/qwen3-instruct-2507.jinja').read_text()
        messages=[{'role':'user','content':'Check the claim.'},{'role':'assistant','content':'Revise it.'}]
        prefix=tok.apply_chat_template(messages[:-1],add_generation_prompt=True,return_dict=False)
        full=tok.apply_chat_template(messages,return_dict=False)
        self.assertEqual(full[:len(prefix)],prefix)
        self.assertNotIn('<think>',tok.decode(full[len(prefix):]))
        self.assertIn(tok.eos_token_id,full[len(prefix):])

class GateTests(unittest.TestCase):
    def test_correct_tag_does_not_hide_loop(self):
        from check_generation_gate import check
        row={'id':'a','prompt':'p','answer':'retain','wrong':'revise','text':'Supported.',
             'hit_token_cap':False,'score':{'parsed':True,'correct':True}}
        self.assertTrue(check([row],[row])['passed'])
        loop={**row,'text':('The paragraph does not state the sample does not establish regional preferences. '*10)+'<answer>retain</answer>'}
        self.assertFalse(check([loop],[row])['passed'])
        capped={**row,'hit_token_cap':True}
        self.assertFalse(check([capped],[row])['passed'])
        wrong={**row,'score':{'parsed':True,'correct':False}}
        self.assertFalse(check([wrong],[row])['passed'])

class ModelViewTests(unittest.TestCase):
    def test_view_does_not_modify_source(self):
        import json,tempfile
        from model_template import model_view,TEMPLATE
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source';source.mkdir()
            (source/'tokenizer_config.json').write_text(json.dumps({'chat_template':'original'}))
            (source/'chat_template.jinja').write_text('original')
            (source/'weights').write_text('unchanged')
            provenance=json.loads(TEMPLATE.with_suffix('.json').read_text())
            result=model_view({'path':str(source),'revision':provenance['model_revision']},root/'view')
            self.assertEqual((source/'chat_template.jinja').read_text(),'original')
            self.assertEqual(json.loads((source/'tokenizer_config.json').read_text())['chat_template'],'original')
            self.assertEqual((root/'view/chat_template.jinja').read_text(),TEMPLATE.read_text())
            self.assertTrue((root/'view/weights').is_symlink())
