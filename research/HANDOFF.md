# Resume writing-FTM

Saved November 8, 2026 (America/Vancouver).

## Current state

Local Qwen3-4B MLX inference and ten-step QLoRA capacity tests passed. Writing-v1 contains 36 authored paragraph drafts across 18 fictional evidence dossiers, with matched neutral/warm feedback. Training has 20 independent passages expanded to 120 context variants per tone. Twelve automated tests and the latest CI run passed. The v1 validation smoke produced 12 correct final verdicts; this does not establish feedback quality. No v1 training has run.

User calibration is saved locally under `private/writing-v1-review/calibration-round-*.json`, with ratings in the review CSV where applicable. Private writing samples and calibration records remain excluded from Git. Warmth and user preference must stay separate: calibration showed they can diverge. Additional candidates are not yet integrated into dataset targets.

## Agreed product direction

An academic-writing feedback interface with separate warmth and directness controls, plus feedback actions such as too robotic, too indirect, doesn't make sense, and this works. Wording complaints should revise delivery while preserving valid criticism. A substantive complaint must trigger evidence rechecking and permit correction of a mistaken critique. Store local original/revised response pairs and user preferences for later reviewed training data. No interface has been implemented yet.

## Prior-art boundary

Tone controls already exist in writing products. A two-stage generate-then-personalize architecture and preserving substantive feedback while changing presentation also have close precedents. Do not claim these as novel.

- PERG / Pref-Aligner: https://aclanthology.org/2025.findings-emnlp.870/ — factual robustness under personalization; two-stage rewrite baseline.
- Feedback as an Interface: https://aclanthology.org/2026.findings-aacl.61/ — feedback presentation changes while aiming to preserve critique content, in translation refinement.
- Orthogonal and Parametrized Multi-Attribute Steering: https://arxiv.org/html/2610.37517 — preprint studying multi-trait steering, including warmth and sycophancy; residual interference remains.
- DeepL Write: https://support.deepl.com/hc/en-us/articles/9710730337820-Customize-your-text-with-DeepL-Write — established style/tone controls.
- How LLMs Distort Our Written Language: https://arxiv.org/abs/2603.18161 — meaning changes under writing assistance.

## Candidate research question

During repeated requests to make academic feedback warmer, more natural or more direct, does a model weaken valid criticism? Can verification against a structured critique reduce that drift while improving user experience?

This is a candidate incremental contribution, not verified novelty. Compare direct conversational rewriting, a Pref-Aligner-style two-stage baseline, and a rewrite checked against the source-supported critique. Measure omission of valid issues, severity/uncertainty changes, unsupported reassurance, revision-advice preservation, readability, user preference and warmth separately. Include initially incorrect critiques to detect stubborn preservation of mistakes. Evaluate source-group splits, not individual prompt rows as independent samples.

## Next session

1. Review the closest papers and fix a narrow experiment protocol before adding more training examples.
2. Specify the critique record: issue, evidence, severity, uncertainty and recommended correction.
3. Build the smallest local interface and log tone edits separately from substantive corrections.
4. Run a small repeated-rewrite pilot on development passages before training. Keep the held-out test sources untouched.

Project: `/Users/yash/Desktop/writing-FTM`. GitHub: https://github.com/YashVG/writing-FTM (private).
