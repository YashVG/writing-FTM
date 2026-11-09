"""Tokenizer audit and privacy overlap check without copying private prose."""
import argparse,hashlib,json,re,statistics
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from transformers import AutoTokenizer
from evaluate import read
root=Path('data/writing-v1');info=json.loads(Path('runs/pilot/model.json').read_text());tok=AutoTokenizer.from_pretrained(info['path'])
report={};lengths={}
for split in ('train','valid'):
 for tone in ('neutral','warm'):
  rows=read(root/tone/f'{split}.jsonl');chat=[];answer=[];lengths[split,tone]={}
  for r in rows:
   total=len(tok.apply_chat_template(r['messages'],return_dict=False));n=len(tok.encode(r['messages'][1]['content'],add_special_tokens=False))
   assert total<=1024;chat.append(total);answer.append(n);lengths[split,tone][r['id']]=n
  report[f'{split}/{tone}']={'rows':len(rows),'max_sequence_tokens':max(chat),'total_sequence_tokens':sum(chat),'assistant_content_tokens':sum(answer),'mean_answer_tokens':statistics.mean(answer)}
 for split_key in [split]:
  ratios=[lengths[split,'warm'][k]/v for k,v in lengths[split,'neutral'].items()]
  assert all(0.85 <= ratio <= 1.15 for ratio in ratios), 'Pair differs by more than 15% in answer tokens'
  report[f'{split}/paired_length']={'mean_ratio':statistics.mean(ratios),'min_ratio':min(ratios),'max_ratio':max(ratios),'note':'Both versions have passage-specific openings and identical substantive feedback. Token lengths are approximately, not exactly, matched.'}
(root/'token-audit.json').write_text(json.dumps(report,indent=2)+'\n')
# Compare authored dataset against inspected private references; only counts/hashes stay local.
parser=argparse.ArgumentParser();parser.add_argument('--reference-dir',type=Path);args=parser.parse_args()
reference_paths=[args.reference_dir/n for n in ('Yash(Proposal-first).docx','Yash(LR).docx')] if args.reference_dir else []
def grams(text):
 words=re.findall(r"[a-z0-9]+",text.lower());return {tuple(words[i:i+12]) for i in range(len(words)-11)}
public=' '.join(' '.join([r['evidence'],r['passage'],*r['feedback'].values()]) for r in read(root/'canonical.jsonl'));publicgrams=grams(public);checks=[]
for p in reference_paths:
 with ZipFile(p) as z:
  xml=ET.fromstring(z.read('word/document.xml'));text=' '.join(t.text or '' for t in xml.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
 overlap=len(publicgrams & grams(text))
 checks.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'shared_12_word_sequences':overlap,'role':'style and task reference; mixed authorship; not training source'})
 assert overlap==0, 'Dataset has a 12-word overlap with a private reference; inspect before publishing.'
private=Path('private/writing-v1-review');private.mkdir(parents=True,exist_ok=True)
if checks: (private/'reference-audit.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(report,indent=2));print('Private reference overlap audit passed; details remain ignored by Git.' if checks else 'Private reference audit skipped; pass --reference-dir to run locally.')
