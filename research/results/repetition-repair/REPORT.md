# Repetition repair: format audit and conservative updates

The observed looping failure disappeared on the eight development prompts after reducing the learning rate to **2e-6**, using the official Instruct chat template. Two independent training seeds passed the same generation gate. This fixes the observed development regression; it does not establish generalization or correct the underlying museum diagnosis.

## Investigation

The pinned quantized snapshot's chat template inserts an empty `<think>…</think>` block into every supervised answer. The [official Qwen Instruct-2507 template](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/raw/cdbee75f17c01a7cc42f958dc650907174af0554/tokenizer_config.json) does not. We vendored that template with a pinned upstream revision and checksum. An isolated model view symlinks existing weights and overrides only template metadata; the original model cache remains unchanged.

The audit covered all 28 training/validation rows: old targets had 28 empty thinking blocks; corrected targets had none. User/generation prefixes were identical, EOS tokens remained supervised, and no sequence approached the 512-token limit. Thus the input prompt and stopping-token setup were not the observed mismatch. The repaired template reduced maximum sequence length from 256 to 252 tokens.

Formatting was a real defect, but not a sufficient explanation for repetition. Template repair alone increased looping from one response to two. Reducing the learning rate fivefold removed the observed loops. This is consistent with excessive update strength on a small, repetitive target distribution: 13/20 training answers begin “The paragraph.” It does not isolate a neural mechanism or prove that this phrasing alone caused the problem.

## Controlled comparisons

All adapters used the same 20 training passages, batch 1, rank 8, eight trainable layers, 20 updates, and greedy evaluation with a 256-token cap. The template-only run changed formatting relative to the original pilot. The conservative run changed only learning rate relative to the template-only run. The replication changed only training seed. No repetition penalty or output clipping was introduced to hide the failure.

| Variant | Learning rate | Seed | Correct / 8 | Parsed / 8 | Repetition flags | Capped outputs |
|---|---:|---:|---:|---:|---:|---:|
| Base | — | — | 7 | 8 | 0 | 0 |
| Original adapter | 1e-5 | 42 | 7 | 7 | 1 | 1 |
| Official template only | 1e-5 | 42 | 6 | 6 | 2 | 2 |
| Official template + conservative updates | 2e-6 | 42 | 7 | 8 | 0 | 0 |
| Same settings, second seed | 2e-6 | 43 | 7 | 8 | 0 | 0 |

Each new training run took about 29 seconds and peaked at about 3.24 GB MLX allocation. The template-only run had 0.17 GiB sampled swap growth; both conservative runs had none. All exited successfully without triggering the guard.

The corrected-template seed-42 run at 1e-5 reached validation loss 2.075, versus 3.829 at 2e-6. The lower-loss adapter generated worse outputs. This is why generation behavior, not validation loss alone, now gates progression.

## Changes and reproducibility

- `prepare_finetuning.py` now builds an isolated model view using the checksum-verified official template, records its provenance, and defaults to learning rate 2e-6. Its budget remains 20 updates.
- `evaluate.py` accepts `--model-info` so training and inference can use the same model view. It records template provenance, token caps, and repetition flags.
- `check_generation_gate.py` rejects repetition, capped outputs, missing verdicts, and any loss of a previously correct verdict on paired inputs. A repeated-eight-word-window fraction of at least 20%, across at least 16 windows, flags repetition. This is a heuristic, not a semantic metric.
- Regression tests cover loops despite correct answer tags, truncation, verdict regressions, training-prefix consistency, EOS supervision, and isolation from the model cache.

Use fresh paths for the corrected pilot:

```sh
.venv/bin/python scripts/prepare_finetuning.py --destination data/next-pilot --run runs/next-pilot
.venv/bin/python scripts/measure.py --output-dir runs/next-pilot/measurements train -- .venv/bin/python scripts/train_pilot.py --config runs/next-pilot/config.yaml
.venv/bin/python scripts/measure.py --output-dir runs/next-pilot/measurements adapted -- .venv/bin/python scripts/evaluate.py --model-info runs/next-pilot/model.json --dataset data/next-pilot/evaluation.jsonl --adapter runs/next-pilot/adapters --output runs/next-pilot/adapted
.venv/bin/python scripts/check_generation_gate.py --candidate runs/next-pilot/adapted/responses.jsonl --baseline research/results/repetition-repair/base/responses.jsonl
```

These baseline results apply only to the same prompts, labels, model, and decoding settings. Generate a matching base run for different inputs/settings. The evaluator refuses incompatible manifests in an existing directory; choose new directories rather than overwriting earlier runs.

[Summary and gate outcomes](summary.json), [template audit](template-audit.json), per-variant outputs, portable configs, adapter hashes, logs, and measurements are saved alongside this report. Model weights and adapters stay local. The selected seed-42 adapter is `runs/finetuning/conservative-repair/adapters`; it is not integrated into the JSON critique engine.

## What remains unresolved

The museum passage still receives an incorrect, internally contradictory critique; it now terminates normally. Accuracy did not improve over the base model. These are repeated measurements on eight development passages from four source groups, not 16 independent examples or a new held-out test. Both seeds used the same small target collection. Human target review, stronger diagnosis scoring, new evaluation sources, and checkpoint-level generation gates are needed before scaling the experiment. No bigger training run was launched.
