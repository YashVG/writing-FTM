# v0.1.0 release checks

Source-based research prototype, checked on November 10, 2026, on an M3 Pro Mac with 18 GB unified memory. This release includes the Rust companion, Python critique engine, model-free browser demo, and recorded experiments. It is not a notarized application download or a validated writing-assessment product.

## Setup and automated checks

| Check | Result and scope |
|---|---|
| Isolated checkout and environment | Passed. Copied release sources without existing `runs/` or `.venv`, created a fresh Python 3.12 environment, installed all 51 locked packages, and prepared the runtime from the pinned cached snapshot. A first-time internet download was not repeated. |
| Repeatable model setup | Passed. Repeated setup reuses the same audited view, preserves cached model files, and publishes one explicit `runs/runtime/model.json`. |
| Missing model / changed template | Passed regression checks. Missing weights, broken weight symlinks, and changed templates fail before generation. Errors offer setup guidance and do not echo user input. |
| Python suite | 40 tests passed in the isolated environment, including model-template checks. Dependency-free CI can skip the two optional environment-dependent tests. |
| Rust suite | 6 tests passed: permission denial, newly granted permission, missing Python, cancellation, timeout, and responses exceeding pipe capacity. Cancellation/timeout use a controlled subprocess and run without a local model. |
| Malformed critique / fabricated quote | Passed fixture tests. No free-form fallback is accepted. These tests do not validate semantic reasoning. |
| Signed app build | Passed local build and strict signature verification using the existing development identity. No permission reset was required. |

## Live acceptance checks

| Check | Result and scope |
|---|---|
| Fresh-checkout causal claim | `revise`, 10.65 seconds. |
| Fresh-checkout qualified association | `retain`, 6.50 seconds. |
| Tone preservation | All four cached views returned. Framing/order changes preserve the verdict and substantive fields in automated tests and the UI. |
| Input editing / expand-collapse | Passed. Editing clears old feedback; repeated collapse/expand preserves the current result. |
| UI cancellation | Passed. Cancel restored editable inputs and the feedback button. |
| Native region selector timeout | Passed. An unattended selector timed out and restored the overlay with an actionable message. |
| Region selection / Escape | Unverified. The computer-control tool could not interact with the system selector; a manual check is still needed. |
| Permission denied | Tested with injected permission results, not by revoking the user's existing macOS permission. |
| Display capture and OCR | Verified earlier on this Mac after stable signing, including a rebuild. This is not a cross-application OCR accuracy claim. |

[Live smoke measurements and model/template provenance](../research/results/release-v0.1.0/live-smoke.json). The two synthetic examples check the integration; they are not a new benchmark or independent test set. Diagnosis still scored 4/8 on the earlier reserved synthetic evaluation.

## Manual follow-up

Open **Choose an area**, select a small synthetic paragraph, and confirm that the overlay returns with a preview and editable OCR. Repeat with Escape and confirm that no image or critique is accepted. Record the result before claiming region selection is verified. The feature remains experimental in this release; pasted text is the reproducible path.

## Before the next research iteration

Use the app for 10–20 real sessions. Keep a private note of diagnosis correctness, usefulness, preferred presentation, and friction in capture/source entry. Do not commit coursework, screen captures, or session text. Decide the next change from these observations; this release does not automatically learn from use.
