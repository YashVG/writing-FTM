mod capture;
mod worker;

use eframe::egui::{self, Color32, Pos2, Vec2};
use std::path::PathBuf;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    mpsc, Arc,
};
use std::time::Duration;

enum Event {
    Captured(u64),
    Capture(u64, Result<capture::Snapshot, String>),
    Feedback(u64, Result<String, String>),
}

struct Companion {
    expanded: bool,
    context: String,
    task: String,
    feedback: String,
    status: String,
    preview: Option<egui::TextureHandle>,
    busy: bool,
    epoch: u64,
    cancel: Arc<AtomicBool>,
    sender: mpsc::Sender<Event>,
    receiver: mpsc::Receiver<Event>,
    root: PathBuf,
}

impl Companion {
    fn new(root: PathBuf) -> Self {
        let (sender, receiver) = mpsc::channel();
        Self {
            expanded: false,
            context: String::new(),
            task: "Give me concise, actionable feedback on this work.".into(),
            feedback: String::new(),
            status: "Capture a screen or paste text to begin.".into(),
            preview: None,
            busy: false,
            epoch: 0,
            cancel: Arc::new(AtomicBool::new(false)),
            sender,
            receiver,
            root,
        }
    }
    fn expand(&mut self, ctx: &egui::Context, expanded: bool) {
        self.expanded = expanded;
        ctx.send_viewport_cmd(egui::ViewportCommand::InnerSize(if expanded {
            Vec2::new(560., 740.)
        } else {
            Vec2::splat(88.)
        }));
    }
    fn cancel(&mut self) {
        self.cancel.store(true, Ordering::Relaxed);
        self.epoch += 1;
        self.busy = false;
        self.status = "Cancelled.".into();
    }
    fn capture(&mut self, ctx: &egui::Context, interactive: bool) {
        self.epoch += 1;
        let epoch = self.epoch;
        self.busy = true;
        self.feedback.clear();
        self.context.clear();
        self.preview = None;
        self.status = if interactive {
            "Choose a region of your work. Escape cancels."
        } else {
            "Capturing the main display…"
        }
        .into();
        // Hide our overlay while the user selects the work area.
        ctx.send_viewport_cmd(egui::ViewportCommand::Visible(false));
        let sender = self.sender.clone();
        let repaint = ctx.clone();
        std::thread::spawn(move || {
            std::thread::sleep(Duration::from_millis(300));
            let result = capture::capture_screen(interactive, || {
                let _ = sender.send(Event::Captured(epoch));
                repaint.send_viewport_cmd(egui::ViewportCommand::Visible(true));
                repaint.request_repaint();
            });
            let _ = sender.send(Event::Capture(epoch, result));
            repaint.send_viewport_cmd(egui::ViewportCommand::Visible(true));
            repaint.request_repaint();
        });
    }
    fn review(&mut self, ctx: &egui::Context) {
        self.epoch += 1;
        let epoch = self.epoch;
        self.busy = true;
        self.feedback.clear();
        self.status = "Thinking locally… the first request loads the model.".into();
        self.cancel = Arc::new(AtomicBool::new(false));
        let cancel = self.cancel.clone();
        let sender = self.sender.clone();
        let repaint = ctx.clone();
        let root = self.root.clone();
        let context = self.context.clone();
        let task = self.task.clone();
        std::thread::spawn(move || {
            let result = worker::feedback(&root, &context, &task, cancel);
            let _ = sender.send(Event::Feedback(epoch, result));
            repaint.request_repaint();
        });
    }
    fn events(&mut self, ctx: &egui::Context) {
        while let Ok(event) = self.receiver.try_recv() {
            match event {
                Event::Captured(id) if id == self.epoch => {
                    self.status =
                        "Reading captured text locally… first use may take longer.".into();
                }
                Event::Capture(id, result) if id == self.epoch => {
                    self.busy = false;
                    match result {
                        Ok(snapshot) => {
                            self.preview = Some(ctx.load_texture(
                                "captured work",
                                snapshot.image,
                                Default::default(),
                            ));
                            self.context = snapshot.text;
                            self.status = if self.context.trim().is_empty() {
                                "No readable text found. Paste or type the relevant text below."
                            } else {
                                "Captured just now. Review or edit the text, then ask for feedback."
                            }
                            .into();
                        }
                        Err(error) => self.status = error,
                    }
                }
                Event::Feedback(id, result) if id == self.epoch => {
                    self.busy = false;
                    match result {
                        Ok(text) => {
                            self.feedback = text;
                            self.status =
                                "Ready. Feedback uses the text shown below, not a live view."
                                    .into();
                        }
                        Err(error) => self.status = error,
                    }
                }
                _ => {}
            }
        }
    }
}

impl Drop for Companion {
    fn drop(&mut self) {
        self.cancel.store(true, Ordering::Relaxed);
    }
}

impl eframe::App for Companion {
    fn clear_color(&self, _visuals: &egui::Visuals) -> [f32; 4] {
        [0., 0., 0., 0.]
    }
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.events(ctx);
        if !self.expanded {
            egui::CentralPanel::default()
                .frame(egui::Frame::NONE)
                .show(ctx, |ui| {
                    let (rect, response) =
                        ui.allocate_exact_size(Vec2::splat(80.), egui::Sense::click_and_drag());
                    response.widget_info(|| {
                        egui::WidgetInfo::labeled(
                            egui::WidgetType::Button,
                            true,
                            "Open Writing FTM overlay",
                        )
                    });
                    let center = rect.center();
                    let painter = ui.painter();
                    painter.circle_filled(
                        center + Vec2::new(0., 3.),
                        35.,
                        Color32::from_black_alpha(35),
                    );
                    painter.circle_filled(center, 33., Color32::from_rgb(27, 97, 85));
                    painter.circle_filled(
                        center + Vec2::new(-16., -24.),
                        10.,
                        Color32::from_rgb(27, 97, 85),
                    );
                    painter.circle_filled(
                        center + Vec2::new(16., -24.),
                        10.,
                        Color32::from_rgb(27, 97, 85),
                    );
                    for x in [-11., 11.] {
                        painter.circle_filled(
                            center + Vec2::new(x, -3.),
                            8.,
                            Color32::from_rgb(235, 239, 218),
                        );
                        painter.circle_filled(
                            center + Vec2::new(x + 1., -2.),
                            3.5,
                            Color32::from_rgb(18, 44, 39),
                        );
                    }
                    painter.line_segment(
                        [center + Vec2::new(-5., 14.), center + Vec2::new(5., 14.)],
                        (2., Color32::from_rgb(235, 239, 218)),
                    );
                    if response.drag_started() {
                        ctx.send_viewport_cmd(egui::ViewportCommand::StartDrag);
                    }
                    if response.clicked() {
                        self.expand(ctx, true);
                    }
                    response
                        .clone()
                        .on_hover_text("Writing FTM · click for feedback · drag to move");
                    response.context_menu(|ui| {
                        if ui.button("Open feedback").clicked() {
                            self.expand(ctx, true);
                            ui.close_menu();
                        }
                        if ui.button("Quit Writing FTM").clicked() {
                            ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                        }
                    });
                });
            return;
        }
        egui::CentralPanel::default().frame(egui::Frame::new().fill(Color32::from_rgb(246, 245, 239)).inner_margin(20.).corner_radius(18.)).show(ctx, |ui| {
            ui.horizontal(|ui| {
                let title = ui.add(egui::Label::new(egui::RichText::new("Writing FTM").size(23.).strong()).sense(egui::Sense::drag()));
                if title.drag_started() { ctx.send_viewport_cmd(egui::ViewportCommand::StartDrag); }
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    if ui.button("Collapse").clicked() { self.expand(ctx, false); }
                    ui.menu_button("More", |ui| {
                        if ui.button("Clear context and feedback").clicked() { self.cancel(); self.context.clear(); self.feedback.clear(); self.preview = None; self.status = "Context cleared.".into(); ui.close_menu(); }
                        if ui.button("Quit").clicked() { ctx.send_viewport_cmd(egui::ViewportCommand::Close); }
                    });
                });
            });
            ui.label(egui::RichText::new("A second look at your work.").color(Color32::from_rgb(74, 100, 91)));
            ui.add_space(8.);
            ui.label("On-demand capture · on-device OCR · local model");
            ui.separator();
            ui.horizontal(|ui| {
                if ui.add_enabled(!self.busy, egui::Button::new("Capture work area")).clicked() { self.capture(ctx, true); }
                if ui.add_enabled(!self.busy, egui::Button::new("Capture display")).clicked() { self.capture(ctx, false); }
                if ui.add_enabled(!self.busy, egui::Button::new("Load example")).clicked() {
                    self.context = "Draft: The workshop caused higher confidence.\nSource: Participants chose whether to attend. Attendance was associated with confidence in a one-time survey.".into();
                    self.feedback.clear(); self.preview = None; self.status = "Example text loaded — not a screen capture.".into();
                }
                if self.busy && ui.button("Cancel").clicked() { self.cancel(); }
            });
            ui.add_space(6.);
            ui.label(&self.status);
            ui.add_space(8.);
            egui::ScrollArea::vertical().show(ui, |ui| {
                if let Some(texture) = &self.preview {
                    ui.add(egui::Image::new(texture).max_height(140.).max_width(ui.available_width()).maintain_aspect_ratio(true));
                }
                ui.label(egui::RichText::new("Context to review").strong());
                ui.label(egui::RichText::new("Edit OCR errors or paste a passage. Screen text is not automatically verified evidence.").small());
                ui.add(egui::TextEdit::multiline(&mut self.context).desired_rows(7).desired_width(f32::INFINITY).hint_text("Capture a work area, or paste text here…"));
                ui.label(format!("{} / 8,000 characters", self.context.chars().count()));
                ui.add_space(8.);
                ui.label(egui::RichText::new("What would you like help with?").strong());
                ui.add(egui::TextEdit::multiline(&mut self.task).desired_rows(2).desired_width(f32::INFINITY));
                let valid = !self.busy && !self.context.trim().is_empty() && self.context.chars().count() <= 8000 && !self.task.trim().is_empty() && self.task.chars().count() <= 1000;
                if ui.add_enabled(valid, egui::Button::new("Give feedback").fill(Color32::from_rgb(180, 218, 200))).clicked() { self.review(ctx); }
                if !self.feedback.is_empty() {
                    ui.add_space(12.); ui.separator(); ui.heading("Feedback");
                    ui.add(egui::Label::new(&self.feedback).selectable(true).wrap());
                    if ui.button("Copy feedback").clicked() { ctx.copy_text(self.feedback.clone()); }
                }
                ui.add_space(12.);
                ui.label(egui::RichText::new("Review suggestions critically. The model reads extracted text, not images or your activity history. Nothing is sent to a cloud service.").small().color(Color32::DARK_GRAY));
            });
        });
    }
}

fn project_root() -> Result<PathBuf, String> {
    if let Some(root) = std::env::var_os("WRITING_FTM_ROOT") {
        return Ok(root.into());
    }
    let exe = std::env::current_exe().map_err(|e| e.to_string())?;
    if let Some(contents) = exe.parent().and_then(|p| p.parent()) {
        let config = contents.join("Resources/project-root.txt");
        if let Ok(root) = std::fs::read_to_string(config) {
            return Ok(PathBuf::from(root.trim()));
        }
    }
    Ok(PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf())
}

fn main() -> eframe::Result<()> {
    let root = project_root().expect("Unable to locate Writing FTM project");
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_title("Writing FTM")
            .with_inner_size([88., 88.])
            .with_position(Pos2::new(40., 120.))
            .with_decorations(false)
            .with_transparent(true)
            .with_resizable(false)
            .with_always_on_top(),
        ..Default::default()
    };
    eframe::run_native(
        "Writing FTM",
        options,
        Box::new(move |cc| {
            cc.egui_ctx.set_visuals(egui::Visuals::light());
            let mut style = (*cc.egui_ctx.style()).clone();
            style
                .text_styles
                .insert(egui::TextStyle::Body, egui::FontId::proportional(15.));
            style
                .text_styles
                .insert(egui::TextStyle::Button, egui::FontId::proportional(14.));
            style.spacing.button_padding = egui::vec2(10., 6.);
            style.spacing.item_spacing = egui::vec2(8., 8.);
            cc.egui_ctx.set_style(style);
            Ok(Box::new(Companion::new(root)))
        }),
    )
}
