# Writing-feedback dataset v1

This replaces study-v0 as the active research seed. It contains newly authored paragraph drafts and matched feedback, guided by private academic-writing references. It is not a collection of the user's essays. The sources are fictional, explicit evidence summaries; no findings should be cited as real research.

## Contents and splits

| Split | Source groups | Distinct passages | Rows per tone / evaluation rows |
|---|---:|---:|---:|
| Train | 10 | 20 | 120 per tone |
| Validation | 4 | 8 | 48 per tone |
| Held-out test | 4 | 8 | 48 evaluation prompts |

Each source has a flawed paragraph and a supported counterpart. Each passage appears under six conditions: neutral/discouraged wording crossed with no user verdict, a correct user verdict, or an incorrect user verdict. These repeated conditions are NOT independent passages. All variants of a source stay in one split. The 12-prompt smoke subset uses the two sleep paragraphs from validation; the test sources were evaluated once for the November 10 diagnosis release and are now consumed; future tuning needs new held-out sources.

Topics include causal claims, sample coverage, rating-versus-behavior confusion, percentages, equivalence, clustered observations, construct measurement, synthesis, novelty and recommendation scope. Test documents are new but some issue categories recur from training. This is source-level generalization within a narrow academic-feedback domain, not evidence of broad transfer.

## Feedback matching

Each pair contains the exact same diagnosis, explanation and revision advice. Supported passages instead receive the same justification for retaining the claim. The opening sentence differs: neutral feedback situates the claim; warm feedback addresses the writer with passage-specific acknowledgment. There are no generic encouragement suffixes. Intended warmth is an author-assigned manipulation, not a human-validated fact.

Neutral feedback is respectful rather than hostile. Warm feedback does not remove criticism or fabricate confidence in an unsupported claim. Formality, respect, warmth and correctness must be rated separately. All targets preserve the same evidence verdict.

With the pinned Qwen tokenizer, training assistant-content means are 55.75 tokens (neutral) and 56.30 (warm). Within-pair training length ratios range from 0.980 to 1.041. Total answer-token budgets differ by about 1%, not zero. Validation pairs are similarly close. Counts include the requested answer tag but exclude chat-template delimiters. See `token-audit.json` for full sequence counts.

## Provenance and privacy

The authored source is `dossiers.py`; exported JSONL checksums are recorded in `sha256.json`. The assistant created the fictional evidence, paragraphs and feedback. User samples informed task choice and a restrained, evidence-focused register. They have mixed-authorship disclosures and were not treated as unassisted gold labels. No private paragraphs, quotations, filenames or document hashes are included in this public dataset. Private inventory, overlap audit, annotation sheets and their keys are Git-ignored.

A local check found no shared contiguous 12-word sequence between this dataset's passages/feedback and the two inspected writing references. This is a copying check, not proof of anonymity or independence of ideas. Original files remain unchanged.

## Review and limitations

Programmatic checks verify source separation, condition coverage, required-content preservation, answer tags and checksums. They cannot establish that a warm variant feels warmer or that every judgment is appropriate. A 72-response shuffled review sheet is generated locally under `private/writing-v1-review/`; its labels are blank. Keep the separate key away from raters. Human review should check evidence fidelity, warmth, respect, directness, actionability and unwarranted praise. Revise or exclude pairs lacking a reliable warmth difference.

This small seed has only 20 distinct training passages. Do not call 120 context variants 120 independent examples. Expand with independently authored documents and reviewers before making publishable claims. No writing-v1 training has run. Draft configurations are available but should follow review rather than replace it.
