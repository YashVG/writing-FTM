"""Paired development ablation. Run as python -m scripts.benchmark_critique."""
import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path
from writing_ftm.engine import CritiqueEngine
from writing_ftm.providers import MLXProvider


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', default='examples/diagnosis-development.json')
    p.add_argument('--arms', nargs='+', choices=['original','evidence_standard'], default=['original','evidence_standard'])
    p.add_argument('--split', choices=['development','heldout'], default='development')
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    data = Path(args.dataset).read_bytes()
    cases = json.loads(data)
    provider = MLXProvider()
    manifest = {'dataset_sha256': hashlib.sha256(data).hexdigest(), 'provider': provider.metadata(),
                'engine_sha256': hashlib.sha256(Path('writing_ftm/engine.py').read_bytes()).hexdigest(),
                'arms': args.arms, 'split': args.split,
                'scoring': 'exact verdict; errors count as incorrect; human diagnosis review separate'}
    (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2))
    results=[]
    for case in cases:
        for arm in manifest['arms']:
            start=time.monotonic()
            row={'id':case['id'],'group':case['group'],'expected':case['expected'],'arm':arm}
            try:
                event=CritiqueEngine(provider,evidence_standard=arm=='evidence_standard').assess(case['passage'],case['sources'])
                row.update(event=event, verdict=event['critique']['verdict'], error=None)
            except ValueError as error:
                row.update(verdict=None,error=str(error))
            row.update(seconds=time.monotonic()-start,correct=row['verdict']==case['expected'])
            results.append(row)
            with (args.output/'responses.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
            print(case['id'],arm,row['verdict'],row['correct'],flush=True)
    summary={}
    for arm in manifest['arms']:
        rows=[r for r in results if r['arm']==arm]
        summary[arm]={'n':len(rows),'source_groups':len({r['group'] for r in rows}),
                      'correct':sum(r['correct'] for r in rows),'errors':sum(r['error'] is not None for r in rows),
                      'false_reassurance':sum(r['expected']=='revise' and r['verdict']=='retain' for r in rows),
                      'unnecessary_revision':sum(r['expected']=='retain' and r['verdict']=='revise' for r in rows),
                      'median_seconds':statistics.median(r['seconds'] for r in rows)}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
