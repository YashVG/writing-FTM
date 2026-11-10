# Diagnosis development protocol

Fixed before the paired run on November 10, 2026. This is a development ablation, not an independent held-out claim.

Compare the previous engine prompt against the same prompt plus an explicit evidence-support decision rule. Use the same pinned quantized Qwen3-4B, greedy decoding, 1,024 output-token cap, and structural validator. No retries. Run sequentially using one loaded model. Cases are eight existing validation passages across four dossiers, plus the original workshop failure and a qualified counterpart. No private samples or test sources are used.

Primary outcome: exact verdict matches the authored label. Malformed, truncated, and quote-invalid responses count as failures. Report coverage, false reassurance, unnecessary revisions, and median end-to-end time separately. Each source has two dependent passages; ten passages are five source groups, not ten independent experiments. Inspect diagnoses and recommendations separately; verdict accuracy cannot establish critique completeness. Labels are AI-authored, not independently human-validated.

The intervention tests whether an explicit support standard improves behavior. It cannot identify neural mechanisms or isolate every sentence of the added prompt. A single greedy run on one small model cannot establish generality. Do not tune on reserved test results.

## Reserved evaluation gate

After the 10-passage development comparison completed, freeze the evidence-standard prompt and run it once on the eight existing test passages (four source groups), neutral context and no stated user belief. Use the same decoding, cap, validator, and scoring. Do not modify the prompt in response to test failures. This tests source generalization within the existing authored benchmark, not an independent human benchmark. These test sources are considered consumed after this release; future tuning requires new held-out sources. No test feedback targets enter generation or retrieval.
