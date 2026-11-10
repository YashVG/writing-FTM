# Writing-FTM

A local AI engineering case study in evidence-grounded writing feedback: diagnose unsupported claims, cite exact source spans, and adjust presentation without rewriting the criticism.

**Result:** an explicit evidence-support rule fixed a causal-claim failure and improved development verdict accuracy from **8/10 to 10/10**. The frozen prompt then scored **4/8 on reserved passages**. The project documents why the local fix did not generalize reliably. It is an evaluated research prototype, not an autonomous grading system.

[Read the study and failures](research/results/diagnosis-study.md) · [Architecture](research/architecture.md) · [Demo walkthrough](research/demo-guide.md)

## Try it without a model

Python 3.12+; run from the repository root. No third-party dependencies are needed for tests or fixture mode.

```sh
python3 -m unittest discover -s tests -v
python3 -m writing_ftm.demo
```

Open http://127.0.0.1:8765. Click **Review evidence**, change framing/order, inspect citations, and save feedback. This mode is explicitly labeled **fixture replay**. It refuses edited inputs rather than pretending to run a model. Stop with Ctrl-C.

## Run locally on Apple Silicon

The measured environment is an M3 Pro with 18 GB unified memory. Base inference reached 54–55 tokens/s; ten QLoRA updates at 1,024 tokens took 49 seconds with 4.02 GB peak MLX allocation. Those are synthetic capacity measurements, not essay-model training results. [Measurements and limitations](research/results/mac-capacity.md).

```sh
uv venv --python 3.12 --python-preference only-managed .venv
uv pip sync --python .venv/bin/python requirements.lock
.venv/bin/python scripts/download_model.py
.venv/bin/python -m writing_ftm.demo --live
```

The downloader pins `mlx-community/Qwen3-4B-Instruct-2507-4bit` to revision `50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b`. Live mode supports edited passages and evidence disputes. It is a single-user loopback server; keep it local. No paid API is used.

CLI alternative, with optional lexical evidence retrieval:

```sh
.venv/bin/python -m writing_ftm --input examples/critique-request.json --retrieve-k 1 --output runs/my-critique.json
```

Choose a new output path for each run. Event records include source spans, model/prompt provenance, and a human-review-required flag.

## Reproduce the evaluation

```sh
.venv/bin/python -m scripts.benchmark_critique --output runs/my-development
.venv/bin/python -m scripts.benchmark_critique --dataset examples/diagnosis-heldout.json --arms evidence_standard --split heldout --output runs/my-heldout
python3 -m scripts.benchmark_retrieval
```

The runner refuses an existing directory. Model outputs, manifests, summaries, input datasets, and source snapshots for the reported runs are committed under `research/results/`. Development uses ten passages from five source groups; reserved evaluation uses eight passages from four groups. Labels never enter model prompts. Reserved sources are now consumed, so future experiments need new holdouts.

## What is implemented

- A reusable Python critique engine, local MLX provider, CLI, and browser demo.
- Strict records with issue, evidence, severity, uncertainty, and recommended correction; malformed or ungrounded quotes fail validation.
- A lexical evidence-retrieval baseline with document-level measurements.
- Fixed framing and ordering controls that preserve substantive fields; local feedback and dispute logs.
- Annotation-preserving evaluation reruns, regression tests, and dependency-free CI checks.

Exact quotes do not prove entailment. Correct verdicts do not prove factual explanations. Warmth has not been independently validated. The demo's controls are constrained presentation, not generative style transfer. Style-example retrieval, free-form rewrite verification, and writing-v1 fine-tuning remain future work.

All benchmark passages are fictional and AI-authored. Private writing samples, ratings, models, and runtime logs are excluded from Git. This is a solo, AI-assisted project; it does not establish team experience or independent replication. See the [dataset card](data/writing-v1/DATASET_CARD.md), [retrospective](research/retrospective.md), and [remaining research roadmap](research/HANDOFF.md).
