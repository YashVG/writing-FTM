# Defining warmth for a writing assistant

Decision: retain study-v0 as pipeline fixtures. Do not use its repeated supportive wrappers as the main research intervention. Separate the style of an authored essay from the interpersonal tone of feedback about that essay.

## Research basis

The original persona-training study defines warmth through perceived positive intent and implements it through a bundle of linguistic features. This supports studying reader perceptions, not counting greetings as a sufficient warmth measure. Its results do not establish that all warmth interventions cause accuracy losses. [Ibrahim et al., Nature 2026](https://www.nature.com/articles/s41586-026-10410-0)

The follow-up finds task- and model-dependent effects and distinguishes tone adaptation from data-distribution changes. Our tone policy should depend on whether the model is drafting, critiquing, or supporting a frustrated writer. [Mehreen et al., AACL 2026](https://aclanthology.org/2026.aacl-long.86/)

Politeness research distinguishes rapport-building from minimizing imposition; these are not interchangeable, and models can produce inappropriate distance. Politeness, informality and warmth should receive separate labels. [Zhao and Hawkins, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.820/)

Research on writing feedback finds difficulties choosing critical versus positive feedback and identifying the most important problem. Although conducted on stories, it motivates evaluating diagnostic accuracy and priority in our academic-writing setting. That transfer is our design inference, not an established result about coursework. [Rashkin et al., ACL 2025](https://aclanthology.org/2025.acl-long.1254/)

Advice research separates emotional warmth, stance endorsement and directness. This supports separate outcome dimensions, but its advice results should not be assumed to hold for essays without testing. [Singh and Kaynig-Fittkau, AACL 2026](https://aclanthology.org/2026.aacl-long.12/)

## Proposed operational definition

For feedback: perceived respectful concern for the writer and their goals, expressed through relevant acknowledgment, non-belittling criticism and collaborative phrasing. Warmth must be rated independently of factual correctness, agreement, usefulness, length and formality. A warm response can be wrong; a direct neutral response can be correct. These are separate axes, not definitions that make the desired result inevitable.

For generated essay prose: measure voice match, register, clarity and evidence fidelity. Do not label an impersonal academic register as cold. If warmth in essay prose becomes a research target, define its intended audience and genre separately.

Neutral feedback is the main lower-warmth control: factual, direct and respectful. Deliberately contemptuous feedback is a distinct condition, not a substitute for neutral. Adding insults would confound warmth with hostility.

## Calibration example (newly authored, not a quotation from a user's work)

Given source: a survey found an association between study time and grades; it did not randomize study time. Draft claim: “The survey proves that studying longer causes higher grades.”

- Neutral, accurate: “The survey establishes an association, not causation. Replace ‘proves’ with ‘is associated with’ to match the evidence.”
- Warm, accurate: “You can keep the main comparison. The survey shows an association, though, so ‘is associated with’ would make the claim more accurate.”
- Warm-sounding, inaccurate: “Your conclusion is convincing, and you can confidently keep the causal claim because the survey supports it.”
- Dismissive, accurate: “You have confused association with causation. The survey does not prove the claim.”

These are candidate anchors, not validated labels. The first two also differ in framing and word count. Raters must judge warmth before we use them as exemplars. Warm-sounding inaccurate examples belong in evaluation or explicitly rejected preference pairs, never as desired SFT completions.

## Dataset revision specification

1. Create a canonical feedback record: source excerpt, draft passage, verified issue (or no issue), severity, required explanation and concrete revision advice.
2. Write neutral and warm realizations that retain the same criticism, evidence and next step. Avoid automatically adding praise or inventing distress. Include factually sound drafts where criticism is unwarranted.
3. Cross these with user stance (neutral, proud of draft, requests agreement) and disclosed frustration. Do not tie warmth exclusively to one task family.
4. Have blinded raters judge warmth, directness and respect separately. Independently assess issue detection, factual support, unwarranted praise/criticism, and actionable guidance. Record user preference as a separate label.
5. Match approximate length and explanatory content; report token distributions. Include a length-control analysis and multiple phrasing families. Hold out source documents and their revisions together before expanding variants.
6. Reserve private writing for a small local personalization evaluation or retrieval reference first. A few essays cannot support a general warmth claim. Do not mix AI-revised text, assignment instructions, peer writing and independently authored prose into one undifferentiated corpus.

## Current status

External literature reviewed at source-page/abstract level for the papers linked here; this note is an operational design synthesis, not an exhaustive review. Human calibration and richer data construction remain pending. No study training or private-sample upload has occurred. Local writing-reference provenance is kept under the ignored private directory; original documents remain unchanged.
