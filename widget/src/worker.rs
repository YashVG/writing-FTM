use std::io::Write;
use std::path::Path;
use std::process::{Command, Stdio};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::time::{Duration, Instant};

pub fn feedback(
    root: &Path,
    context: &str,
    task: &str,
    cancel: Arc<AtomicBool>,
) -> Result<String, String> {
    let python = root.join(".venv/bin/python");
    if !python.exists() {
        return Err("Local Python environment missing. Run the project setup first.".into());
    }
    let request = serde_json::to_vec(&serde_json::json!({"context":context,"task":task}))
        .map_err(|e| e.to_string())?;
    let mut child = Command::new(python)
        .args(["-m", "writing_ftm.widget_feedback"])
        .current_dir(root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;
    if let Some(mut input) = child.stdin.take() {
        if let Err(error) = input.write_all(&request) {
            let _ = child.kill();
            let _ = child.wait();
            return Err(error.to_string());
        }
    }
    let start = Instant::now();
    loop {
        if cancel.load(Ordering::Relaxed) || start.elapsed() > Duration::from_secs(120) {
            let _ = child.kill();
            let _ = child.wait();
            return Err("Feedback cancelled or timed out. Try a shorter passage.".into());
        }
        match child.try_wait() {
            Ok(Some(_)) => break,
            Ok(None) => std::thread::sleep(Duration::from_millis(100)),
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(error.to_string());
            }
        }
    }
    let output = child.wait_with_output().map_err(|e| e.to_string())?;
    let response: serde_json::Value = serde_json::from_slice(&output.stdout).map_err(|_| {
        "Local worker did not return valid feedback. Check the model installation.".to_string()
    })?;
    if let Some(error) = response.get("error").and_then(|v| v.as_str()) {
        return Err(error.into());
    }
    response
        .get("feedback")
        .and_then(|v| v.as_str())
        .map(String::from)
        .ok_or_else(|| "Feedback was empty.".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn missing_python_returns_useful_error() {
        let result = feedback(
            Path::new("/not-a-writing-ftm-project"),
            "context",
            "review",
            Arc::new(AtomicBool::new(false)),
        );
        assert!(result.unwrap_err().contains("environment missing"));
    }
    #[test]
    fn cancelled_worker_is_reaped() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
        if !root.join(".venv/bin/python").exists() {
            return;
        }
        let start = Instant::now();
        let result = feedback(root, "sample", "review", Arc::new(AtomicBool::new(true)));
        assert!(result.unwrap_err().contains("cancelled"));
        assert!(start.elapsed() < Duration::from_secs(3));
    }
}
