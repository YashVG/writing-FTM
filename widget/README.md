# Writing FTM companion (Rust / macOS)

A small floating companion opens a local feedback overlay. The app stays running until you quit it; it does not continuously record the screen or launch at login.

## Build and open

Requires Rust/Cargo, Xcode command-line tools, and the project's Python/MLX environment on Apple Silicon. From the repository root:

```sh
./scripts/setup_local.sh
./scripts/build_widget.sh
open "runs/widget/Writing FTM.app"
```

The build script uses an available Apple Development or Developer ID Application certificate and verifies the resulting signature. Set `WRITING_FTM_SIGNING_IDENTITY` to choose a specific identity. It fails with setup guidance if none is available; `WRITING_FTM_SIGNING_IDENTITY=-` explicitly opts into temporary ad-hoc signing, whose capture permissions may break after rebuilding.

A stable certificate keeps macOS's permission identity consistent across builds. The bundle records the project path so it can locate `.venv` and the pinned model when launched from Finder. Rebuild if you move the repository. This is a local development bundle, not a notarized distribution build.

## Use

- Click the companion to open the overlay; drag it to move it. Drag the overlay title to move the expanded window.
- **Choose an area** opens macOS's region selector. Drag around your work; Escape cancels. The overlay hides during selection and returns before OCR starts, with a reading-text status. An unattended selector times out after 90 seconds.
- **Capture screen** takes a snapshot of the main display. The overlay hides before capture so it does not read itself.
- Open **Captured screen** to inspect the preview and review the editable OCR text in **Your draft**. Fix OCR mistakes or paste text directly. Paste the reference excerpt into **Source evidence**, then click **Give feedback**. Both fields are required. Completed critiques open in the **Feedback** tab; switch back to **Your draft** to revise your input.
- **Warmth → Neutral / Warm** changes the introduction. **Directness → Explain first / Action first** changes the order of diagnosis and correction; Action first also moves the overall explanation below the issues. These controls use cached views, so changes are instant and do not rerun the model. Verdicts, criticism, and evidence remain unchanged.
- Feedback shows the affected passage, severity, uncertainty, and expandable source quotes. Editing either input clears the previous critique.
- **Cancel** stops local generation. **More → Clear context and feedback** clears the session. **Hide** returns to the floating companion. Right-click the companion or use **More → Quit Writing FTM** to exit.
- **More → Try an example** inserts a synthetic passage and source; it does not capture your screen.

For capture, enable **Writing FTM** under System Settings → Privacy & Security → Screen Recording (called Screen & System Audio Recording on some macOS versions), then quit and reopen if prompted. When migrating from an old ad-hoc build, remove only the old Writing FTM entry and add the newly signed bundle once; an enabled stale entry can still be denied. Pasted-text feedback works without this permission.

## Architecture

```text
Rust / egui widget and overlay
  → macOS screencapture (explicit click; screen or selected region)
  → Apple Vision OCR through Rust objc2 bindings
  → editable passage + separate source evidence
  → one-shot Python/MLX subprocess → CritiqueEngine.assess
  → strict schema + exact source/passage quote validation
  → four deterministic presentation views
  → Rust overlay selects a view without another model call
```

The interface, capture orchestration, OCR bridge, cancellation, and process lifecycle are Rust. Python remains the existing local model runtime. There is no web server, Swift code, cloud inference, or always-on capture loop. The base model is used; experimental fine-tuned adapters are not loaded.

The shared default is `runs/runtime/model.json`, prepared by setup with pinned weights and a checksum-verified Instruct template. No ignored fine-tuning run is selected automatically. `.venv/bin/python -m scripts.check_setup` checks this configuration without loading the model.

The worker is started only for a feedback request and exits afterward, releasing model memory. Each input is limited to 8,000 characters, with a 120-second worker timeout and a 1,536-token output cap. The widget accepts one source excerpt (`source-1`). Capture and inference run off the UI thread. The model receives extracted text only, not the screenshot or other files.

## Data and limitations

Screenshots use a private temporary directory and are deleted after OCR/image loading, including ordinary cancellation/error paths. The preview, OCR text, and response remain in application memory until cleared or quit. A forced process crash could leave a temporary image for the OS to clean up. Screen context is passed through stdin; it is not placed in command-line arguments or application logs. Copying feedback writes it to your clipboard only when you click Copy.

A capture is a snapshot, not ongoing awareness. Main-display capture may include unrelated visible content; use a selected region or edit the extracted text before asking for feedback. OCR may lose layout, equations, and reading order. The model does not understand the image itself or verify facts against external sources. Its critiques can be incorrect. The UI does not type into or modify other applications.

## Verification

```sh
~/.cargo/bin/cargo test --manifest-path widget/Cargo.toml --locked
.venv/bin/python -m unittest discover -s tests
```

Rust tests cover missing-runtime errors, cancellation/reaping, and draining structured responses larger than the pipe buffer. Python tests cover input limits, instruction/data separation, rejection of fabricated quotes, retain/revise presentations, and preservation across all four tone settings with one model call. Live OCR and UI behavior require a macOS session and user-granted Screen Recording access.

### Release verification

See the [v0.1.0 acceptance record](../docs/release-v0.1.0.md) for exact automated, live, and unverified checks. The [visual walkthrough](../docs/demo.md) uses synthetic inputs and actual app captures. The release is a locally built development bundle; cross-machine installation and notarized distribution are not verified.

The controls currently change framing and ordering, not the model's wording. Perceived warmth is not calibrated or evaluated here. Schema and literal-quote validation cannot establish that the reasoning is correct. Invalid or token-capped model outputs are rejected without a free-form fallback. The widget reviews evidence claims; it does not yet expose the engine's dispute/reassessment flow or offer general grammar/style editing.

## Visual design

The companion uses an original imagegen-created charcoal bot with a transparent background, embedded in the executable. The overlay pairs warm neutral surfaces with larger text, separate draft/feedback views, and a persistent action button. Clicking the bot opens the panel with a 320 ms eased expansion from its position; Clicking the bot in the panel header (or Hide) reverses the transition. Text fades in behind the expanding boundary without reflowing, and controls are disabled during the transition. It has no idle animation. The source asset and exact generation prompt are in [assets/GENERATION.md](assets/GENERATION.md).
