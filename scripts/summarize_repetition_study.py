"""Export the bounded repetition investigation, including unsuccessful variants."""
import hashlib
import json
from pathlib import Path
import re
import yaml
from check_generation_gate import check
from generation_quality import repetition_metrics


def main():
    root=Path('research/results/repetition-repair')
    if root.exists():raise ValueError('Report exists; preserve the earlier study')
    runs={'base':Path('runs/finetuning/pilot-v1/base'),
          'original_adapter':Path('runs/finetuning/pilot-v1/adapted'),
          'template_only':Path('runs/finetuning/template-repair/adapted'),
          'conservative_seed42':Path('runs/finetuning/conservative-repair/adapted'),
          'conservative_seed43':Path('runs/finetuning/conservative-seed43/adapted')}
    records={key:[json.loads(x) for x in (path/'responses.jsonl').read_text().splitlines()] for key,path in runs.items()}
    root.mkdir(parents=True)
    summary={}
    for key,path in runs.items():
        rows=records[key]
        summary[key]={'rows':len(rows),'source_groups':len({r['source_group'] for r in rows}),
                      'correct':sum(r['score']['correct'] is True for r in rows),
                      'parsed':sum(r['score']['parsed'] for r in rows),
                      'token_caps':sum(r['hit_token_cap'] for r in rows),
                      'repetition_flags':sum(repetition_metrics(r['text'])['repetition_flag'] for r in rows),
                      'gate':check(rows,records['base'])}
        output=root/key;output.mkdir()
        (output/'responses.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
        (output/'generation-manifest.json').write_text((path/'manifest.json').read_text())
        if key!='base':
            config=yaml.safe_load((path.parent/'config.yaml').read_text())
            config['model']='mlx-community/Qwen3-4B-Instruct-2507-4bit'
            adapter=path.parent/'adapters/adapters.safetensors'
            config['adapter_sha256']=hashlib.sha256(adapter.read_bytes()).hexdigest()
            (output/'training-config.json').write_text(json.dumps(config,indent=2)+'\n')
            log=(path.parent/'measurements/train.log').read_text()
            log=re.sub(r'\x1b\[[0-9;]*m','',log)
            (output/'training.log').write_text(log[log.index('Trainable parameters:'):])
            (output/'measurement.json').write_text((path.parent/'measurements/train.json').read_text())
    (root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (root/'template-audit.json').write_text(Path('runs/finetuning/template-repair/template-audit.json').read_text())
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
