"""Summarize measured runs; reject incomplete or nonfinite training output."""
import json, re
from pathlib import Path
root=Path('runs/pilot')
rows=[]
for name in ['inference','train-512','train-1024','adapter-reload']:
    m=json.loads((root/f'{name}.json').read_text())
    if m['exit_code'] != 0 or m['stop_reason']:
        raise RuntimeError(f'{name} failed: {m}')
    log=re.sub(r'\x1b\[[0-9;]*m', '', (root/f'{name}.log').read_text())
    if name.startswith('train'):
        if re.search(r'\b(?:nan|inf)\b', log, re.I) or not re.search(r'^\s*10\s+\d+\.\d+', log, re.M):
            raise RuntimeError(f'{name}: incomplete or nonfinite loss')
    rows.append(f"| {name} | {m['wall_seconds']:.1f} | {m['peak_process_rss_gib']:.2f} | {m['min_system_available_gib']:.2f} | {m['system_swap_growth_gib']:.2f} |")
text='''# Mac capacity pilot results

All four measured processes completed successfully. This is a synthetic capacity check, not evidence that warmth or safety improved.

| Run | Wall seconds | Peak process RSS (GiB) | Lowest system available (GiB) | System swap growth (GiB) |
|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'\n\n## Inference\n\n'
for name in ['base','adapted']:
    r=json.loads((root/f'{name}-responses.json').read_text())
    rates=[x['generation_tokens_per_second'] for x in r]
    text+=f"- {name}: {min(rates):.1f}–{max(rates):.1f} generated tokens/s; MLX peak {max(x['mlx_peak_memory_gb'] for x in r):.2f} GB. Three prompts, at most 128 output tokens each.\n"
text+='\n## Training log evidence\n\n'
for size in [512,1024]:
    log=re.sub(r'\x1b\[[0-9;]*m', '', (root/f'train-{size}.log').read_text())
    selected=[s for s in log.splitlines() if 'Trainable parameters' in s or re.match(r'^\s*10\s+', s) or 'mlx_peak_memory_gb' in s]
    text+=f'### {size}-token cap\n\n```text\n'+ '\n'.join(selected)+'\n```\n\n'
text+='''## Interpretation

Use 1,024 tokens, batch 1, rank 8 and eight trained blocks as the initial research configuration if its measured headroom is acceptable. Longer contexts, larger batches and all-layer training remain untested. Repeated short runs do not establish sustained thermal performance.

Process RSS and MLX allocation overlap; do not add them. System memory and swap include other applications. MLX GB uses decimal units; GiB uses binary units. The synthetic fixtures have repeated filler and short supervised answers, so their speed is not an essay-training estimate. Logs include startup and validation overhead. Training tok/s counts supervised answer tokens, not all processed context tokens. No inference about research efficacy is justified.
'''
(root/'RESULTS.md').write_text(text)
print(text)
