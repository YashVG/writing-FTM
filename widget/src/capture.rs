use eframe::egui;
use objc2::AllocAnyThread;
use objc2_foundation::{NSArray, NSDictionary, NSString, NSURL};
use objc2_vision::{
    VNImageRequestHandler, VNRecognizeTextRequest, VNRequest, VNRequestTextRecognitionLevel,
};
use std::path::Path;
use std::process::Command;
use std::time::{Duration, Instant};

#[link(name = "CoreGraphics", kind = "framework")]
unsafe extern "C" {
    fn CGPreflightScreenCaptureAccess() -> bool;
    fn CGRequestScreenCaptureAccess() -> bool;
}

pub struct Snapshot {
    pub image: egui::ColorImage,
    pub text: String,
}

pub fn recognize(path: &Path) -> Result<String, String> {
    objc2::rc::autoreleasepool(|_| {
        let url = NSURL::fileURLWithPath(&NSString::from_str(&path.to_string_lossy()));
        let request = VNRecognizeTextRequest::new();
        request.setRecognitionLevel(VNRequestTextRecognitionLevel::Accurate);
        request.setUsesLanguageCorrection(true);
        // Empty options dictionary has no mismatched generic values.
        let handler = unsafe {
            VNImageRequestHandler::initWithURL_options(
                VNImageRequestHandler::alloc(),
                &url,
                &NSDictionary::new(),
            )
        };
        let requests: objc2::rc::Retained<NSArray<VNRequest>> = NSArray::from_slice(&[&request]);
        handler
            .performRequests_error(&requests)
            .map_err(|e| format!("Text recognition failed: {e}"))?;
        let mut lines = Vec::new();
        if let Some(observations) = request.results() {
            for observation in observations.iter() {
                if let Some(candidate) = observation.topCandidates(1).firstObject() {
                    lines.push(candidate.string().to_string());
                }
            }
        }
        Ok(lines.join("\n"))
    })
}

pub fn capture_screen(interactive: bool, captured: impl FnOnce()) -> Result<Snapshot, String> {
    // Request can succeed immediately; don't discard its result and report a
    // false denial. Capture itself still runs under macOS permission enforcement.
    ensure_permission(
        || unsafe { CGPreflightScreenCaptureAccess() },
        || unsafe { CGRequestScreenCaptureAccess() },
    )?;
    let directory = tempfile::tempdir().map_err(|e| e.to_string())?;
    let path = directory.path().join("capture.png");
    let mut command = Command::new("/usr/sbin/screencapture");
    command.args(["-x", "-t", "png"]);
    if interactive {
        command.arg("-i");
    } else {
        command.args(["-D", "1"]);
    }
    let mut child = command.arg(&path).spawn().map_err(|e| e.to_string())?;
    let start = Instant::now();
    let status = loop {
        if start.elapsed() > Duration::from_secs(90) {
            let _ = child.kill();
            let _ = child.wait();
            return Err("Capture timed out. Click Capture work area to try again.".into());
        }
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) => std::thread::sleep(Duration::from_millis(100)),
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(error.to_string());
            }
        }
    };
    if !status.success() || !path.exists() {
        return Err("Capture cancelled. Nothing was sent to the model.".into());
    }
    // OCR can take longer on its first run while Vision prepares its models.
    // The window only needs to be hidden while taking the screenshot.
    captured();
    let text = recognize(&path)?;
    let image = image::open(&path).map_err(|e| e.to_string())?.into_rgba8();
    let size = [image.width() as usize, image.height() as usize];
    // Temporary screenshot is deleted when the directory is dropped here.
    Ok(Snapshot {
        image: egui::ColorImage::from_rgba_unmultiplied(size, image.as_raw()),
        text,
    })
}

fn ensure_permission(
    preflight: impl FnOnce() -> bool,
    request: impl FnOnce() -> bool,
) -> Result<(), String> {
    if preflight() || request() {
        return Ok(());
    }
    Err("Screen Recording access is needed. Enable Writing FTM in System Settings → Privacy & Security → Screen Recording, then quit and reopen the app. You can paste text without granting access.".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn denied_permission_offers_paste_without_capture() {
        assert!(ensure_permission(|| false, || false)
            .unwrap_err()
            .contains("paste text without granting access"));
    }
    #[test]
    fn newly_granted_permission_is_respected() {
        assert!(ensure_permission(|| false, || true).is_ok());
        assert!(
            ensure_permission(|| true, || panic!("Must not request existing permission")).is_ok()
        );
    }
}
