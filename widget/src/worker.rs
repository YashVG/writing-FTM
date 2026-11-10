use serde::Deserialize;
use std::collections::BTreeMap;
use std::io::{Read, Write};
use std::path::Path;
use std::process::{Command, Stdio};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc,
};
use std::time::{Duration, Instant};

#[derive(Debug, Deserialize)]
pub struct Feedback {
    pub presentations: BTreeMap<String, Presentation>,
}

#[derive(Debug, Deserialize)]
pub struct Presentation {
    pub intro: String,
    pub verdict: String,
    pub rationale: String,
    pub sections: Vec<Section>,
    pub evidence: Vec<Evidence>,
}

#[derive(Debug, Deserialize)]
pub struct Section {
    pub issue_id: String,
    pub passage_quote: String,
    pub text: String,
    pub severity: String,
    pub uncertainty: String,
    pub evidence: Vec<Evidence>,
}

#[derive(Debug, Deserialize)]
pub struct Evidence {
    pub source_id: String,
    pub quote: String,
}

impl Presentation {
    pub fn copy_text(&self) -> String {
        let mut text = format!("{}\n{}\n{}", self.intro, self.verdict, self.rationale);
        for section in &self.sections {
            text.push_str(&format!(
                "\n\nPassage: {}\n{}\nSeverity: {}; uncertainty: {}",
                section.passage_quote, section.text, section.severity, section.uncertainty
            ));
            for evidence in &section.evidence {
                text.push_str(&format!("\n{}: {}", evidence.source_id, evidence.quote));
            }
        }
        for evidence in &self.evidence {
            text.push_str(&format!("\n{}: {}", evidence.source_id, evidence.quote));
        }
        text.push_str(
            "\n\nQuotes checked against supplied text; reasoning still needs your review.",
        );
        text
    }
}

pub fn feedback(
    root: &Path,
    context: &str,
    source: &str,
    cancel: Arc<AtomicBool>,
) -> Result<Feedback, String> {
    let python = root.join(".venv/bin/python");
    if !python.exists() {
        return Err("Local Python environment missing. Run the project setup first.".into());
    }
    let request = serde_json::to_vec(&serde_json::json!({"passage":context,"source":source}))
        .map_err(|e| e.to_string())?;
    let mut child = Command::new(python)
        .args(["-m", "writing_ftm.widget_feedback"])
        .current_dir(root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;
    // Drain while running: four structured views can exceed the OS pipe buffer.
    let mut stdout = child.stdout.take().unwrap();
    let output_reader = std::thread::spawn(move || {
        let mut bytes = Vec::new();
        stdout.read_to_end(&mut bytes).map(|_| bytes)
    });
    let mut stderr = child.stderr.take().unwrap();
    std::thread::spawn(move || {
        let _ = std::io::copy(&mut stderr, &mut std::io::sink());
    });
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
    let status = child.wait().map_err(|e| e.to_string())?;
    let output = output_reader
        .join()
        .map_err(|_| "Local worker reader failed.")?
        .map_err(|e| e.to_string())?;
    let response: serde_json::Value = serde_json::from_slice(&output).map_err(|_| {
        "Local worker did not return valid feedback. Check the model installation.".to_string()
    })?;
    if let Some(error) = response.get("error").and_then(|v| v.as_str()) {
        return Err(error.into());
    }
    if !status.success() {
        return Err("Local critique failed.".into());
    }
    let feedback: Feedback = serde_json::from_value(response)
        .map_err(|_| "Local worker returned an incomplete critique.".to_string())?;
    for warmth in ["neutral", "warm"] {
        for directness in ["explanation-first", "action-first"] {
            if !feedback
                .presentations
                .contains_key(&format!("{warmth}/{directness}"))
            {
                return Err("Local worker returned incomplete tone controls.".into());
            }
        }
    }
    Ok(feedback)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn structured_output_larger_than_pipe_buffer_is_drained() {
        use std::os::unix::fs::PermissionsExt;
        let folder = tempfile::tempdir().unwrap();
        let bin = folder.path().join(".venv/bin");
        std::fs::create_dir_all(&bin).unwrap();
        let mut views = serde_json::Map::new();
        for warmth in ["neutral", "warm"] {
            for directness in ["explanation-first", "action-first"] {
                views.insert(
                    format!("{warmth}/{directness}"),
                    serde_json::json!({
                        "intro": "Evidence review", "verdict": "retain",
                        "rationale": "A".repeat(40000), "sections": [],
                        "evidence": [{"source_id": "source-1", "quote": "Evidence"}]
                    }),
                );
            }
        }
        let response = serde_json::json!({"presentations": views});
        let python = bin.join("python");
        std::fs::write(
            &python,
            format!("#!/bin/sh\ncat >/dev/null\ncat <<'RESULT'\n{response}\nRESULT\n"),
        )
        .unwrap();
        std::fs::set_permissions(&python, std::fs::Permissions::from_mode(0o700)).unwrap();
        let result = feedback(
            folder.path(),
            "Passage",
            "Evidence",
            Arc::new(AtomicBool::new(false)),
        )
        .unwrap();
        assert_eq!(result.presentations.len(), 4);
        assert_eq!(
            result.presentations["warm/action-first"].rationale.len(),
            40000
        );
        assert!(result.presentations["warm/action-first"]
            .copy_text()
            .contains("source-1: Evidence"));
    }
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
