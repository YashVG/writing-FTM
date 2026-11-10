# Critique engine v1

The local engine converts a passage and supplied source texts into a versioned critique. It supports initial assessment and evidence rechecking after a substantive dispute. Optional CLI lexical retrieval and constrained framing/order controls are implemented; generative rewriting remains planned.

## Run

From the repository root, run without loading a model:

```sh
.venv/bin/python -m writing_ftm --input examples/critique-request.json --fixture-response examples/critique-response.json --output runs/critique-demo/fixture.json
```

Omit `--fixture-response` for local MLX generation using the pinned model described in `runs/pilot/model.json`. Run `scripts/download_model.py` first on a fresh machine. Use a new output filename for each event; the CLI refuses overwrites. Fixture mode validates a supplied response and makes no model-quality claim.

## Contracts and boundaries

`writing_ftm.engine.Provider` separates generation from validation. `MLXProvider` loads lazily, serializes calls within one provider instance, uses greedy decoding, and rejects empty or token-capped generations. Run a single CLI process at a time on the 18 GB Mac. No cloud service is used.

The model returns strict JSON with a verdict, rationale, supporting evidence, and issues. Each issue includes a passage quote, diagnosis, source quotes, severity, uncertainty, and concrete recommendation. Unique literal quotes resolve to zero-based Python Unicode character offsets, with exclusive ends. Ambiguous or missing quotes, unknown sources, inconsistent verdicts, and malformed records fail validation. Supported passages have an empty issue list and still require evidence.

Validation proves structure and quote presence only. It does not prove entailment, completeness, or correctness. Every event explicitly requires human review. Source/passage content is marked as untrusted in the prompt; this is not a demonstrated prompt-injection defense.

`CritiqueEngine.assess(..., previous=critique, dispute=reason)` rechecks evidence and may change the verdict. CLI requests can supply `previous` in the model's wire schema shown in the example response, plus `dispute`. The previous critique and reason are retained in the event. Events also record input/prompt hashes, provider settings, elapsed time, and raw model output. They remain local under ignored `runs/`; hashes do not replace retaining the original request for reproduction.

## Evidence

Tests cover fabricated and ambiguous quotes, unknown sources, malformed records, inconsistent verdicts, missing evidence, offsets, and the ability to replace an earlier critique during reassessment. The latter is a control-flow fixture, not proof that the model correctly resolves disputes.

The first live demo incorrectly returned `retain`: it substituted the source's association wording for the passage's causal wording. See [saved failure](results/critique-initial-failure.json) and the shared [demo request](../examples/critique-request.json). This passed structural validation. The prompt was subsequently clarified to distinguish the passage from its sources. Development examples are not held-out evidence of accuracy.

The clarified prompt also returned an incorrect `retain` verdict on the same development passage. The [follow-up output](results/critique-followup-failure.json) is preserved. Both runs completed, but neither passed the substantive task. Improving diagnosis quality remains the next blocker; these runs do not validate the engine as an autonomous critic.

## Current diagnosis results

An explicit evidence-support decision rule subsequently fixed the workshop case and produced 10/10 development verdict matches, but only 4/8 reserved matches. See the [full case study](results/diagnosis-study.md). Earlier failure artifacts above are retained as historical evidence.
