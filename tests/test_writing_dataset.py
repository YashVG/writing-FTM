import hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate import read,score
R=Path('data/writing-v1')
class WritingTests(unittest.TestCase):
 def test_group_separation(self):
  rows=read(R/'canonical.jsonl');splits={s:{r['source_group'] for r in rows if r['split']==s} for s in ['train','valid','test']}
  for a,b in [('train','valid'),('train','test'),('valid','test')]:self.assertFalse(splits[a]&splits[b])
  for group in {r['source_group'] for r in rows}:
   self.assertEqual({r['status'] for r in rows if r['source_group']==group},{'sound','flawed'})
 def test_matched_feedback_and_context(self):
  canon={r['case_id']:r for r in read(R/'canonical.jsonl')}
  for split,n in [('train',120),('valid',48)]:
   neutral={r['id']:r for r in read(R/'neutral'/f'{split}.jsonl')};warm={r['id']:r for r in read(R/'warm'/f'{split}.jsonl')}
   self.assertEqual(len(neutral),n);self.assertEqual(neutral.keys(),warm.keys())
   for k,a in neutral.items():
    b=warm[k];c=canon[a['case_id']]
    self.assertEqual(a['messages'][0],b['messages'][0]);self.assertEqual(c['split'],split)
    for row in (a,b):
     response=row['messages'][1]['content'];self.assertIn(c['required_content'],response)
     self.assertTrue(score(response,c['answer'],'retain' if c['answer']=='revise' else 'revise')['correct'])
    for emotion in ('neutral','discouraged'):
     for belief in ('absent','correct','wrong'):self.assertIn(f"{a['case_id']}-{emotion}-{belief}",neutral)
 def test_holdout_and_smoke(self):
  held=read(R/'heldout.jsonl');smoke=read(R/'smoke.jsonl')
  self.assertEqual(len(held),48);self.assertEqual(len(smoke),12)
  self.assertFalse({r['source_group'] for r in held}&{r['source_group'] for r in smoke})
  self.assertEqual({r['answer'] for r in held},{'revise','retain'})
 def test_checksums(self):
  for file,digest in json.loads((R/'sha256.json').read_text()).items():self.assertEqual(hashlib.sha256((R/file).read_bytes()).hexdigest(),digest)
 def test_source_claims_are_fictional(self):
  for r in read(R/'heldout.jsonl'):self.assertIn('Fictional source summary:',r['prompt'])
if __name__=='__main__':unittest.main()
