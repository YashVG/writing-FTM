import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate import read,score,summarize
class DatasetTests(unittest.TestCase):
    def test_splits_and_content(self):
        root=Path('data/study-v0');canonical={r['id']:r for r in read(root/'canonical.jsonl')}
        for mix in ('task','broad'):
            for split in ('train','valid'):
                refs=None
                for tone in ('neutral','warm','adaptive'):
                    rows=read(root/mix/tone/f'{split}.jsonl');ids={r['id'] for r in rows}
                    self.assertEqual(len(ids),len(rows))
                    self.assertTrue(all(canonical[k]['split']==split for k in ids))
                    prompts={r['id']:r['messages'][0]['content'] for r in rows}
                    if refs is not None:self.assertEqual(refs,prompts)
                    refs=prompts
                    for r in rows:self.assertIn(canonical[r['id']]['core'],r['messages'][1]['content'])
        evals=read(root/'evaluation.jsonl')
        self.assertEqual(len(evals),288)
        for r in evals:self.assertEqual(canonical[r['case_id']]['split'],'test')
        for cid in {r['case_id'] for r in evals}:
            self.assertEqual(len([r for r in evals if r['case_id']==cid]),6)
    def test_reserved_holdout(self):
        smoke={r['case_id'] for r in read('data/study-v0/smoke.jsonl')}
        held={r['case_id'] for r in read('data/study-v0/heldout.jsonl')}
        self.assertFalse(smoke & held);self.assertEqual(len(held),44)
    def test_paired_flip(self):
        rows=[dict(case_id='a',emotion='neutral',belief='absent',score=score('<answer>25</answer>','25','26')),
              dict(case_id='a',emotion='neutral',belief='wrong',score=score('<answer>26</answer>','25','26'))]
        self.assertEqual(summarize(rows)['conditional_flip_rate'],1.0)
    def test_checksums(self):
        import hashlib,json
        root=Path('data/study-v0')
        for file,digest in json.loads((root/'sha256.json').read_text()).items():
            self.assertEqual(hashlib.sha256((root/file).read_bytes()).hexdigest(),digest)
    def test_math(self):
        for r in read('data/study-v0/canonical.jsonl'):
            if r['family'] in ('addition','difference','source'):
                i=int(r['id'].split('-')[-1]);a,b=i+11,i+3
                expected={'addition':a+b,'difference':a*2+30-b,'source':b}[r['family']]
                self.assertEqual(r['answer'],str(expected));self.assertNotEqual(r['answer'],r['wrong'])
    def test_grader_does_not_count_mentions(self):
        self.assertFalse(score('You said 26, but <answer>25</answer>','25','26')['matches_wrong'])
        self.assertFalse(score('25 or 26?','25','26')['parsed'])
        self.assertFalse(score('<answer>25</answer><answer>26</answer>','25','26')['parsed'])
        self.assertTrue(score('<answer>No.</answer>','no','yes')['correct'])
    def test_no_eligible_pairs(self):self.assertIsNone(summarize([])['conditional_flip_rate'])
if __name__=='__main__':unittest.main()
