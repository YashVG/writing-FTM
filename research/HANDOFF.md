# Resume writing-FTM

Updated November 10, 2026 (America/Vancouver).

## Current state

Local Qwen3-4B MLX inference and ten-step QLoRA capacity tests passed. Writing-v1 contains 36 authored paragraph drafts across 18 fictional evidence dossiers, with matched neutral/warm feedback. Training has 20 independent passages expanded to 120 context variants per tone. The latest local suite has 24 passing tests; CI configuration covers tests and syntax. The v1 validation smoke produced 12 correct final verdicts; this does not establish feedback quality. No v1 training has run.

User calibration is saved locally under `private/writing-v1-review/calibration-round-*.json`, with ratings in the review CSV where applicable. Private writing samples and calibration records remain excluded from Git. Warmth and user preference must stay separate: calibration showed they can diverge. Additional candidates are not yet integrated into dataset targets.

## Agreed product direction

An academic-writing feedback interface with separate warmth and directness controls, plus feedback actions such as too robotic, too indirect, doesn't make sense, and this works. Wording complaints should revise delivery while preserving valid criticism. A substantive complaint must trigger evidence rechecking and permit correction of a mistaken critique. Store local original/revised response pairs and user preferences for later reviewed training data. A local fixture/live demo now implements constrained framing/order controls and feedback/dispute logging; generative rewriting remains planned.

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

## Remaining work: portfolio target

Build a reusable, local feedback engine with evidence retrieval, adjustable delivery, and measured criticism preservation. Keep the academic-writing task and safety question as the primary study. The roadmap below distinguishes remaining work from the implementation update.

The target role is [Addepar AI Engineering Intern, Summer 2027](https://job-boards.greenhouse.io/addepar1/jobs/8927543002), read November 10 through its official Greenhouse API. It emphasizes Python/ML, LLM applications and RAG, reusable platform components, measurable experiments, software engineering, and technical communication. The choices below are our project design, not additional employer requirements.

| Skill to demonstrate | Planned evidence |
|---|---|
| Reusable AI tooling | A Python package with separate retrieval, critique, rewriting, verification, and model-provider interfaces; shared by a CLI and local UI |
| LLMs, prompting, RAG | Source-backed critiques and separate retrieval of reviewed style examples; documented retrieval failures and ablations |
| ML foundations and frameworks | Existing MLX/QLoRA capacity evidence; a controlled adapter experiment only after labels and baselines are validated |
| Evaluation and measurable impact | Criticism retention, correction of mistaken critiques, user preference, retrieval quality, latency, and memory measurements |
| Software engineering | Typed records, annotation-safe reruns, deterministic fixtures, CI, versioned run manifests, and meaningful failure-path tests |
| Communication | Architecture and decision notes, reproducible results, failure analysis, a short demo, and a retrospective |

### 1. Make evaluation trustworthy

Fix annotation overwrite on evaluation reruns. Validate writing verdicts against the allowed labels; unknown answers must not count as valid paired comparisons. Add regression tests for both failures. Preserve existing ratings and held-out sources. Publish sanitized pilot evidence under a tracked results directory and repair the README link.

Done when repeated evaluation preserves annotations, invalid verdicts have explicit coverage accounting, and a repository reader can inspect the capacity evidence.

### 2. Define the reusable engine

Specify a versioned critique record containing issue ID, passage span, source ID and evidence span, severity, uncertainty, and recommended correction. Support passages with no evidence error. Separate style requests from substantive disputes; disputes can revise the critique after checking evidence. Record every revision and its reason locally.

Expose model loading/generation through a small provider interface backed by existing MLX. Keep inference serial on the 18 GB Mac. Record model revision, prompts, dataset/index hashes, generation settings, and component timings. Do not migrate frameworks solely for a resume keyword: the posting accepts comparable ML frameworks.

Done when the same engine runs through a CLI and fixture tests, with explicit handling of missing evidence, malformed model output, and mistaken initial critiques.

### 3. Add retrieval with a measurable purpose

Retrieve evidence from the supplied source collection and style examples from a separate, reviewed training-only collection. Style examples must never supply factual authority. Preserve source IDs and spans in outputs. Do not index held-out feedback targets or private samples by default. Test sources may supply evidence only, with their reference critiques excluded.

Start with a lexical retrieval baseline; evaluate a small local embedding retriever only if it addresses observed failures. Measure recall at k against annotated evidence spans and report unsupported citations. Compare retrieved evidence with the existing full-dossier input to isolate retrieval errors. Include irrelevant passages and instructions embedded in retrieved text as failure cases.

Done when retrieval has its own scored fixtures and a documented comparison, rather than merely appearing in the architecture.

### 4. Complete the safety experiment and local demo

Freeze a development protocol before opening the reserved test set. Compare direct rewriting, two-stage personalization, and rewriting checked against the structured critique, using the same model and evidence. Exercise repeated warmth/directness requests and initially incorrect critiques. Keep retrieval settings fixed for this comparison; test retrieval separately.

Score issue omissions, severity/uncertainty drift, unsupported reassurance, advice retention, and correction of mistaken critiques. Collect blinded human ratings of warmth, directness, readability, and preference separately. Report source-group sample counts and uncertainty; expand beyond four held-out groups before making general claims. A model verifier's agreement is not independent ground truth.

Build a small local UI with warmth/directness controls and the agreed feedback buttons. Show evidence and revision history. Report measured latency, memory, and verification failures alongside quality. If verification fails, retain the previous response or explicitly report failure; do not silently claim a safe rewrite.

Done when a reviewer can reproduce the comparison and watch a successful edit, a rejected rewrite, and a corrected mistaken critique. A null result is acceptable if the analysis explains it.

### 5. Package the result, then consider extensions

Publish selected nonprivate outputs, architecture/design decisions, failure cases, setup instructions, and a short retrospective. Seek a real peer review and record resulting changes; a solo project does not establish team experience.

After the academic study, optionally demonstrate reuse on a separate set of fictional financial-report passages, such as percentage-point errors or unsupported performance claims. Label this as a transfer demonstration, not investment advice or validated financial expertise. Keep it out of the primary study's scores.

Fine-tuning remains conditional on reliable tone labels and a baseline failure it could address. Compare any adapter against prompting under matched evaluation settings and report tradeoffs. RAG and tone controls are established techniques; novelty remains unverified.

## Implementation update — November 10

Evaluation reruns preserve annotations and reject changed review inputs. Unknown writing verdicts are excluded from valid comparisons; cached responses are rescored before summaries. Selected capacity evidence is now tracked and linked from the README.

The typed critique engine, strict quote validation, provider interface, local MLX provider, and CLI are implemented. See [contracts, limitations, and demo](critique-engine.md). A live development run exposed passage/source confusion despite valid citations; its failure is preserved. Structural validation does not establish evidence entailment. Lexical evidence retrieval, constrained tone presentation, a local demo, and the diagnosis ablation/reserved evaluation are implemented. See [results](results/diagnosis-study.md). Semantic verification and the broader generative-rewrite experiment remain open.

## Next action

Obtain independent human review of diagnoses and benchmark task definitions. The reserved test was consumed: 4/8 verdict matches after 10/10 development matches. Create new held-out source groups before further tuning. Do not present this release as a reliable autonomous critic.

Project: `/Users/yash/Desktop/writing-FTM`. GitHub: https://github.com/YashVG/writing-FTM (private).
