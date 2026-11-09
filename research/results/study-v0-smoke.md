# Study-v0 base-model smoke check

Qwen3-4B-Instruct-2507 (4-bit MLX), pinned revision `50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b`, completed 24 prompts from four underlying synthetic questions. Greedy decoding, maximum 256 output tokens; no trained adapter or warm system prompt.

- 24/24 responses parsed; 24/24 final answers were correct.
- No output reached the token cap.
- Eight no-belief answers were correct and had a parsed wrong-belief counterpart; zero changed to the user's wrong answer.
- Human warmth and prose-consistency ratings remain blank.

This is an execution check, not evidence of general robustness. The questions are simple and conditions share underlying cases. The four inspected IDs are excluded from `heldout.jsonl` (44 cases / 264 prompts). Raw responses and annotation sheets remain local in `runs/study-v0/base-smoke/`.

Six automated tests pass for canonical arithmetic, tone content preservation, split membership, holdout separation, conservative answer parsing and paired-flip counting. Token lengths were checked with the actual model tokenizer. No study-v0 training has run. Next: human review and richer challenge data before a substantive training comparison.
