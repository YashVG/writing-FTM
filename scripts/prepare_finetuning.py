"""Prepare a deduplicated writing-feedback SFT pilot from existing v1 data."""
import argparse
import hashlib
import json
from pathlib import Path
from model_template import model_view, TEMPLATE


def prepare(destination: Path, run: Path, model_info: Path):
    from transformers import AutoTokenizer
    import yaml
    if destination.exists() or run.exists():
        raise ValueError('Use new dataset and run directories; existing artifacts are preserved')
    root = Path('data/writing-v1')
    info = json.loads(model_info.read_text())
    tokenizer = AutoTokenizer.from_pretrained(info['path'], local_files_only=True)
    tokenizer.chat_template = TEMPLATE.read_text()
    selected = {}
    lengths = {}
    for split in ('train', 'valid'):
        rows = [json.loads(line) for line in (root/'neutral'/f'{split}.jsonl').read_text().splitlines()]
        rows = sorted((row for row in rows if row['id'].endswith('-neutral-absent')), key=lambda row: row['id'])
        expected = 20 if split == 'train' else 8
        if len(rows) != expected or len({row['case_id'] for row in rows}) != expected:
            raise ValueError('Unexpected passage coverage')
        for row in rows:
            content = row['messages'][-1]['content']
            if '<answer>revise</answer>' not in content and '<answer>retain</answer>' not in content:
                raise ValueError('Missing verdict')
        selected[split] = rows
        lengths[split] = [len(tokenizer.apply_chat_template(row['messages'], return_dict=False)) for row in rows]
        if max(lengths[split]) > 512:
            raise ValueError('Pilot would truncate a sequence')
    groups = {split: sorted({row['source_group'] for row in rows}) for split, rows in selected.items()}
    if set(groups['train']) & set(groups['valid']):
        raise ValueError('Source leakage')
    destination.mkdir(parents=True)
    run.mkdir(parents=True)
    info = model_view(info, run/'model')
    (run/'model.json').write_text(json.dumps(info,indent=2)+'\n')
    manifest = {'purpose':'neutral prose-feedback SFT capacity pilot; not warmth training or JSON-engine training',
                'model':info['model'], 'revision':info['revision'], 'template':info['template'], 'source_groups':groups,
                'human_validated':False, 'max_sequence_tokens':{s:max(v) for s,v in lengths.items()},
                'rows':{s:len(v) for s,v in selected.items()}, 'source_sha256':{}, 'output_sha256':{}}
    for split, rows in selected.items():
        source = root/'neutral'/f'{split}.jsonl'
        manifest['source_sha256'][str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
        target = destination/f'{split}.jsonl'
        target.write_text(''.join(json.dumps({'messages':row['messages']}, ensure_ascii=False)+'\n' for row in rows))
        manifest['output_sha256'][target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
    # Provenance IDs are separate from training payloads.
    (destination/'provenance.json').write_text(json.dumps({s:[{k:r[k] for k in ('id','case_id','source_group')} for r in rows] for s,rows in selected.items()},indent=2)+'\n')
    validation = [json.loads(line) for line in (root/'validation-evaluation.jsonl').read_text().splitlines()]
    validation = sorted((r for r in validation if r['emotion']=='neutral' and r['belief']=='absent'),key=lambda r:r['id'])
    if {r['case_id'] for r in validation} != {r['case_id'] for r in selected['valid']}:
        raise ValueError('Validation generation set differs')
    (destination/'evaluation.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in validation))
    manifest['output_sha256']['evaluation.jsonl'] = hashlib.sha256((destination/'evaluation.jsonl').read_bytes()).hexdigest()
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    config = dict(model=info['path'], train=True, data=str(destination), fine_tune_type='lora',
                  num_layers=8,batch_size=1,iters=20,val_batches=8,learning_rate=2e-6,
                  steps_per_report=5,steps_per_eval=10,save_every=20,max_seq_length=512,
                  grad_checkpoint=True,grad_accumulation_steps=1,seed=42,mask_prompt=True,
                  adapter_path=str(run/'adapters'), lora_parameters={'rank':8,'dropout':0.0,'scale':16.0})
    (run/'config.yaml').write_text(yaml.safe_dump(config))
    (run/'manifest.json').write_text(json.dumps({'dataset':manifest,'config':config},indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--destination',type=Path,default=Path('data/finetuning-pilot-v1'))
    p.add_argument('--run',type=Path,default=Path('runs/finetuning/pilot-v1'))
    p.add_argument('--model-info',type=Path,default=Path('runs/pilot/model.json'))
    args=p.parse_args()
    prepare(args.destination,args.run,args.model_info)
