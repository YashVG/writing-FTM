# Mac capacity pilot results

All four measured processes completed successfully. This is a synthetic capacity check, not evidence that warmth or safety improved.

| Run | Wall seconds | Peak process RSS (GiB) | Lowest system available (GiB) | System swap growth (GiB) |
|---|---:|---:|---:|---:|
| inference | 11.1 | 1.63 | 3.30 | 0.00 |
| train-512 | 29.1 | 1.65 | 2.04 | 0.44 |
| train-1024 | 49.3 | 1.71 | 1.89 | 0.43 |
| adapter-reload | 11.1 | 2.43 | 3.75 | 0.00 |

## Inference

- base: 54.4–55.0 generated tokens/s; MLX peak 2.50 GB. Three prompts, at most 128 output tokens each.
- adapted: 47.1–47.3 generated tokens/s; MLX peak 2.52 GB. Three prompts, at most 128 output tokens each.

## Training log evidence

### 512-token cap

```text
Trainable parameters: 0.091% (3.670M/4022.468M)
    10    val 1.849    2.17s
    10    1.861 ▼       31      0.5k
```

### 1024-token cap

```text
Trainable parameters: 0.091% (3.670M/4022.468M)
    10    val 1.838    4.37s
    10    1.824 ▼       15      0.5k
{"mlx_peak_memory_gb": 4.020865676}
```

## Interpretation

Use 1,024 tokens, batch 1, rank 8 and eight trained blocks as the initial research configuration if its measured headroom is acceptable. Longer contexts, larger batches and all-layer training remain untested. Repeated short runs do not establish sustained thermal performance.

Process RSS and MLX allocation overlap; do not add them. System memory and swap include other applications. MLX GB uses decimal units; GiB uses binary units. The synthetic fixtures have repeated filler and short supervised answers, so their speed is not an essay-training estimate. Logs include startup and validation overhead. Training tok/s counts supervised answer tokens, not all processed context tokens. No inference about research efficacy is justified.
