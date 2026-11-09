# Writing-v1 evaluation smoke check

The unchanged pinned Qwen3-4B-Instruct-2507 4-bit model completed 12 prompts using two validation passages from one fictional sleep-survey dossier. These crossed passage correctness, emotional wording and user verdict. No adapter was loaded.

All 12 final verdicts parsed and matched the authored labels: six revise verdicts for flawed passages and six retain verdicts for supported passages. No incorrect-user-verdict flips occurred among the four baseline-correct comparisons. No output reached the 256-token cap. This checks execution and verdict scoring, not human-perceived warmth or comprehensive critique quality. The source-group sample size is one.

The four test source groups remain unrun. Raw responses and human-review sheets are local under `runs/writing-v1/base-smoke/`. Dataset-feedback calibration sheets are local under `private/writing-v1-review/`. No ratings have been invented or filled automatically.

Twelve automated tests pass across v0 and v1. The tokenizer audit keeps every training and validation sequence below 1,024 tokens. Training feedback pairs differ by at most about 4.1% in token length, and aggregate assistant-content token budgets differ by about 1%. Private-reference overlap checks passed without copying user passages to Git. Human calibration and v1 training remain pending.

A spot check of the neutral/no-belief response to the flawed sleep passage found a correct causal diagnosis but no explicit concrete revision step. This is a qualitative observation from one output, not a completed human rating exercise. It illustrates why verdict accuracy must not be reported as overall feedback quality.
