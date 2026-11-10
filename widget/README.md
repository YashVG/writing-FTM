# Writing FTM companion (Rust / macOS)

A small floating companion opens a local feedback overlay. The app stays running until you quit it; it does not continuously record the screen or launch at login.

## Build and open

Requires Rust/Cargo, Xcode command-line tools, and the project's Python/MLX environment on Apple Silicon. From the repository root:

```sh
./scripts/build_widget.sh
open "runs/widget/Writing FTM.app"
```

The build script uses an available Apple Development or Developer ID Application certificate and verifies the resulting signature. Set `WRITING_FTM_SIGNING_IDENTITY` to choose a specific identity. It fails with setup guidance if none is available; `WRITING_FTM_SIGNING_IDENTITY=-` explicitly opts into temporary ad-hoc signing, whose capture permissions may break after rebuilding.

A stable certificate keeps macOS's permission identity consistent across builds. The bundle records the project path so it can locate `.venv` and the pinned model when launched from Finder. Rebuild if you move the repository. This is a local development bundle, not a notarized distribution build.

## Use

- Click the companion to open the overlay; drag it to move it. Drag the overlay title to move the expanded window.
- **Capture work area** opens macOS's region selector. Drag around your work; Escape cancels. The overlay hides during selection and returns before OCR starts, with a reading-text status. An unattended selector times out after 90 seconds.
- **Capture display** takes a snapshot of the main display. The overlay hides before capture so it does not read itself.
- Review the preview and editable OCR text. Fix OCR mistakes or paste text directly. Enter a request and click **Give feedback**.
- **Cancel** stops local generation. **More → Clear context and feedback** clears the session. **Collapse** returns to the floating companion. Right-click the companion or use **More → Quit** to exit.
- **Load example** inserts a clearly labeled synthetic passage; it does not capture your screen.

For capture, enable **Writing FTM** under System Settings → Privacy & Security → Screen Recording (called Screen & System Audio Recording on some macOS versions), then quit and reopen if prompted. When migrating from an old ad-hoc build, remove only the old Writing FTM entry and add the newly signed bundle once; an enabled stale entry can still be denied. Pasted-text feedback works without this permission.

## Architecture

```text
Rust / egui widget and overlay
  → macOS screencapture (explicit click; screen or selected region)
  → Apple Vision OCR through Rust objc2 bindings
  → editable context + user request
  → one-shot local Python/MLX subprocess
  → feedback shown in the Rust overlay
```

The interface, capture orchestration, OCR bridge, cancellation, and process lifecycle are Rust. Python remains the existing local model runtime. There is no web server, Swift code, cloud inference, or always-on capture loop. The base model is used; experimental fine-tuned adapters are not loaded.

The worker is started only for a feedback request and exits afterward, releasing model memory. Requests are limited to 8,000 context characters and 1,000 instruction characters, with a 120-second worker timeout. Capture and inference run off the UI thread. The model receives extracted text only, not the screenshot or other files.

## Data and limitations

Screenshots use a private temporary directory and are deleted after OCR/image loading, including ordinary cancellation/error paths. The preview, OCR text, and response remain in application memory until cleared or quit. A forced process crash could leave a temporary image for the OS to clean up. Screen context is passed through stdin; it is not placed in command-line arguments or application logs. Copying feedback writes it to your clipboard only when you click Copy.

A capture is a snapshot, not ongoing awareness. Main-display capture may include unrelated visible content; use a selected region or edit the extracted text before asking for feedback. OCR may lose layout, equations, and reading order. The model does not understand the image itself or verify facts against external sources. Its critiques can be incorrect. The UI does not type into or modify other applications.

## Verification

```sh
~/.cargo/bin/cargo test --manifest-path widget/Cargo.toml --locked
.venv/bin/python -m unittest discover -s tests
```

Rust tests cover missing-runtime errors and cancellation/reaping of the local worker. Python tests cover input limits and separating captured text from system instructions. Live OCR and UI behavior require a macOS session and user-granted Screen Recording access.

### Local smoke test (2026-11-10)

On the development Mac, the bundle launched, the companion opened and collapsed the overlay, the synthetic example produced local feedback, and Cancel returned the UI to its idle state. The response flagged the example's unsupported causal claim; this is a smoke test, not a quality evaluation. All 33 Python tests and 2 Rust tests passed locally.

The initial ad-hoc build had a stale Screen Recording grant despite an enabled switch. The bundle's designated requirement was tied to its executable hash. Switching to the existing Apple Development certificate and refreshing only Writing FTM's permission entry resolved it. The actual display-capture → screenshot preview → Apple Vision OCR path succeeded, including after another source rebuild and relaunch without regranting permission. The app now restores the overlay before OCR, since Vision's first-run model preparation caused a long hidden-window delay. The permission request's success result is also respected instead of always reporting denial after a request.

This verifies display capture and OCR on the development Mac, not OCR accuracy across applications. Successful manual region selection remains unverified. Captured test context was cleared; no screenshots or OCR contents were added to the repository. See [Apple's explanation of ad-hoc signing and capture permission](https://developer.apple.com/forums/thread/819406) and [code-signing requirements](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements).

The overlay currently uses a separate free-form feedback prompt through the existing MLX provider. It does not yet invoke the project's structured critique engine, preservation checks, or warmth/directness controls. Those integrations and their evaluations remain follow-up work.
