mod capture;
mod worker;

use eframe::egui::{self, Color32, Pos2, Vec2};
use std::path::PathBuf;
use std::sync::{
    atomic::{AtomicBool, Ordering},
    mpsc, Arc,
};
use std::time::{Duration, Instant};

const COMPACT_SIZE: Vec2 = Vec2::new(104., 92.);
const PANEL_SIZE: Vec2 = Vec2::new(520., 720.);
const EXPAND_DURATION: Duration = Duration::from_millis(320);

struct Expansion {
    started: Instant,
    opening: bool,
}

enum Event {
    Captured(u64),
    Capture(u64, Result<capture::Snapshot, String>),
    Feedback(u64, Result<String, String>),
}

struct Companion {
    expanded: bool,
    expansion: Option<Expansion>,
    mascot: egui::TextureHandle,
    showing_feedback: bool,
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
    fn new(root: PathBuf, ctx: &egui::Context) -> Self {
        let image = image::load_from_memory(include_bytes!("../assets/companion-bot-v1.png"))
            .expect("embedded companion PNG")
            .into_rgba8();
        let mascot = ctx.load_texture(
            "companion",
            egui::ColorImage::from_rgba_unmultiplied(
                [image.width() as usize, image.height() as usize],
                image.as_raw(),
            ),
            egui::TextureOptions::LINEAR,
        );
        let (sender, receiver) = mpsc::channel();
        Self {
            expanded: false,
            expansion: None,
            mascot,
            showing_feedback: false,
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
        if self.expanded == expanded || self.expansion.is_some() {
            return;
        }
        self.expanded = expanded;
        self.expansion = Some(Expansion {
            started: Instant::now(),
            opening: expanded,
        });
        if expanded {
            // Allocate a transparent canvas once; animate its contents rather
            // than repeatedly resizing the native window and reflowing text.
            let origin = ctx.input(|i| i.viewport().outer_rect.map(|r| r.min));
            ctx.send_viewport_cmd(egui::ViewportCommand::InnerSize(PANEL_SIZE));
            if let Some(origin) = origin {
                ctx.send_viewport_cmd(egui::ViewportCommand::OuterPosition(origin));
            }
        }
        ctx.request_repaint();
    }
    fn expansion_progress(&mut self, ctx: &egui::Context) -> f32 {
        let Some(animation) = &self.expansion else {
            return if self.expanded { 1. } else { 0. };
        };
        let t = (animation.started.elapsed().as_secs_f32() / EXPAND_DURATION.as_secs_f32()).min(1.);
        let eased = t * t * (3. - 2. * t);
        let progress = if animation.opening { eased } else { 1. - eased };
        if t >= 1. {
            self.expansion = None;
            if !self.expanded {
                let origin = ctx.input(|i| i.viewport().outer_rect.map(|r| r.min));
                ctx.send_viewport_cmd(egui::ViewportCommand::InnerSize(COMPACT_SIZE));
                if let Some(origin) = origin {
                    ctx.send_viewport_cmd(egui::ViewportCommand::OuterPosition(origin));
                }
            }
        } else {
            ctx.request_repaint_after(Duration::from_millis(16));
        }
        progress
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
        self.showing_feedback = false;
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
                            self.showing_feedback = true;
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
        let progress = self.expansion_progress(ctx);
        if !self.expanded && self.expansion.is_none() {
            egui::CentralPanel::default()
                .frame(egui::Frame::NONE)
                .show(ctx, |ui| {
                    let (rect, response) =
                        ui.allocate_exact_size(Vec2::new(104., 88.), egui::Sense::click_and_drag());
                    response.widget_info(|| {
                        egui::WidgetInfo::labeled(
                            egui::WidgetType::Button,
                            true,
                            "Open Writing FTM overlay",
                        )
                    });
                    ui.painter().image(
                        self.mascot.id(),
                        rect,
                        egui::Rect::from_min_max(Pos2::ZERO, Pos2::new(1., 1.)),
                        Color32::WHITE,
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
        let transitioning = self.expansion.is_some();
        let panel_rect = egui::Rect::from_min_size(
            Pos2::ZERO,
            COMPACT_SIZE + (PANEL_SIZE - COMPACT_SIZE) * progress,
        );
        let content_opacity = ((progress - 0.4) / 0.6).clamp(0., 1.);
        let painter = ctx.layer_painter(egui::LayerId::background());
        painter.rect_filled(panel_rect, 22., PAPER.gamma_multiply(progress));
        painter.rect_stroke(
            panel_rect,
            22.,
            egui::Stroke::new(1_f32, BORDER.gamma_multiply(progress)),
            egui::StrokeKind::Inside,
        );
        egui::CentralPanel::default()
            .frame(egui::Frame::NONE.inner_margin(24.))
            .show(ctx, |ui| {
                // Full-size layout stays stable behind the expanding mask.
                ui.set_clip_rect(panel_rect.shrink(1.));
                ui.set_opacity(content_opacity);
                if transitioning { ui.disable(); }
                ui.horizontal(|ui| {
                    let bot = ui.add(egui::Image::new(&self.mascot)
                        .fit_to_exact_size(Vec2::new(44., 38.))
                        .sense(egui::Sense::click()));
                    bot.widget_info(|| egui::WidgetInfo::labeled(
                        egui::WidgetType::Button, !transitioning, "Collapse Writing FTM overlay"));
                    if bot.on_hover_text("Click to return to the companion")
                        .on_hover_cursor(egui::CursorIcon::PointingHand).clicked() {
                        self.expand(ctx, false);
                    }
                    let title = ui.add(egui::Label::new(egui::RichText::new("Writing FTM").size(19.).strong())
                        .sense(egui::Sense::drag()));
                    if title.drag_started() { ctx.send_viewport_cmd(egui::ViewportCommand::StartDrag); }
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        if ui.button("Hide").on_hover_text("Return to the companion").clicked() { self.expand(ctx, false); }
                        ui.menu_button("More", |ui| {
                            if ui.add_enabled(!self.busy, egui::Button::new("Try an example")).clicked() {
                                self.context = "Draft: The workshop caused higher confidence.\nSource: Participants chose whether to attend. Attendance was associated with confidence in a one-time survey.".into();
                                self.feedback.clear(); self.preview = None; self.showing_feedback = false;
                                self.status = "Example loaded. This is not a screen capture.".into(); ui.close_menu();
                            }
                            if ui.button("Clear context and feedback").clicked() {
                                self.cancel(); self.context.clear(); self.feedback.clear(); self.preview = None;
                                self.showing_feedback = false; self.status = "Context cleared.".into(); ui.close_menu();
                            }
                            ui.separator();
                            if ui.button("Quit Writing FTM").clicked() { ctx.send_viewport_cmd(egui::ViewportCommand::Close); }
                        });
                    });
                });
                ui.add_space(20.);
                ui.label(egui::RichText::new("A fresh pair of eyes.").size(27.));
                ui.label(egui::RichText::new("Bring a passage. Get a little perspective.").color(MUTED));
                ui.add_space(18.);
                ui.horizontal(|ui| {
                    if ui.selectable_label(!self.showing_feedback, "Your draft").clicked() { self.showing_feedback = false; }
                    if ui.selectable_label(self.showing_feedback, "Feedback").clicked() { self.showing_feedback = true; }
                });
                ui.add_space(12.);
                // Reserve the bottom for the main action so it never gets lost
                // below a long screenshot, draft, or response.
                let body_height = (ui.available_height() - 126.).max(180.);
                egui::ScrollArea::vertical().id_salt("review-body").max_height(body_height)
                    .min_scrolled_height(body_height).auto_shrink([false, false]).show(ui, |ui| {
                    ui.set_min_height(body_height);
                    if self.showing_feedback {
                        card().show(ui, |ui| {
                            ui.set_width(ui.available_width());
                            if self.feedback.is_empty() {
                                ui.add_space(24.);
                                ui.label(egui::RichText::new(if self.busy { "Taking a closer look…" } else { "Room for a second thought." }).size(20.));
                                ui.add_space(8.);
                                ui.label(if self.busy { "Your local model is working. You can cancel below." } else { "Add your draft, then ask for feedback. Your notes will appear here." });
                                ui.add_space(24.);
                            } else {
                                ui.label(egui::RichText::new("A few thoughts").size(20.).strong());
                                ui.add_space(12.);
                                ui.add(egui::Label::new(&self.feedback).selectable(true).wrap());
                                ui.add_space(16.);
                                if ui.button("Copy feedback").clicked() { ctx.copy_text(self.feedback.clone()); }
                                ui.add_space(8.);
                                ui.label(egui::RichText::new("A suggestion, not a verdict. Check important claims.").small().color(MUTED));
                            }
                        });
                    } else {
                        ui.horizontal(|ui| {
                            if ui.add_enabled(!self.busy, egui::Button::new("Capture screen").min_size(Vec2::new(144., 36.))).clicked() { self.capture(ctx, false); }
                            if ui.add_enabled(!self.busy, egui::Button::new("Choose an area").min_size(Vec2::new(144., 36.))).clicked() { self.capture(ctx, true); }
                        });
                        ui.add_space(12.);
                        if let Some(texture) = &self.preview {
                            egui::CollapsingHeader::new("Captured screen").show(ui, |ui| {
                                ui.add(egui::Image::new(texture).max_height(120.).max_width(ui.available_width()).maintain_aspect_ratio(true));
                                ui.label(egui::RichText::new("A snapshot, not a live view. Check the extracted text below.").small().color(MUTED));
                            });
                            ui.add_space(8.);
                        }
                        card().show(ui, |ui| {
                            ui.horizontal(|ui| {
                                ui.label(egui::RichText::new("Your passage").strong());
                                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                    let count = self.context.chars().count();
                                    ui.label(egui::RichText::new(format!("{count} / 8,000")).small().color(if count > 8000 { Color32::from_rgb(160, 55, 45) } else { MUTED }));
                                });
                            });
                            ui.add_space(8.);
                            ui.add(egui::TextEdit::multiline(&mut self.context).font(egui::TextStyle::Body)
                                .frame(false).desired_rows(5).desired_width(f32::INFINITY)
                                .hint_text("Paste something you're working on, or capture it from your screen…"));
                        });
                        ui.add_space(14.);
                        ui.label(egui::RichText::new("What should I focus on?").strong());
                        ui.add_space(4.);
                        ui.add(egui::TextEdit::multiline(&mut self.task).font(egui::TextStyle::Body)
                            .desired_rows(2).desired_width(f32::INFINITY));
                        if self.task.chars().count() > 1000 {
                            ui.colored_label(Color32::from_rgb(160, 55, 45), "Keep your request under 1,000 characters.");
                        }
                    }
                });
                ui.add_space(12.);
                let valid = !self.busy && !self.context.trim().is_empty() && self.context.chars().count() <= 8000
                    && !self.task.trim().is_empty() && self.task.chars().count() <= 1000;
                ui.horizontal(|ui| {
                    if self.busy {
                        ui.spinner();
                        if ui.add_sized([ui.available_width(), 42.], egui::Button::new("Cancel")).clicked() { self.cancel(); }
                    } else if ui.add_enabled(valid, egui::Button::new(egui::RichText::new("Give feedback").color(Color32::WHITE))
                        .fill(INK).min_size(Vec2::new(ui.available_width(), 42.))).clicked() { self.review(ctx); }
                });
                ui.add_space(6.);
                ui.label(egui::RichText::new(&self.status).size(12.).color(MUTED));
                ui.add_space(4.);
                ui.label(egui::RichText::new("On this Mac · Captures only when you ask").size(12.).color(MUTED))
                    .on_hover_text("Screen text is processed locally. The model reads extracted text, not images. Nothing is sent to a cloud service. Clear the session from More.");
            });
        if transitioning {
            let bot_min = Pos2::ZERO.lerp(Pos2::new(24., 24.), progress);
            let bot_size = Vec2::new(104., 88.) + Vec2::new(-60., -50.) * progress;
            ctx.layer_painter(egui::LayerId::new(
                egui::Order::Foreground,
                egui::Id::new("expanding-bot"),
            ))
            .image(
                self.mascot.id(),
                egui::Rect::from_min_size(bot_min, bot_size),
                egui::Rect::from_min_max(Pos2::ZERO, Pos2::new(1., 1.)),
                Color32::WHITE.gamma_multiply(1. - content_opacity),
            );
        }
    }
}

const PAPER: Color32 = Color32::from_rgb(245, 244, 239);
const INK: Color32 = Color32::from_rgb(43, 45, 44);
const MUTED: Color32 = Color32::from_rgb(100, 105, 100);
const BORDER: Color32 = Color32::from_rgb(222, 222, 214);

fn card() -> egui::Frame {
    egui::Frame::new()
        .fill(Color32::from_rgb(255, 254, 251))
        .inner_margin(16.)
        .corner_radius(14.)
        .stroke(egui::Stroke::new(1_f32, BORDER))
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
            .with_inner_size([104., 92.])
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
            let mut visuals = egui::Visuals::light();
            visuals.override_text_color = Some(INK);
            visuals.panel_fill = PAPER;
            visuals.extreme_bg_color = Color32::from_rgb(255, 254, 251);
            visuals.selection.bg_fill = Color32::from_rgb(218, 222, 213);
            visuals.selection.stroke = egui::Stroke::new(1_f32, INK);
            visuals.widgets.inactive.weak_bg_fill = Color32::from_rgb(235, 234, 228);
            visuals.widgets.inactive.bg_stroke = egui::Stroke::NONE;
            visuals.widgets.hovered.weak_bg_fill = Color32::from_rgb(222, 224, 216);
            visuals.widgets.hovered.bg_stroke = egui::Stroke::new(1_f32, BORDER);
            for widget in [
                &mut visuals.widgets.inactive,
                &mut visuals.widgets.hovered,
                &mut visuals.widgets.active,
            ] {
                widget.corner_radius = egui::CornerRadius::same(10);
            }
            cc.egui_ctx.set_visuals(visuals);
            let mut style = (*cc.egui_ctx.style()).clone();
            style
                .text_styles
                .insert(egui::TextStyle::Body, egui::FontId::proportional(16.));
            style
                .text_styles
                .insert(egui::TextStyle::Button, egui::FontId::proportional(14.));
            style
                .text_styles
                .insert(egui::TextStyle::Small, egui::FontId::proportional(12.));
            style.spacing.button_padding = egui::vec2(12., 8.);
            style.spacing.item_spacing = egui::vec2(10., 8.);
            style.spacing.interact_size.y = 32.;
            cc.egui_ctx.set_style(style);
            Ok(Box::new(Companion::new(root, &cc.egui_ctx)))
        }),
    )
}
