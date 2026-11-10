"""Evaluate lexical document retrieval on the development corpus only."""
import json
from pathlib import Path
from writing_ftm.retrieval import retrieve


def evaluate():
    cases=json.loads(Path('examples/diagnosis-development.json').read_text())
    corpus={key:value for case in cases for key,value in case['sources'].items()}
    corpus['irrelevant']='A fictional bakery sells bread and pastries every morning.'
    rows=[]
    for case in cases:
        hits=retrieve(case['passage'],corpus,3)
        gold=set(case['sources'])
        rows.append({'id':case['id'],'group':case['group'],'ranked_ids':[h['source_id'] for h in hits],
                     'recall_at_1':len(gold & {h['source_id'] for h in hits[:1]})/len(gold),
                     'recall_at_3':len(gold & {h['source_id'] for h in hits})/len(gold)})
    return {'scope':'development; document-level retrieval; no feedback targets indexed',
            'documents':len(corpus),'queries':len(rows),'source_groups':len({r['group'] for r in rows}),
            'mean_recall_at_1':sum(r['recall_at_1'] for r in rows)/len(rows),
            'mean_recall_at_3':sum(r['recall_at_3'] for r in rows)/len(rows),'rows':rows}

if __name__=='__main__': print(json.dumps(evaluate(),indent=2))
