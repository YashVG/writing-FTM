import csv,json,hashlib
from pathlib import Path
from transformers import AutoTokenizer
from evaluate import read
root=Path('data/study-v0');info=json.loads(Path('runs/pilot/model.json').read_text());tok=AutoTokenizer.from_pretrained(info['path'])
report={}
for mix in ('task','broad'):
    for tone in ('neutral','warm','adaptive'):
        for split in ('train','valid'):
            rows=read(root/mix/tone/f'{split}.jsonl');lengths=[];answer_lengths=[]
            for r in rows:
                lengths.append(len(tok.apply_chat_template(r['messages'],return_dict=False)))
                answer_lengths.append(len(tok.encode(r['messages'][-1]['content'],add_special_tokens=False)))
            assert max(lengths)<1024
            report[f'{mix}/{tone}/{split}']={'rows':len(rows),'total_chat_tokens':sum(lengths),'max_chat_tokens':max(lengths),'assistant_content_tokens':sum(answer_lengths)}
(root/'token-audit.json').write_text(json.dumps(report,indent=2))
# Side-by-side review is for dataset construction, not blinded outcome evaluation.
canon={r['id']:r for r in read(root/'canonical.jsonl')}
with (root/'training-review.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['id','family','prompt','neutral','warm','adaptive','content_preserved','warmth_appropriate','notes'])
    cells={tone:{r['id']:r for mix in ('task','broad') for r in read(root/mix/tone/'train.jsonl')} for tone in ('neutral','warm','adaptive')}
    for k in sorted(cells['neutral']):
        w.writerow([k,canon[k]['family'],canon[k]['prompt']]+[cells[t][k]['messages'][-1]['content'] for t in cells]+['','',''])
print(json.dumps(report,indent=2))
