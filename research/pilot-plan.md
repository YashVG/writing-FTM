# Warmth training: capacity pilot

This pilot measures whether a 4B model can run and train on this Mac. It does not test the research hypothesis.

## Research direction

Compare general and task-focused training data, each with unchanged, uniformly warm, and context-dependent tone. Within a data source, preserve factual content and user prompts. Match token budgets and training settings. Include untouched and prompt-only baselines. Evaluate warmth, factual correctness, false agreement, and unwarranted disagreement separately. Split by underlying question before rewriting examples. Use multiple seeds and blinded human checks before drawing conclusions.

The original warmth study reports reliability losses from persona training. A follow-up finds data-distribution effects and identifies a missing task-focused unchanged-tone control. This is a candidate incremental extension, not an established novelty claim.

- https://www.nature.com/articles/s41586-026-10410-0
- https://aclanthology.org/2026.aacl-long.86.pdf
- https://arxiv.org/abs/2609.39863

## Hardware pilot

- Qwen3-4B-Instruct-2507, community MLX 4-bit conversion; exact snapshot recorded in runs/pilot/model.json.
- MLX QLoRA, last eight transformer blocks, rank 8, MLX scale 16, batch 1, gradient checkpointing, prompt-masked loss.
- Ten updates at each of 512 and 1,024 tokens. Each starts from the same base model.
- Synthetic arithmetic and repeated context exercise sequence memory; 24 training and four validation fixtures per length. These are not representative research data or a benchmark.
- Generate three short responses before training and after reloading the 1,024-token adapter.
- Record MLX allocator peak (decimal GB), process resident memory (GiB), system available memory, swap growth, and wall time. These quantities differ and must not be added together.
- Stop a child run after 20 minutes, five low-memory samples (<1.5 GiB available), or >2 GiB system swap growth. System memory measurements include other applications.

Success: both training jobs finish with finite losses, saved adapters reload, and resource use leaves useful headroom. Failure: record evidence and reduce sequence length or trained layers before proceeding.

No external paid inference, uploads, or private coursework data are used. Model files live in the standard Hugging Face cache. No full-model copies are saved per experiment.
