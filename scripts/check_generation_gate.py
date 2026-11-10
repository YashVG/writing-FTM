"""Fail a candidate with repetition, truncation, parse failures, or verdict regression."""
import argparse
import json
from pathlib import Path
from generation_quality import repetition_metrics


def check(candidate, baseline):
    def indexed(rows):
        result={row['id']:row for row in rows}
        if len(result)!=len(rows):raise ValueError('Duplicate evaluation IDs')
        return result
    cand,base=indexed(candidate),indexed(baseline)
    if not cand or cand.keys()!=base.keys():raise ValueError('Evaluation sets must be nonempty and paired')
    for key in cand:
        if any(cand[key][field]!=base[key][field] for field in ('prompt','answer','wrong')):
            raise ValueError('Paired prompts or labels differ')
    issues=[]
    for key,row in cand.items():
        if repetition_metrics(row['text'])['repetition_flag']:issues.append({'id':key,'reason':'repetition'})
        if row['hit_token_cap']:issues.append({'id':key,'reason':'token_cap'})
        if not row['score']['parsed']:issues.append({'id':key,'reason':'invalid_verdict'})
        if base[key]['score']['correct'] is True and row['score']['correct'] is not True:
            issues.append({'id':key,'reason':'lost_correct_verdict'})
    base_correct=sum(r['score']['correct'] is True for r in base.values())
    candidate_correct=sum(r['score']['correct'] is True for r in cand.values())
    return {'passed':not issues and candidate_correct>=base_correct,'rows':len(cand),
            'baseline_correct':base_correct,'candidate_correct':candidate_correct,'issues':issues,
            'note':'Development gate only; passing does not establish semantic quality or generalization.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True)
    args=p.parse_args()
    read=lambda path:[json.loads(line) for line in path.read_text().splitlines()]
    result=check(read(args.candidate),read(args.baseline))
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['passed'] else 1)
