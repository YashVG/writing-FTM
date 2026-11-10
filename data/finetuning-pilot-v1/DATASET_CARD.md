# Neutral writing-feedback SFT pilot

This pilot selects one neutral/no-stated-belief context per passage from writing-v1. It contains 20 training passages from ten source groups and eight validation passages from four disjoint groups. Training payloads contain only chat messages; IDs and source groups are recorded separately in `provenance.json`.

Targets are short prose critiques ending with a revise/retain tag. They are not structured JSON critique records. No private writing or calibration ratings are included. Warmth candidates remain unvalidated and are not used as preference labels. The fictional sources and feedback are AI-authored; this is a pipeline pilot, not independently reviewed supervision.

The largest full chat sequence is 256 tokens in training and 212 in validation, below the 512-token cap. Training masks the user prompt. Selection is deterministic, preserving exact targets from the original neutral dataset. `manifest.json` records input/output hashes, source groups, and model revision.

Use `scripts/prepare_finetuning.py` with new `--destination` and `--run` directories to rebuild. It refuses existing destinations. The generated run configuration pins the local snapshot and uses rank 8, eight trained layers, batch 1, 20 updates, learning rate 1e-5, gradient checkpointing, and seed 42. Validation loss uses all eight validation examples. Generation compares the base model and saved adapter on the same eight validation prompts with greedy decoding and a 256-token output cap.

No reserved test sources are used. These validation sources have already been inspected in earlier development and cannot establish unbiased generalization. Before larger training, obtain independent target review and new evaluation sources. Loss changes and verdict scores do not establish warmth, complete feedback quality, or JSON-engine compatibility.

## Template/update audit

The lengths and learning rate above describe the original pilot. The preparation script now uses the official Instruct template (maximum 252/208 train/validation tokens) and learning rate 2e-6. Training messages are unchanged. See the [repetition repair](../../research/results/repetition-repair/REPORT.md) for the controlled comparison and provenance.
