# Three-minute demonstration

From the repository root, run `python3 -m writing_ftm.demo` with Python 3.12 or newer. Open http://127.0.0.1:8765. This default fixture mode requires no model or third-party package. Stop with Ctrl-C.

1. Show the causal workshop claim and observational evidence. Click **Review evidence**. The fixture returns a correction with exact source quotes; explicitly call this a replay.
2. Select **Warm** framing and **Action first**. Show that the recommendation moves first while diagnosis, severity, uncertainty, and verdict remain unchanged.
3. Expand the evidence record. Click **This works**; the local acknowledgement confirms logging. Explain why preference is separate from warmth and correctness.
4. Show the diagnosis case study: the prior prompt's false reassurance, the controlled comparison, and the reserved-test failures. Explain that quote validation cannot establish entailment.

For live generation, install the pinned environment, run `scripts/download_model.py`, and use `.venv/bin/python -m writing_ftm.demo --live`. The model uses your Mac, not a paid API. In live mode, edit the passage/source and use the dispute field to recheck a mistaken critique. One shared session is supported; do not expose this server publicly. A dispute requests reconsideration, not automatic acceptance of the user's opinion.

Logs are written to a new ignored `runs/demo/<session>/events.jsonl`. They contain passage/source text and feedback; do not publish private logs. There is no generative tone rewriting, online learning, or automatic training from clicks in this release.
