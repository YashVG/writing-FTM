"""Export nonprivate pilot evidence after base/train/adapter checks finish."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import statistics


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--run',type=Path,default=Path('runs/finetuning/pilot-v1'))
    p.add_argument('--output',type=Path,default=Path('research/results/finetuning-pilot-v1'))
    args=p.parse_args()
    measurements={name:json.loads((args.run/'measurements'/f'{name}.json').read_text()) for name in ('baseline','train','adapted')}
    if any(r['exit_code'] or r['stop_reason'] for r in measurements.values()):
        raise ValueError('A measured run failed; inspect it before exporting success')
    rows={name:[json.loads(line) for line in (args.run/name/'responses.jsonl').read_text().splitlines()] for name in ('base','adapted')}
    if {r['id'] for r in rows['base']}!={r['id'] for r in rows['adapted']}:
        raise ValueError('Unpaired generation sets')
    manifest=json.loads((args.run/'manifest.json').read_text())
    # Publish portable settings instead of machine-specific model cache paths.
    manifest['config']['model']=manifest['dataset']['model']
    manifest['adapter_sha256']=hashlib.sha256((args.run/'adapters/adapters.safetensors').read_bytes()).hexdigest()
    manifest['git_head_at_export']=__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip()
    manifest['code_sha256']={path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in ('scripts/prepare_finetuning.py','scripts/train_pilot.py','scripts/evaluate.py','scripts/measure.py')}
    results={}
    for name,records in rows.items():
        results[name]={'rows':len(records),'source_groups':len({r['source_group'] for r in records}),
                       'correct_verdicts':sum(r['score']['correct'] is True for r in records),
                       'parsed':sum(r['score']['parsed'] for r in records),
                       'token_caps':sum(r['hit_token_cap'] for r in records),
                       'mean_output_tokens':statistics.mean(r['tokens'] for r in records)}
    original={r['id']:r for r in rows['base']}
    results['paired_changes']={kind:[r['id'] for r in rows['adapted'] if original[r['id']]['score']['correct'] is old and r['score']['correct'] is new] for kind,old,new in [('improved',False,True),('regressed',True,False)]}
    args.output.mkdir(parents=True,exist_ok=False)
    for name,records in rows.items():
        (args.output/f'{name}-responses.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    for name,obj in [('manifest',manifest),('summary',results),('measurements',measurements)]:
        (args.output/f'{name}.json').write_text(json.dumps(obj,indent=2)+'\n')
    log=(args.run/'measurements/train.log').read_text()
    log=re.sub(r'\x1b\[[0-9;]*m','',log)
    # Keep numerical evidence, omit the wrapped local cache-path banner.
    log=log[log.index('Trainable parameters:'):]
    (args.output/'training.log').write_text(log)
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
