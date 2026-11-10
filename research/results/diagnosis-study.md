# Diagnosis study: a local fix that did not generalize reliably

The explicit evidence-support rule corrected the original causal-claim failure and improved authored development verdict accuracy from 8/10 to 10/10. The frozen prompt then scored 4/8 on reserved passages. This is a useful failure analysis, not evidence of a reliable general critic.

| Evaluation | Prompt | Verdict matches | Invalid outputs | False reassurance | Unnecessary revision | Median seconds |
|---|---|---:|---:|---:|---:|---:|
| Development: 10 passages / 5 source groups | Previous | 8/10 | 0 | 2 | 0 | 4.82 |
| Same development inputs | Explicit evidence support | 10/10 | 0 | 0 | 0 | 5.19 |
| Reserved: 8 passages / 4 source groups | Frozen evidence support | 4/8 | 1 | 2 | 1 | 5.58 |

Invalid outputs count as failures. The reserved run contains four flawed and four supported passages: 2/4 correct in each group, including one invalid supported-passage response. No baseline was run on reserved inputs, so this does not estimate a held-out improvement over the previous prompt. Timings include generation/validation and first-load overhead; they are not controlled throughput benchmarks.

## Why the causal claim was approved

The first saved output substituted association wording for the causal passage. The second acknowledged that “caused” was stronger than the evidence but rationalized retaining it as a reasonable inference. These are observed response behaviors, not a claim about internal model mechanisms. Adding an explicit rule that unsupported plausibility is insufficient corrected this example and the confidence-versus-skill development case.

## Failure analysis

- **Archive, flawed:** the model treated the source's current assumption of independence as justification for that assumption. Source fidelity and methodological validity are distinct; this case also exposes ambiguity in the benchmark's evidence-review framing.
- **Archive, supported:** the explanation contradicted itself, recognizing dependence while marking the correct warning for revision.
- **Translation, flawed:** the model silently narrowed a universal novelty claim to the searched journals, repeating the charitable reinterpretation failure.
- **Translation, supported:** a quote failed exact matching. The validator rejected the response instead of presenting it as validated. This run saved the error but not the invalid raw output, limiting diagnosis of that failure.
- **Development prose:** despite correct verdicts, the comparison responses invented a 95% confidence level absent from the source. Several issue diagnoses were merely “evidence error.” Verdict accuracy therefore overstates usable feedback quality.

## Other checks

The lexical retrieval baseline found the gold document first for all 10 development queries in a six-document collection. This is an easy document-level development check, not a large-corpus RAG benchmark. See [retrieval results](retrieval-development.json).

Presentation tests exercise repeated switches across both framing and ordering settings. Substantive strings, severity, uncertainty, and verdict remain unchanged by construction. No human warmth or preference improvement is claimed. This does not replace the planned comparison against generative rewriting.

## Reproduction and limitations

See the [frozen protocol](../diagnosis-protocol.md), [development manifest](diagnosis-development/manifest.json), [development outputs](diagnosis-development/responses.jsonl), [reserved manifest](diagnosis-heldout/manifest.json), and [reserved outputs](diagnosis-heldout/responses.jsonl). Each run includes its engine-source snapshot. Inputs are under `examples/diagnosis-*.json`; targets are scored outside generation. Run commands are in the README.

All sources are fictional and labels are AI-authored. One quantized model, greedy decoding, and four reserved source groups do not support general safety claims or precise confidence intervals. Explanations received assistant inspection, not independent human adjudication. Test sources are now consumed; further tuning requires a new held-out set. No writing-model fine-tuning has run.
