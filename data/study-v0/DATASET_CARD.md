# Study v0: synthetic matched-tone pilot

Status: programmatically validated; human review pending. This is an experiment-development dataset, not a validated benchmark or a replication of the published studies.

## Contents

Each of six cells has 96 training rows and 24 validation rows. Task-focused cells contain arithmetic, source extraction, and a causal-inference question family. Broad cells contain 50% reasoning and 50% short email, summary, rewrite, and heading tasks. “Broad” refers only to this synthetic mixture, not representative human conversation. The six cells do not contain 576 independent underlying questions: tone variants share cases, and mixtures share reasoning cases.

Neutral responses contain the canonical answer. Warm responses add acknowledgment and supportive wording. Adaptive responses add this wording only when the user expresses discouragement. All variants retain the canonical answer verbatim and use identical prompts within each mixture. This isolates a narrow wrapper intervention, not all meanings of warmth. Factual content preservation does not guarantee that the added wording is appropriate; reviewers must check that separately.

Training examples balance reasoning families, emotional context and belief correctness in the task mixture. Evaluation contains 48 independent case IDs, each in six paired conditions: two emotional contexts times three belief conditions. The 24-row smoke subset uses four of these cases. Treat it as development data; exclude these four case IDs from any final held-out analysis after inspecting results.

## Provenance and splits

All text is authored procedurally for this project by `scripts/build_dataset.py`; no coursework, personal messages or external corpus was ingested. Facts refer to fictional records or elementary arithmetic. The generator and canonical answers are the provenance. SHA-256 checksums identify JSONL artifacts.

Case IDs and parameter ranges are disjoint across train, validation and test before tone expansion. Templates are shared: this tests new instances of familiar templates, not out-of-distribution generalization. Arithmetic and source answers are checked independently in tests. The causal family always has “no” as its answer; report it separately to expose this bias. Human reviewers have not independently audited the content.

## Token budgets and limitations

See `token-audit.json` for actual tokenizer counts. Warm answers are longer. Equal row counts or optimizer steps are NOT equal supervised-token budgets. Do not interpret six equal-step runs as isolating warmth independently of length. A later study must include length controls and a token-budget sensitivity analysis, richer independently authored examples, new held-out task families, and multiple seeds. Do not pad with meaningless filler to claim matched semantic exposure.

Use `training-review.csv` for a first content/appropriateness audit. No human ratings have been filled in automatically. Preserve this version; introduce improved data under a new version and record what changed.

`heldout.jsonl` reserves the other 44 cases (264 prompts) and excludes all four smoke case IDs. It has not been run. Use it only after the protocol and checkpoint selection rules are fixed.
