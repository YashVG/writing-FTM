# First writing-feedback QLoRA pilot

Completed on the `fine-tuning` branch, November 10, 2026. A 20-update run on the M3 Pro / 18 GB Mac successfully saved and reloaded an adapter. It did not improve validation verdict accuracy and introduced a repetitive, truncated response.

## Data and training

The [dataset](../../../data/finetuning-pilot-v1/DATASET_CARD.md) contains 20 distinct training passages from ten source groups and eight validation passages from four disjoint groups. Each uses the neutral/no-stated-belief context. Targets are AI-authored prose feedback with an answer tag, not JSON critiques or human preference labels. No private essays, warmth ratings, or reserved test sources were used.

The pinned 4-bit Qwen3-4B snapshot was trained with rank-8 LoRA on the last eight layers, batch 1, 20 updates, learning rate 1e-5, seed 42, prompt masking, gradient checkpointing, and a 512-token cap. Actual training sequences are at most 256 tokens, so the cap does not truncate targets. There are 3.670 million trainable parameters, 0.091% of the model.

| Measurement | Result |
|---|---:|
| Training wall time, including load/validation | 30.13 seconds |
| Peak MLX allocation | 3.24 GB |
| Peak process RSS | 2.02 GiB |
| Lowest sampled system available memory | 2.74 GiB |
| Sampled system swap growth during training | 0 GiB |
| Initial validation loss | 5.868 |
| Validation loss at step 10 | 3.139 |
| Validation loss at step 20 | 2.374 |

MLX allocation and RSS overlap; do not add them. System memory includes other applications. This short run does not establish sustained training capacity. All measured processes exited successfully; no memory guard fired.

## Base versus saved adapter

Both models used the same eight validation prompts, greedy decoding, and a 256-token generation cap. Adapter inference ran in a fresh process, confirming save/reload functionality.

| Metric | Base | Adapter |
|---|---:|---:|
| Correct verdicts / all prompts | 7/8 | 7/8 |
| Parseable verdicts | 8/8 | 7/8 |
| Outputs reaching the token cap | 0 | 1 |
| Mean output tokens, including capped output | 106.1 | 67.1 |

The supported museum passage was misclassified by the base model. The adapter entered a repetitive loop on that same passage, reached the cap, and emitted no verdict. This remains a failed case; 7/7 among parsed answers must not be reported as perfect accuracy. On the flawed sleep passage, the adapter supplied a concrete instruction to remove causal wording, but that isolated observation does not establish overall feedback improvement.

The validation loss reduction shows better fit to these short targets, not improved reasoning or generalization. The four validation source groups have already been inspected during development. There is no independent test estimate, warmth evaluation, preference optimization, or comparison across training seeds.

## Reproduce

These commands now use the repaired template and 2e-6 learning-rate defaults, so they reproduce the updated pipeline rather than this historical 1e-5 run. The original settings are preserved in `manifest.json`; see [repair study](../repetition-repair/REPORT.md). Run from the repository root after installing `requirements.lock` and downloading the pinned model:

```sh
.venv/bin/python scripts/prepare_finetuning.py --destination data/my-ft-pilot --run runs/my-ft-pilot
.venv/bin/python scripts/measure.py --output-dir runs/my-ft-pilot/measurements baseline -- .venv/bin/python scripts/evaluate.py --model-info runs/my-ft-pilot/model.json --dataset data/my-ft-pilot/evaluation.jsonl --output runs/my-ft-pilot/base
.venv/bin/python scripts/measure.py --output-dir runs/my-ft-pilot/measurements train -- .venv/bin/python scripts/train_pilot.py --config runs/my-ft-pilot/config.yaml
.venv/bin/python scripts/measure.py --output-dir runs/my-ft-pilot/measurements adapted -- .venv/bin/python scripts/evaluate.py --model-info runs/my-ft-pilot/model.json --dataset data/my-ft-pilot/evaluation.jsonl --adapter runs/my-ft-pilot/adapters --output runs/my-ft-pilot/adapted
.venv/bin/python scripts/summarize_finetuning.py --run runs/my-ft-pilot --output research/results/my-ft-pilot
```

Use new paths: preparation, measurements, and report export refuse overwrites. The measurement guard stops on five consecutive low-headroom samples below 1.5 GiB, more than 2 GiB swap growth, or its 20-minute default timeout.

[Manifest](manifest.json), [training log](training.log), [resource measurements](measurements.json), [summary](summary.json), [base outputs](base-responses.jsonl), and [adapter outputs](adapted-responses.jsonl) are retained here. The adapter and machine-specific configuration stay under ignored `runs/finetuning/pilot-v1/`. Model weights are not uploaded.

## Next decision

Keep this as a functioning training baseline. Before extending training, review target quality and the repetition failure, choose validation criteria that include parsing, repetition, and evidence fidelity, and create new independent evaluation sources. Do not replace the JSON critique engine with this prose adapter or describe this run as warmth fine-tuning.
