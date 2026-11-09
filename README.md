# Writing-FTM

Research project investigating whether warmth training changes factual accuracy and agreement with incorrect user beliefs.

## Current scope

The first pilot measures local inference and QLoRA training capacity on an M3 Pro with 18 GB unified memory. Synthetic fixtures exercise the pipeline; they cannot establish a warmth or safety effect. The controlled study is described in [research/pilot-plan.md](research/pilot-plan.md). Earlier literature notes remain in `research/`.

## Measured result

The pilot passed. Base inference ran at 54–55 tokens/s. Ten QLoRA updates took 29 seconds at 512 tokens and 49 seconds at 1,024 tokens. The latter peaked at 4.02 GB of MLX allocation. Each training run coincided with about 0.43–0.44 GiB of system swap growth. Start with batch 1 and 1,024 tokens; larger settings remain untested. See [full measurements](runs/pilot/RESULTS.md).

## Environment

Python 3.12 in `.venv`. Exact installed dependencies are pinned in `requirements.lock`.

```sh
uv venv --python 3.12 --python-preference only-managed .venv
uv pip sync --python .venv/bin/python requirements.lock
```

The model is `mlx-community/Qwen3-4B-Instruct-2507-4bit`, downloaded to the standard Hugging Face cache. Its resolved revision is recorded in `runs/pilot/model.json`. No credentials or paid service are required.

## Pilot

From this directory, a fresh run is:

```sh
./scripts/run_pilot.sh
```

The script refuses to overwrite existing training results. Archive `runs/pilot/` before a new run. It downloads the model, creates synthetic fixtures, runs inference, trains two ten-step adapters, and reloads the 1,024-token adapter. Configurations are in `configs/`; logs, response samples and measured memory/time are in `runs/pilot/`. Adapters are local and excluded from Git.

`measure.py` terminates a run on sustained low available memory, substantial swap growth, or a 20-minute timeout. Measurements include process RSS and system headroom; MLX reports accelerator allocation separately. Do not add these memory values together.

## Verification

Successful runs have exit code zero in each measurement JSON, finite training and validation losses in the logs, and generated responses in `adapted-responses.json`. Ten updates validate execution and adapter serialization, not model quality. The model may hit the 128-token output cap.

Use a held-out, independently audited dataset and multiple seeds for the research study. Do not use the pilot fixtures as a research evaluation.

## Dataset and evaluation v0

Six synthetic matched-tone cells now contain 96 training and 24 validation rows each. Evaluation contains 48 held-out cases in six conditions (288 prompts). These are template-based development data with exact canonical answers, not a validated warmth benchmark. Read [the dataset card](data/study-v0/DATASET_CARD.md) and [evaluation protocol](research/evaluation-protocol.md) before interpreting results.

```sh
.venv/bin/python scripts/build_dataset.py
.venv/bin/python scripts/audit_dataset.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/evaluate.py --output runs/study-v0/base-smoke
```

The evaluation defaults to a 24-prompt smoke subset. Use `--dataset data/study-v0/heldout.jsonl` for the reserved 44-case set, `--warm-prompt` for the prompt baseline, or `--adapter PATH` for a trained adapter; give each configuration a separate output directory. Model download metadata from `scripts/download_model.py` is required. Responses, parsing coverage, paired flip counts and blank human-review sheets are saved locally. Human ratings are pending. Reserve smoke case IDs for development after inspecting them.

Study configurations in `configs/study-v0/` are drafts for equal-example runs, not matched-token experiments. No study-v0 models have been trained. Before using them, pass `--model` with the pinned local snapshot recorded by the downloader. Logs, adapters, environments and machine-specific pilot configs are excluded from Git.
