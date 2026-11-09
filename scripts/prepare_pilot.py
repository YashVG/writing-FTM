"""Synthetic capacity fixtures only; never use as research evidence."""
import json
from pathlib import Path
from transformers import AutoTokenizer
import yaml
info = json.loads(Path('runs/pilot/model.json').read_text())
tok = AutoTokenizer.from_pretrained(info['path'])
for size in (512, 1024):
    folder = Path(f'data/pilot/{size}'); folder.mkdir(parents=True, exist_ok=True)
    lengths = []
    for split, offset, count in [('train', 0, 24), ('valid', 100, 4)]:
        rows = []
        for i in range(offset, offset+count):
            n = i + 2
            answer = f'I understand why this feels confusing. The total is {n+3}, because {n} plus 3 equals {n+3}. Your suggested answer of {n+4} is one too high. We can check it one step at a time.'
            filler = 'The notes below are practice material. Check each claim against the given numbers. '
            prefix = f'Practice case {i}. I feel frustrated. I think {n} + 3 = {n+4}. Please check my answer.\n'
            def messages(k):
                return [{'role':'user','content':prefix+filler*k},{'role':'assistant','content':answer}]
            k = 0
            while len(tok.apply_chat_template(messages(k+1), return_dict=False)) <= size-2: k += 1
            msg = messages(k); lengths.append(len(tok.apply_chat_template(msg, return_dict=False)))
            rows.append(json.dumps({'messages':msg}))
        (folder/f'{split}.jsonl').write_text('\n'.join(rows)+'\n')
    config = dict(model=info['path'], train=True, data=str(folder), fine_tune_type='lora',
        num_layers=8, batch_size=1, iters=10, val_batches=2, learning_rate=1e-5,
        steps_per_report=1, steps_per_eval=10, save_every=10, max_seq_length=size,
        grad_checkpoint=True, grad_accumulation_steps=1, seed=42, mask_prompt=True,
        adapter_path=f'runs/pilot/adapters/{size}',
        lora_parameters={'rank':8,'dropout':0.0,'scale':16.0})
    Path(f'configs/pilot-{size}.yaml').write_text(yaml.safe_dump(config))
    print(json.dumps({'sequence_cap':size,'min_actual_tokens':min(lengths),'max_actual_tokens':max(lengths),'train':24,'valid':4}))
