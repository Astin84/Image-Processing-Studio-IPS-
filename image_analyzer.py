import sys
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QFrame, QGroupBox,
    QScrollArea, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QDialog, QTextEdit, QDoubleSpinBox, QSpinBox, QDialogButtonBox,
    QTabWidget, QSizePolicy, QSplitter
)
from PyQt5.QtGui import QFont, QPixmap, QImage, QColor
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────
# Dialog: filter / noise / denoise parameters
# ─────────────────────────────────────────────
class FilterParamsDialog(QDialog):
    def __init__(self, filter_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"⚙️ {filter_name} Parameters")
        self.setModal(True)
        self.resize(350, 220)
        self.params = {}

        layout = QVBoxLayout(self)

        title_label = QLabel(f"📐 {filter_name} Settings")
        title_label.setObjectName("DialogTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Tahoma", 11, QFont.Bold))
        layout.addWidget(title_label)

        if "Noise" in filter_name and "Denoise" not in filter_name:
            layout.addWidget(QLabel("Noise Strength (0.0-1.0):"))
            self.params["strength"] = QDoubleSpinBox()
            self.params["strength"].setRange(0.0, 1.0)
            self.params["strength"].setValue(0.5)
            self.params["strength"].setSingleStep(0.1)
            layout.addWidget(self.params["strength"])

        elif "Denoise" in filter_name:
            layout.addWidget(QLabel("Denoise Strength (0.0-1.0):"))
            self.params["strength"] = QDoubleSpinBox()
            self.params["strength"].setRange(0.0, 1.0)
            self.params["strength"].setValue(0.5)
            self.params["strength"].setSingleStep(0.1)
            layout.addWidget(self.params["strength"])

        elif filter_name in ["Low Pass", "High Pass", "Notch Pass", "Notch Reject", "Gaussian"]:
            layout.addWidget(QLabel("Cutoff Frequency:"))
            self.params["cutoff"] = QSpinBox()
            self.params["cutoff"].setRange(5, 200)
            self.params["cutoff"].setValue(30)
            layout.addWidget(self.params["cutoff"])

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_params(self):
        return self.params

# ─────────────────────────────────────────────
# Dialog: shows CV2 code snippet
# ─────────────────────────────────────────────
class CodeViewerDialog(QDialog):
    def __init__(self, title, code, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"📋 {title} - CV2 Code")
        self.setModal(True)
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        title_label = QLabel(f"🔍 {title} Implementation")
        title_label.setObjectName("DialogTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Tahoma", 11, QFont.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        self.code_display = QTextEdit()
        self.code_display.setObjectName("StatsBox")
        self.code_display.setReadOnly(True)
        self.code_display.setFont(QFont("Consolas", 10))
        self.code_display.setPlainText(code)

        cursor = self.code_display.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.code_display.setTextCursor(cursor)

        layout.addWidget(self.code_display)

        close_btn = QPushButton("✅ Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

# ─────────────────────────────────────────────
# Matplotlib canvas helper
# ─────────────────────────────────────────────
class MplCanvas(FigureCanvas):
    def __init__(self, figsize=(7, 4)):
        self.fig = Figure(figsize=figsize, dpi=100, facecolor='#FAFAF8')
        self.ax = self.fig.add_subplot(111, facecolor='#FAFAF8')
        super().__init__(self.fig)

# ─────────────────────────────────────────────
# Zoomable / pan-able QGraphicsView
# ─────────────────────────────────────────────
class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        zoom_in = 1.25
        zoom_out = 1 / zoom_in
        if event.angleDelta().y() > 0:
            self.scale(zoom_in, zoom_in)
        else:
            self.scale(zoom_out, zoom_out)

# ─────────────────────────────────────────────
# Main application window
# ─────────────────────────────────────────────
class ImageAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Analyzer -- Ver 1.5.1 (LIGHT XP STYLE - RESIZABLE SIDEBAR)")
        self.resize(1600, 900)

        self.original_bgr = None
        self.working_bgr  = None
        self.visualization_mode = "combined"
        self.current_filter_code   = ""
        self.current_denoise_code  = ""
        self.current_freq_code     = ""

        # ── central layout with SPLITTER ──
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        # Create a splitter to make sidebar resizable
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(6)
        self.splitter.setChildrenCollapsible(False)
        
        # ── SCROLLABLE SIDEBAR ──
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sidebar_scroll.setObjectName("SidebarScroll")

        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setMinimumWidth(400)  # Increased from 320
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(8)
        sidebar_layout.setContentsMargins(6, 12, 6, 12)

        sidebar_scroll.setWidget(sidebar)

        # ── sidebar title ──
        title_label = QLabel("Image Tasks")
        title_label.setObjectName("TaskTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Tahoma", 12, QFont.Bold))
        sidebar_layout.addWidget(title_label)

        # ══════════════════════════════════════
        # FILE group
        # ══════════════════════════════════════
        file_group = QGroupBox("File")
        file_group.setObjectName("LightGroup")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(6)
        file_layout.setContentsMargins(12, 20, 12, 12)

        self.btn_open  = self.create_xp_button("📂 Open Image", self.open_image)
        self.btn_save  = self.create_xp_button("💾 Save Image", self.save_image)
        self.btn_reset = self.create_xp_button("🔄 Reset Image", self.reset_image)
        self.btn_save.setEnabled(False)
        self.btn_reset.setEnabled(False)

        file_layout.addWidget(self.btn_open)
        file_layout.addWidget(self.btn_save)
        file_layout.addWidget(self.btn_reset)
        sidebar_layout.addWidget(file_group)

        # ══════════════════════════════════════
        # VISUALIZATION group  (toggle panel)
        # ══════════════════════════════════════
        vis_group = QGroupBox("Visualization")
        vis_group.setObjectName("LightGroup")
        vis_layout = QVBoxLayout(vis_group)
        vis_layout.setSpacing(6)
        vis_layout.setContentsMargins(12, 20, 12, 12)

        self.btn_visualization = self.create_xp_button("📊 Visualization Options", None)
        self.btn_visualization.setCheckable(True)
        self.btn_visualization.clicked.connect(self.toggle_visualization_panel)
        self.btn_visualization.setEnabled(False)
        vis_layout.addWidget(self.btn_visualization)

        self.visualization_panel = QFrame()
        self.visualization_panel.setObjectName("LightSubPanel")
        vis_sub_layout = QVBoxLayout(self.visualization_panel)
        vis_sub_layout.setSpacing(2)
        vis_sub_layout.setContentsMargins(24, 8, 8, 8)

        self.btn_combined  = self.create_sub_button("🎨 Combined (RGB)",     lambda: self.set_vis_mode("combined"))
        self.btn_grayscale = self.create_sub_button("⬜ Grayscale",          lambda: self.set_vis_mode("grayscale"))
        self.btn_red       = self.create_sub_button("🔴 Red Channel",        lambda: self.set_vis_mode("red"))
        self.btn_green     = self.create_sub_button("🟢 Green Channel",      lambda: self.set_vis_mode("green"))
        self.btn_blue      = self.create_sub_button("🔵 Blue Channel",       lambda: self.set_vis_mode("blue"))
        self.btn_hsi       = self.create_sub_button("🌈 HSI Color Space",    lambda: self.set_vis_mode("hsi"))

        for b in [self.btn_combined, self.btn_grayscale, self.btn_red,
                  self.btn_green, self.btn_blue, self.btn_hsi]:
            vis_sub_layout.addWidget(b)

        self.visualization_panel.setVisible(False)
        vis_layout.addWidget(self.visualization_panel)
        sidebar_layout.addWidget(vis_group)

        # ══════════════════════════════════════
        # OPERATIONS group  (toggle panel)
        # ══════════════════════════════════════
        ops_group = QGroupBox("Operations")
        ops_group.setObjectName("LightGroup")
        ops_layout = QVBoxLayout(ops_group)
        ops_layout.setSpacing(6)
        ops_layout.setContentsMargins(12, 20, 12, 12)

        self.btn_ops = self.create_xp_button("⚙️ Image Operations", None)
        self.btn_ops.setCheckable(True)
        self.btn_ops.clicked.connect(self.toggle_ops_panel)
        self.btn_ops.setEnabled(False)
        ops_layout.addWidget(self.btn_ops)

        self.ops_panel = QFrame()
        self.ops_panel.setObjectName("LightSubPanel")
        ops_sub_layout = QVBoxLayout(self.ops_panel)
        ops_sub_layout.setSpacing(2)
        ops_sub_layout.setContentsMargins(24, 8, 8, 8)

        self.btn_invert   = self.create_sub_button("🔁 Invert",        self.invert_image)
        self.btn_flip_h   = self.create_sub_button("↔️ Flip H",        self.flip_horizontal)
        self.btn_flip_v   = self.create_sub_button("↕️ Flip V",        self.flip_vertical)
        self.btn_rotate90 = self.create_sub_button("🔃 Rotate 90°",    self.rotate_90)
        self.btn_equalize = self.create_sub_button("📊 Equalize",       self.equalize_histogram)

        for b in [self.btn_invert, self.btn_flip_h, self.btn_flip_v,
                  self.btn_rotate90, self.btn_equalize]:
            ops_sub_layout.addWidget(b)

        self.ops_panel.setVisible(False)
        ops_layout.addWidget(self.ops_panel)
        sidebar_layout.addWidget(ops_group)

        # ══════════════════════════════════════
        # DENOISE group  (toggle panel)
        # ══════════════════════════════════════
        denoise_group = QGroupBox("Denoise")
        denoise_group.setObjectName("LightGroup")
        denoise_layout = QVBoxLayout(denoise_group)
        denoise_layout.setSpacing(6)
        denoise_layout.setContentsMargins(12, 20, 12, 12)

        self.btn_denoise = self.create_xp_button("🧹 Denoise", None)
        self.btn_denoise.setCheckable(True)
        self.btn_denoise.clicked.connect(self.toggle_denoise_panel)
        self.btn_denoise.setEnabled(False)
        denoise_layout.addWidget(self.btn_denoise)

        self.denoise_panel = QFrame()
        self.denoise_panel.setObjectName("LightSubPanel")
        denoise_sub_layout = QVBoxLayout(self.denoise_panel)
        denoise_sub_layout.setSpacing(2)
        denoise_sub_layout.setContentsMargins(24, 8, 8, 8)

        self.btn_bilateral  = self.create_sub_button("🏔️ Bilateral",       lambda: self.show_denoise_dialog("Bilateral"))
        self.btn_mean       = self.create_sub_button("📐 Mean",            lambda: self.show_denoise_dialog("Mean"))
        self.btn_median     = self.create_sub_button("📊 Median",          lambda: self.show_denoise_dialog("Median"))
        self.btn_nlmeans    = self.create_sub_button("🧠 Non-Local Means", lambda: self.show_denoise_dialog("Non-Local Means"))

        for b in [self.btn_bilateral, self.btn_mean, self.btn_median, self.btn_nlmeans]:
            denoise_sub_layout.addWidget(b)

        self.denoise_panel.setVisible(False)
        denoise_layout.addWidget(self.denoise_panel)
        sidebar_layout.addWidget(denoise_group)

        # ══════════════════════════════════════
        # NOISE group  (toggle panel)
        # ══════════════════════════════════════
        noise_group = QGroupBox("Add Noise")
        noise_group.setObjectName("LightGroup")
        noise_layout = QVBoxLayout(noise_group)
        noise_layout.setSpacing(6)
        noise_layout.setContentsMargins(12, 20, 12, 12)

        self.btn_noise = self.create_xp_button("🎚️ Add noise", None)
        self.btn_noise.setCheckable(True)
        self.btn_noise.clicked.connect(self.toggle_noise_panel)
        self.btn_noise.setEnabled(False)
        noise_layout.addWidget(self.btn_noise)

        self.noise_panel = QFrame()
        self.noise_panel.setObjectName("LightSubPanel")
        noise_sub_layout = QVBoxLayout(self.noise_panel)
        noise_sub_layout.setSpacing(2)
        noise_sub_layout.setContentsMargins(24, 8, 8, 8)

        self.btn_pepper_salt   = self.create_sub_button("🧂 Pepper & Salt",  lambda: self.show_noise_dialog("Pepper & Salt"))
        self.btn_gaussian_noise= self.create_sub_button("📈 Gaussian Noise", lambda: self.show_noise_dialog("Gaussian"))
        self.btn_speckle_noise = self.create_sub_button("✨ Speckle Noise",  lambda: self.show_noise_dialog("Speckle"))
        self.btn_poisson_noise = self.create_sub_button("⚡ Poisson Noise",  lambda: self.show_noise_dialog("Poisson"))

        noise_sub_layout.addWidget(self.btn_pepper_salt)
        noise_sub_layout.addWidget(self.btn_gaussian_noise)
        noise_sub_layout.addWidget(self.btn_speckle_noise)
        noise_sub_layout.addWidget(self.btn_poisson_noise)

        self.noise_panel.setVisible(False)
        noise_layout.addWidget(self.noise_panel)
        sidebar_layout.addWidget(noise_group)

        # ══════════════════════════════════════
        # FREQUENCY FILTERS group  (toggle panel)
        # ══════════════════════════════════════
        filter_group = QGroupBox("Frequency Filters")
        filter_group.setObjectName("LightGroup")
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setSpacing(6)
        filter_layout.setContentsMargins(12, 20, 12, 12)

        self.btn_filters = self.create_xp_button("🎛️ Filters", None)
        self.btn_filters.setCheckable(True)
        self.btn_filters.clicked.connect(self.toggle_filters_panel)
        self.btn_filters.setEnabled(False)
        filter_layout.addWidget(self.btn_filters)

        self.filters_panel = QFrame()
        self.filters_panel.setObjectName("LightSubPanel")
        filters_sub_layout = QVBoxLayout(self.filters_panel)
        filters_sub_layout.setSpacing(2)
        filters_sub_layout.setContentsMargins(20, 6, 6, 6)

        self.btn_lowpass     = self.create_sub_button("🔽 Low Pass filter",    lambda: self.show_filter_dialog("Low Pass"))
        self.btn_highpass    = self.create_sub_button("🔼 High Pass filter",   lambda: self.show_filter_dialog("High Pass"))
        self.btn_notchpass   = self.create_sub_button("🎯 Notch Pass filter",  lambda: self.show_filter_dialog("Notch Pass"))
        self.btn_notchreject = self.create_sub_button("🚫 Notch Reject filter",lambda: self.show_filter_dialog("Notch Reject"))
        self.btn_gaussian    = self.create_sub_button("⛰️ Gaussian filter",    lambda: self.show_filter_dialog("Gaussian"))

        filters_sub_layout.addWidget(self.btn_lowpass)
        filters_sub_layout.addWidget(self.btn_highpass)
        filters_sub_layout.addWidget(self.btn_notchpass)
        filters_sub_layout.addWidget(self.btn_notchreject)
        filters_sub_layout.addWidget(self.btn_gaussian)

        self.filters_panel.setVisible(False)
        filter_layout.addWidget(self.filters_panel)
        sidebar_layout.addWidget(filter_group)

        # ══════════════════════════════════════
        # CODE VIEWER group  (toggle panel)
        # ══════════════════════════════════════
        code_group = QGroupBox("Code Viewer")
        code_group.setObjectName("LightGroup")
        code_layout = QVBoxLayout(code_group)
        code_layout.setSpacing(6)
        code_layout.setContentsMargins(12, 20, 12, 12)

        self.btn_code = self.create_xp_button("📋 Show CV2 code", None)
        self.btn_code.setCheckable(True)
        self.btn_code.clicked.connect(self.toggle_code_panel)
        self.btn_code.setEnabled(False)
        code_layout.addWidget(self.btn_code)

        self.code_panel = QFrame()
        self.code_panel.setObjectName("LightSubPanel")
        code_sub_layout = QVBoxLayout(self.code_panel)
        code_sub_layout.setSpacing(4)
        code_sub_layout.setContentsMargins(24, 8, 8, 8)

        self.btn_show_noise_code   = self.create_sub_button("🎚️ Noise Code",   self.show_current_noise_code)
        self.btn_show_denoise_code = self.create_sub_button("🧹 Denoise Code", self.show_current_denoise_code)
        self.btn_show_filter_code  = self.create_sub_button("🎛️ Filter Code",  self.show_current_filter_code)
        self.btn_show_stats_code   = self.create_sub_button("📊 HSI Code",     self.show_hsi_code)

        code_sub_layout.addWidget(self.btn_show_noise_code)
        code_sub_layout.addWidget(self.btn_show_denoise_code)
        code_sub_layout.addWidget(self.btn_show_filter_code)
        code_sub_layout.addWidget(self.btn_show_stats_code)

        self.code_panel.setVisible(False)
        code_layout.addWidget(self.code_panel)
        sidebar_layout.addWidget(code_group)

        # ══════════════════════════════════════
        # STATUS BAR
        # ══════════════════════════════════════
        status_frame = QFrame()
        status_frame.setObjectName("LightStatusFrame")
        status_frame.setFixedHeight(28)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(6, 4, 6, 4)

        self.status_label = QLabel("Ready - Resizable Sidebar Version")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setFont(QFont("Tahoma", 8))
        status_layout.addWidget(self.status_label)
        sidebar_layout.addWidget(status_frame)

        # ══════════════════════════════════════
        # CONTENT AREA  (right side)
        # ══════════════════════════════════════
        content = QFrame()
        content.setObjectName("Content")
        content.setFrameShape(QFrame.StyledPanel)
        content.setFrameShadow(QFrame.Sunken)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        # ── toolbar ──
        toolbar = QFrame()
        toolbar.setObjectName("LightToolbar")
        toolbar.setFixedHeight(48)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(30, 12, 30, 12)
        toolbar_layout.setSpacing(16)

        self.btn_fit = self.create_tool_button("🔍 Fit to Window", self.fit_to_window)
        self.btn_fit.setMinimumHeight(28)
        self.btn_fit.setEnabled(False)
        self.btn_reset_zoom = self.create_tool_button("🗺️ Reset Zoom (1:1)", self.reset_zoom)
        self.btn_reset_zoom.setMinimumHeight(12)
        self.btn_reset_zoom.setEnabled(False)

        toolbar_layout.addWidget(self.btn_fit)
        toolbar_layout.addWidget(self.btn_reset_zoom)
        toolbar_layout.addStretch(1)

        view_label = QLabel("🖼️ Image Preview & Analysis")
        view_label.setObjectName("ToolbarTitle")
        view_label.setFont(QFont("Tahoma", 10, QFont.Bold))
        view_label.setMinimumHeight(28)
        toolbar_layout.addWidget(view_label, 0, Qt.AlignCenter)
        toolbar_layout.addStretch(1)

        content_layout.addWidget(toolbar)

        # ── TAB WIDGET  (Image tab  +  Fourier tab) ──
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("AnalyzerTabs")
        content_layout.addWidget(self.tab_widget)

        # ──── TAB 0 : Image Preview ────
        image_tab = QWidget()
        image_tab_layout = QVBoxLayout(image_tab)
        image_tab_layout.setContentsMargins(4, 4, 4, 4)
        image_tab_layout.setSpacing(4)

        # graphics view for the image
        self.graphics_view = ZoomableGraphicsView()
        self.graphics_view.setObjectName("ImageView")
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_view.setAlignment(Qt.AlignCenter)
        image_tab_layout.addWidget(self.graphics_view, 1)

        # histogram canvas (below image)
        self.histogram_canvas = MplCanvas(figsize=(7, 2.2))
        self.histogram_canvas.setObjectName("HistogramCanvas")
        image_tab_layout.addWidget(self.histogram_canvas)

        self.tab_widget.addTab(image_tab, "🖼️  Image & Histogram")

        # ──── TAB 1 : Fourier Analysis ────
        fourier_tab = QWidget()
        fourier_tab_layout = QVBoxLayout(fourier_tab)
        fourier_tab_layout.setContentsMargins(6, 6, 6, 6)
        fourier_tab_layout.setSpacing(6)

        # --- top row: three plot canvases side-by-side ---
        plots_widget = QWidget()
        plots_layout = QHBoxLayout(plots_widget)
        plots_layout.setContentsMargins(0, 0, 0, 0)
        plots_layout.setSpacing(8)

        # 1) Magnitude Spectrum
        mag_frame = QFrame()
        mag_frame.setObjectName("FourierPlotFrame")
        mag_frame.setFrameShape(QFrame.StyledPanel)
        mag_frame.setFrameShadow(QFrame.Sunken)
        mag_layout = QVBoxLayout(mag_frame)
        mag_layout.setContentsMargins(4, 4, 4, 4)

        mag_title = QLabel("📐 Magnitude Spectrum")
        mag_title.setObjectName("FourierPlotTitle")
        mag_title.setAlignment(Qt.AlignCenter)
        mag_title.setFont(QFont("Tahoma", 9, QFont.Bold))
        mag_layout.addWidget(mag_title)

        self.mag_canvas = MplCanvas(figsize=(4.5, 3.5))
        mag_layout.addWidget(self.mag_canvas)
        plots_layout.addWidget(mag_frame, 1)

        # 2) Power Spectrum
        pow_frame = QFrame()
        pow_frame.setObjectName("FourierPlotFrame")
        pow_frame.setFrameShape(QFrame.StyledPanel)
        pow_frame.setFrameShadow(QFrame.Sunken)
        pow_layout = QVBoxLayout(pow_frame)
        pow_layout.setContentsMargins(4, 4, 4, 4)

        pow_title = QLabel("⚡ Power Spectrum")
        pow_title.setObjectName("FourierPlotTitle")
        pow_title.setAlignment(Qt.AlignCenter)
        pow_title.setFont(QFont("Tahoma", 9, QFont.Bold))
        pow_layout.addWidget(pow_title)

        self.pow_canvas = MplCanvas(figsize=(4.5, 3.5))
        pow_layout.addWidget(self.pow_canvas)
        plots_layout.addWidget(pow_frame, 1)

        # 3) Phase Spectrum
        phase_frame = QFrame()
        phase_frame.setObjectName("FourierPlotFrame")
        phase_frame.setFrameShape(QFrame.StyledPanel)
        phase_frame.setFrameShadow(QFrame.Sunken)
        phase_layout = QVBoxLayout(phase_frame)
        phase_layout.setContentsMargins(4, 4, 4, 4)

        phase_title = QLabel("🔄 Phase Spectrum")
        phase_title.setObjectName("FourierPlotTitle")
        phase_title.setAlignment(Qt.AlignCenter)
        phase_title.setFont(QFont("Tahoma", 9, QFont.Bold))
        phase_layout.addWidget(phase_title)

        self.phase_canvas = MplCanvas(figsize=(4.5, 3.5))
        phase_layout.addWidget(self.phase_canvas)
        plots_layout.addWidget(phase_frame, 1)

        fourier_tab_layout.addWidget(plots_widget, 3)

        # --- bottom row: 1-D radial-average magnitude plot (wide) ---
        radial_frame = QFrame()
        radial_frame.setObjectName("FourierPlotFrame")
        radial_frame.setFrameShape(QFrame.StyledPanel)
        radial_frame.setFrameShadow(QFrame.Sunken)
        radial_layout = QVBoxLayout(radial_frame)
        radial_layout.setContentsMargins(4, 4, 4, 4)

        radial_title = QLabel("📈 Radial-Average Magnitude  (Fourier Series – 1-D Profile)")
        radial_title.setObjectName("FourierPlotTitle")
        radial_title.setAlignment(Qt.AlignCenter)
        radial_title.setFont(QFont("Tahoma", 9, QFont.Bold))
        radial_layout.addWidget(radial_title)

        self.radial_canvas = MplCanvas(figsize=(12, 2.8))
        radial_layout.addWidget(self.radial_canvas)

        fourier_tab_layout.addWidget(radial_frame, 1)

        # --- info label ---
        self.fourier_info_label = QLabel("Load an image to see the Fourier Analysis.")
        self.fourier_info_label.setObjectName("FourierInfoLabel")
        self.fourier_info_label.setAlignment(Qt.AlignCenter)
        self.fourier_info_label.setFont(QFont("Tahoma", 9))
        fourier_tab_layout.addWidget(self.fourier_info_label)

        self.tab_widget.addTab(fourier_tab, "🌊  Fourier Analysis")

        # Add sidebar and content to splitter
        self.splitter.addWidget(sidebar_scroll)
        self.splitter.addWidget(content)
        
        # Set initial sizes: sidebar gets 400px, content gets the rest
        self.splitter.setSizes([400, 1200])
        
        # Add splitter to main layout
        main_layout.addWidget(self.splitter)

        # ──────────────────────────────────
        # Stylesheet
        # ──────────────────────────────────
        self.setStyleSheet(self._stylesheet())

    # ═══════════════════════════════════════════════════════
    # STYLESHEET
    # ═══════════════════════════════════════════════════════
    def _stylesheet(self):
        return """
        QMainWindow {
            background: #ECE9D8;
        }
        QWidget#Sidebar {
            background: #ECE9D8;
            border-right: 2px solid #9B9B7A;
        }
        QScrollArea#SidebarScroll {
            border: none;
            background: transparent;
        }
        QWidget#Content {
            background: #F7F6F3;
            border: 2px inset #9B9B7A;
        }
        QLabel#TaskTitle {
            color: #003D79;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #245EDC, stop:1 #0B278C
            );
            border: 2px outset #5A8FD9;
            border-radius: 4px;
            padding: 10px;
            font-weight: bold;
        }
        QGroupBox#LightGroup {
            font-weight: bold;
            color: #003D79;
            border: 2px outset #9B9B7A;
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 10px;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #F5F4F0, stop:1 #E0DED8
            );
        }
        QGroupBox#LightGroup::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 2px 6px;
            background: #E0DED8;
            border: 1px solid #9B9B7A;
            border-radius: 3px;
        }
        QPushButton#XpButton {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, stop:0.5 #E8E8E8, stop:1 #D0D0D0
            );
            border: 2px outset #9B9B7A;
            border-radius: 4px;
            padding: 8px;
            font-weight: bold;
            color: #000000;
            min-height: 32px;
        }
        QPushButton#XpButton:hover {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFF7D0, stop:1 #FFDE8A
            );
            border: 2px outset #FFB347;
        }
        QPushButton#XpButton:pressed {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #C0C0C0, stop:1 #E0E0E0
            );
            border: 2px inset #9B9B7A;
        }
        QPushButton#XpButton:disabled {
            background: #D4D0C8;
            color: #808080;
            border: 2px outset #9B9B7A;
        }
        QPushButton#XpButton:checked {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #A8D8FF, stop:1 #6CAEF5
            );
            border: 2px inset #5A8FD9;
            font-weight: bold;
        }
        QPushButton#SubButton {
            background: #F0F0E8;
            border: 1px solid #9B9B7A;
            border-radius: 3px;
            padding: 6px;
            color: #000000;
            text-align: left;
            min-height: 28px;
        }
        QPushButton#SubButton:hover {
            background: #FFF7D0;
            border: 1px solid #FFB347;
        }
        QPushButton#SubButton:pressed {
            background: #E0E0E0;
            border: 1px solid #9B9B7A;
        }
        QFrame#LightSubPanel {
            background: #FAFAF8;
            border: 1px solid #C0C0B0;
            border-radius: 3px;
            padding: 4px;
        }
        QFrame#LightStatusFrame {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #E8E6DC, stop:1 #D0CEC4
            );
            border: 1px solid #9B9B7A;
            border-radius: 3px;
        }
        QLabel#StatusLabel {
            color: #000000;
            padding-left: 4px;
        }
        QFrame#LightToolbar {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #F5F4F0, stop:1 #E0DED8
            );
            border: 2px outset #9B9B7A;
            border-radius: 4px;
        }
        QLabel#ToolbarTitle {
            color: #003D79;
            font-weight: bold;
        }
        QPushButton#ToolButton {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, stop:1 #D8D8D8
            );
            border: 2px outset #9B9B7A;
            border-radius: 3px;
            padding: 6px 12px;
            font-weight: bold;
            color: #000000;
        }
        QPushButton#ToolButton:hover {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFF7D0, stop:1 #FFDE8A
            );
        }
        QPushButton#ToolButton:pressed {
            background: #C0C0C0;
            border: 2px inset #9B9B7A;
        }
        QPushButton#ToolButton:disabled {
            background: #D4D0C8;
            color: #808080;
        }
        QGraphicsView#ImageView {
            background: #FFFFFF;
            border: 2px inset #9B9B7A;
        }
        QTabWidget#AnalyzerTabs::pane {
            border: 2px outset #9B9B7A;
            background: #F7F6F3;
        }
        QTabWidget#AnalyzerTabs::tab-bar {
            left: 5px;
        }
        QTabBar::tab {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #E8E6DC, stop:1 #C0C0B0
            );
            border: 2px outset #9B9B7A;
            border-bottom: none;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            color: #000000;
            font-weight: bold;
        }
        QTabBar::tab:selected {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, stop:1 #F0F0E8
            );
            border-bottom: 2px solid #F7F6F3;
        }
        QTabBar::tab:hover {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFF7D0, stop:1 #FFE8A0
            );
        }
        QFrame#FourierPlotFrame {
            background: #FAFAF8;
            border: 2px inset #9B9B7A;
        }
        QLabel#FourierPlotTitle {
            color: #003D79;
            padding: 4px;
        }
        QLabel#FourierInfoLabel {
            color: #666666;
            font-style: italic;
        }
        QTextEdit#StatsBox {
            background: #FFFFFF;
            border: 2px inset #9B9B7A;
            color: #000000;
            font-family: Consolas, Courier;
        }
        QDialog {
            background: #ECE9D8;
        }
        QLabel#DialogTitle {
            color: #003D79;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #D0E8FF, stop:1 #A0C8F0
            );
            border: 2px outset #5A8FD9;
            border-radius: 4px;
            padding: 8px;
        }
        QSplitter::handle {
            background: #9B9B7A;
            width: 6px;
        }
        QSplitter::handle:hover {
            background: #7A7A5A;
        }
        """

    # ═══════════════════════════════════════════════════════
    # BUTTON HELPERS
    # ═══════════════════════════════════════════════════════
    def create_xp_button(self, text, handler):
        btn = QPushButton(text)
        btn.setObjectName("XpButton")
        btn.setFont(QFont("Tahoma", 10))
        if handler:
            btn.clicked.connect(handler)
        return btn

    def create_sub_button(self, text, handler):
        btn = QPushButton(text)
        btn.setObjectName("SubButton")
        btn.setFont(QFont("Tahoma", 9))
        btn.clicked.connect(handler)
        return btn

    def create_tool_button(self, text, handler):
        btn = QPushButton(text)
        btn.setObjectName("ToolButton")
        btn.setFont(QFont("Tahoma", 9))
        btn.clicked.connect(handler)
        return btn

    # ═══════════════════════════════════════════════════════
    # FILE OPERATIONS
    # ═══════════════════════════════════════════════════════
    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp);;All Files (*)"
        )
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
            self.status_label.setText("❌ Failed to load image")
            return
        self.original_bgr = img.copy()
        self.working_bgr  = img.copy()
        self.enable_buttons(True)
        self.update_display()
        self.update_fourier()
        self.status_label.setText(f"✅ Loaded: {path.split('/')[-1]}  |  {img.shape[1]}×{img.shape[0]}")

    def save_image(self):
        if self.working_bgr is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;All Files (*)"
        )
        if path:
            cv2.imwrite(path, self.working_bgr)
            self.status_label.setText(f"💾 Saved: {path.split('/')[-1]}")

    def reset_image(self):
        if self.original_bgr is not None:
            self.working_bgr = self.original_bgr.copy()
            self.current_filter_code   = ""
            self.current_denoise_code  = ""
            self.current_freq_code     = ""
            self.update_display()
            self.update_fourier()
            self.status_label.setText("🔄 Image reset to original")

    def enable_buttons(self, state):
        for btn in [self.btn_save, self.btn_reset, self.btn_visualization,
                    self.btn_ops, self.btn_denoise, self.btn_noise,
                    self.btn_filters, self.btn_code, self.btn_fit, self.btn_reset_zoom]:
            btn.setEnabled(state)

    # ═══════════════════════════════════════════════════════
    # DISPLAY helpers
    # ═══════════════════════════════════════════════════════
    def bgr_to_qpixmap(self, bgr):
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        return QPixmap.fromImage(QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888).copy())

    def update_display(self):
        if self.working_bgr is None:
            return
        
        mode = self.visualization_mode
        if mode == "combined":
            display = self.working_bgr.copy()
        elif mode == "grayscale":
            gray = cv2.cvtColor(self.working_bgr, cv2.COLOR_BGR2GRAY)
            display = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif mode == "red":
            display = np.zeros_like(self.working_bgr)
            display[:, :, 2] = self.working_bgr[:, :, 2]
        elif mode == "green":
            display = np.zeros_like(self.working_bgr)
            display[:, :, 1] = self.working_bgr[:, :, 1]
        elif mode == "blue":
            display = np.zeros_like(self.working_bgr)
            display[:, :, 0] = self.working_bgr[:, :, 0]
        elif mode == "hsi":
            display = self.compute_hsi_visual()
        else:
            display = self.working_bgr.copy()

        pixmap = self.bgr_to_qpixmap(display)
        self.graphics_scene.clear()
        self.graphics_scene.addPixmap(pixmap)
        self.graphics_view.setSceneRect(self.graphics_scene.itemsBoundingRect())
        
        self.update_histogram()

    def update_histogram(self):
        if self.working_bgr is None:
            return
        
        self.histogram_canvas.ax.clear()
        
        colors = ('b', 'g', 'r')
        labels = ('Blue', 'Green', 'Red')
        
        for i, (col, label) in enumerate(zip(colors, labels)):
            hist = cv2.calcHist([self.working_bgr], [i], None, [256], [0, 256])
            self.histogram_canvas.ax.plot(hist, color=col, label=label, linewidth=1.5)
        
        self.histogram_canvas.ax.set_xlim([0, 256])
        self.histogram_canvas.ax.set_xlabel('Pixel Intensity', fontsize=9)
        self.histogram_canvas.ax.set_ylabel('Frequency', fontsize=9)
        self.histogram_canvas.ax.set_title('Color Histogram', fontsize=10, fontweight='bold')
        self.histogram_canvas.ax.legend(loc='upper right', fontsize=8)
        self.histogram_canvas.ax.grid(True, alpha=0.3)
        self.histogram_canvas.fig.tight_layout()
        self.histogram_canvas.draw()

    def compute_hsi_visual(self):
        rgb = cv2.cvtColor(self.working_bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        H, S, I = self.compute_hsi(rgb)
        
        # Normalize for display
        H_norm = (H / 360.0 * 255).astype(np.uint8)
        S_norm = (S * 255).astype(np.uint8)
        I_norm = (I * 255).astype(np.uint8)
        
        # Stack as BGR for display
        hsi_display = cv2.merge([H_norm, S_norm, I_norm])
        return hsi_display

    def compute_hsi(self, rgb):
        eps = 1e-8
        R, G, B = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
        
        I = (R + G + B) / 3.0
        
        min_rgb  = np.minimum(np.minimum(R, G), B)
        sum_rgb  = R + G + B
        S = 1.0 - (3.0 * min_rgb / (sum_rgb + eps))
        S = np.clip(S, 0.0, 1.0)
        
        num   = 0.5 * ((R - G) + (R - B))
        den   = np.sqrt((R-G)**2 + (R-B)*(G-B)) + eps
        theta = np.arccos(np.clip(num / den, -1.0, 1.0))
        H     = np.degrees(theta)
        H     = np.where(B > G, 360.0 - H, H)
        H     = np.mod(H, 360.0)
        
        return H, S, I

    # ═══════════════════════════════════════════════════════
    # FOURIER ANALYSIS
    # ═══════════════════════════════════════════════════════
    def update_fourier(self):
        if self.working_bgr is None:
            return
        
        gray = cv2.cvtColor(self.working_bgr, cv2.COLOR_BGR2GRAY)
        
        # Compute FFT
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        
        magnitude = np.abs(fshift)
        phase = np.angle(fshift)
        power = magnitude ** 2
        
        # Log scale for visualization
        magnitude_log = np.log(magnitude + 1)
        power_log = np.log(power + 1)
        
        # Update magnitude plot
        self.mag_canvas.ax.clear()
        im1 = self.mag_canvas.ax.imshow(magnitude_log, cmap='hot')
        self.mag_canvas.ax.set_title('Magnitude (log scale)', fontsize=9)
        self.mag_canvas.ax.axis('off')
        self.mag_canvas.fig.tight_layout()
        self.mag_canvas.draw()
        
        # Update power plot
        self.pow_canvas.ax.clear()
        im2 = self.pow_canvas.ax.imshow(power_log, cmap='viridis')
        self.pow_canvas.ax.set_title('Power (log scale)', fontsize=9)
        self.pow_canvas.ax.axis('off')
        self.pow_canvas.fig.tight_layout()
        self.pow_canvas.draw()
        
        # Update phase plot
        self.phase_canvas.ax.clear()
        im3 = self.phase_canvas.ax.imshow(phase, cmap='twilight')
        self.phase_canvas.ax.set_title('Phase', fontsize=9)
        self.phase_canvas.ax.axis('off')
        self.phase_canvas.fig.tight_layout()
        self.phase_canvas.draw()
        
        # Radial average
        radial_profile = self.compute_radial_average(magnitude_log)
        self.radial_canvas.ax.clear()
        self.radial_canvas.ax.plot(radial_profile, linewidth=2, color='#0B278C')
        self.radial_canvas.ax.set_xlabel('Frequency (pixels)', fontsize=9)
        self.radial_canvas.ax.set_ylabel('Magnitude (log)', fontsize=9)
        self.radial_canvas.ax.set_title('Radial Average of Magnitude Spectrum', fontsize=10)
        self.radial_canvas.ax.grid(True, alpha=0.3)
        self.radial_canvas.fig.tight_layout()
        self.radial_canvas.draw()
        
        self.fourier_info_label.setText(f"Fourier analysis updated | Image size: {gray.shape[1]}×{gray.shape[0]}")

    def compute_radial_average(self, data):
        y, x = np.indices(data.shape)
        center = np.array([(x.max()-x.min())/2.0, (y.max()-y.min())/2.0])
        r = np.hypot(x - center[0], y - center[1])
        
        r = r.astype(int)
        tbin = np.bincount(r.ravel(), data.ravel())
        nr = np.bincount(r.ravel())
        radialprofile = tbin / nr
        return radialprofile

    # ═══════════════════════════════════════════════════════
    # ZOOM CONTROLS
    # ═══════════════════════════════════════════════════════
    def fit_to_window(self):
        self.graphics_view.fitInView(self.graphics_scene.sceneRect(), Qt.KeepAspectRatio)

    def reset_zoom(self):
        self.graphics_view.resetTransform()

    # ═══════════════════════════════════════════════════════
    # VISUALIZATION MODE
    # ═══════════════════════════════════════════════════════
    def set_vis_mode(self, mode):
        self.visualization_mode = mode
        self.update_display()
        self.status_label.setText(f"📊 Visualization: {mode.upper()}")

    # ═══════════════════════════════════════════════════════
    # IMAGE OPERATIONS
    # ═══════════════════════════════════════════════════════
    def invert_image(self):
        if self.working_bgr is not None:
            self.working_bgr = cv2.bitwise_not(self.working_bgr)
            self.update_display()
            self.update_fourier()
            self.status_label.setText("🔁 Image inverted")

    def flip_horizontal(self):
        if self.working_bgr is not None:
            self.working_bgr = cv2.flip(self.working_bgr, 1)
            self.update_display()
            self.update_fourier()
            self.status_label.setText("↔️ Flipped horizontally")

    def flip_vertical(self):
        if self.working_bgr is not None:
            self.working_bgr = cv2.flip(self.working_bgr, 0)
            self.update_display()
            self.update_fourier()
            self.status_label.setText("↕️ Flipped vertically")

    def rotate_90(self):
        if self.working_bgr is not None:
            self.working_bgr = cv2.rotate(self.working_bgr, cv2.ROTATE_90_CLOCKWISE)
            self.update_display()
            self.update_fourier()
            self.status_label.setText("🔃 Rotated 90° clockwise")

    def equalize_histogram(self):
        if self.working_bgr is not None:
            ycrcb = cv2.cvtColor(self.working_bgr, cv2.COLOR_BGR2YCrCb)
            ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
            self.working_bgr = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
            self.update_display()
            self.update_fourier()
            self.status_label.setText("📊 Histogram equalized")

    # ═══════════════════════════════════════════════════════
    # NOISE FUNCTIONS
    # ═══════════════════════════════════════════════════════
    def apply_noise(self, noise_type, strength):
        if self.working_bgr is None:
            return
        
        img = self.working_bgr.astype(np.float32) / 255.0
        
        if noise_type == "pepper_&_salt":
            noise = np.random.rand(*img.shape[:2])
            img[noise < strength * 0.5] = 0
            img[noise > 1 - strength * 0.5] = 1
            code = f"# Pepper & Salt Noise\nnoise = np.random.rand(*img.shape[:2])\nimg[noise < {strength * 0.5}] = 0\nimg[noise > {1 - strength * 0.5}] = 1"
            
        elif noise_type == "gaussian":
            noise = np.random.normal(0, strength * 0.1, img.shape)
            img = img + noise
            code = f"# Gaussian Noise\nnoise = np.random.normal(0, {strength * 0.1}, img.shape)\nimg = img + noise"
            
        elif noise_type == "speckle":
            noise = np.random.randn(*img.shape)
            img = img + img * noise * strength * 0.3
            code = f"# Speckle Noise\nnoise = np.random.randn(*img.shape)\nimg = img + img * noise * {strength * 0.3}"
            
        elif noise_type == "poisson":
            vals = len(np.unique(img))
            vals = 2 ** np.ceil(np.log2(vals))
            img = np.random.poisson(img * vals * strength) / float(vals * strength)
            code = f"# Poisson Noise\nvals = 2 ** np.ceil(np.log2(len(np.unique(img))))\nimg = np.random.poisson(img * vals * {strength}) / float(vals * {strength})"
        else:
            code = "# Unknown noise type"
        
        img = np.clip(img, 0, 1)
        self.working_bgr = (img * 255).astype(np.uint8)
        self.current_filter_code = code
        self.update_display()
        self.update_fourier()
        self.status_label.setText(f"🎚️ Applied {noise_type.replace('_', ' ').title()} noise")

    # ═══════════════════════════════════════════════════════
    # DENOISE FUNCTIONS
    # ═══════════════════════════════════════════════════════
    def apply_denoise(self, method, strength):
        if self.working_bgr is None:
            return
        
        ksize = int(3 + strength * 10)
        if ksize % 2 == 0:
            ksize += 1
        
        if method == "bilateral":
            d = int(5 + strength * 10)
            sigma_color = int(50 + strength * 100)
            sigma_space = int(50 + strength * 100)
            self.working_bgr = cv2.bilateralFilter(self.working_bgr, d, sigma_color, sigma_space)
            code = f"# Bilateral Filter\nimg = cv2.bilateralFilter(img, {d}, {sigma_color}, {sigma_space})"
            
        elif method == "mean":
            self.working_bgr = cv2.blur(self.working_bgr, (ksize, ksize))
            code = f"# Mean Filter\nimg = cv2.blur(img, ({ksize}, {ksize}))"
            
        elif method == "median":
            self.working_bgr = cv2.medianBlur(self.working_bgr, ksize)
            code = f"# Median Filter\nimg = cv2.medianBlur(img, {ksize})"
            
        elif method == "non-local means":
            h = int(3 + strength * 20)
            self.working_bgr = cv2.fastNlMeansDenoisingColored(self.working_bgr, None, h, h, 7, 21)
            code = f"# Non-Local Means\nimg = cv2.fastNlMeansDenoisingColored(img, None, {h}, {h}, 7, 21)"
        else:
            code = "# Unknown denoise method"
        
        self.current_denoise_code = code
        self.update_display()
        self.update_fourier()
        self.status_label.setText(f"🧹 Applied {method.title()} denoising")

    # ═══════════════════════════════════════════════════════
    # FREQUENCY FILTERS
    # ═══════════════════════════════════════════════════════
    def apply_frequency_filter(self, filter_type, cutoff):
        if self.working_bgr is None:
            return
        
        gray = cv2.cvtColor(self.working_bgr, cv2.COLOR_BGR2GRAY)
        
        # FFT
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        
        rows, cols = gray.shape
        crow, ccol = rows // 2, cols // 2
        
        # Create filter mask
        mask = np.zeros((rows, cols), np.uint8)
        
        if filter_type == "low pass":
            cv2.circle(mask, (ccol, crow), cutoff, 1, -1)
            code = f"# Low Pass Filter\nmask = np.zeros((rows, cols), np.uint8)\ncv2.circle(mask, (ccol, crow), {cutoff}, 1, -1)"
            
        elif filter_type == "high pass":
            mask = np.ones((rows, cols), np.uint8)
            cv2.circle(mask, (ccol, crow), cutoff, 0, -1)
            code = f"# High Pass Filter\nmask = np.ones((rows, cols), np.uint8)\ncv2.circle(mask, (ccol, crow), {cutoff}, 0, -1)"
            
        elif filter_type == "notch pass":
            cv2.circle(mask, (ccol - cutoff, crow - cutoff), 20, 1, -1)
            cv2.circle(mask, (ccol + cutoff, crow + cutoff), 20, 1, -1)
            code = f"# Notch Pass Filter\ncv2.circle(mask, (ccol - {cutoff}, crow - {cutoff}), 20, 1, -1)\ncv2.circle(mask, (ccol + {cutoff}, crow + {cutoff}), 20, 1, -1)"
            
        elif filter_type == "notch reject":
            mask = np.ones((rows, cols), np.uint8)
            cv2.circle(mask, (ccol - cutoff, crow - cutoff), 20, 0, -1)
            cv2.circle(mask, (ccol + cutoff, crow + cutoff), 20, 0, -1)
            code = f"# Notch Reject Filter\nmask = np.ones((rows, cols), np.uint8)\ncv2.circle(mask, (ccol - {cutoff}, crow - {cutoff}), 20, 0, -1)\ncv2.circle(mask, (ccol + {cutoff}, crow + {cutoff}), 20, 0, -1)"
            
        elif filter_type == "gaussian":
            x = np.linspace(-cols//2, cols//2, cols)
            y = np.linspace(-rows//2, rows//2, rows)
            X, Y = np.meshgrid(x, y)
            mask = np.exp(-(X**2 + Y**2) / (2 * cutoff**2))
            code = f"# Gaussian Filter\nx = np.linspace(-cols//2, cols//2, cols)\ny = np.linspace(-rows//2, rows//2, rows)\nX, Y = np.meshgrid(x, y)\nmask = np.exp(-(X**2 + Y**2) / (2 * {cutoff}**2))"
        else:
            code = "# Unknown filter type"
        
        # Apply filter
        fshift = fshift * mask
        
        # Inverse FFT
        f_ishift = np.fft.ifftshift(fshift)
        img_back = np.fft.ifft2(f_ishift)
        img_back = np.abs(img_back)
        
        # Normalize
        img_back = np.uint8(255 * img_back / np.max(img_back))
        
        # Convert back to BGR
        self.working_bgr = cv2.cvtColor(img_back, cv2.COLOR_GRAY2BGR)
        self.current_freq_code = code
        self.update_display()
        self.update_fourier()
        self.status_label.setText(f"🎛️ Applied {filter_type.title()} filter")

    # ═══════════════════════════════════════════════════════
    # PANEL TOGGLES
    # ═══════════════════════════════════════════════════════
    def toggle_visualization_panel(self):
        self.visualization_panel.setVisible(self.btn_visualization.isChecked())

    def toggle_ops_panel(self):
        self.ops_panel.setVisible(self.btn_ops.isChecked())

    def toggle_denoise_panel(self):
        self.denoise_panel.setVisible(self.btn_denoise.isChecked())

    def toggle_noise_panel(self):
        self.noise_panel.setVisible(self.btn_noise.isChecked())

    def toggle_filters_panel(self):
        self.filters_panel.setVisible(self.btn_filters.isChecked())

    def toggle_code_panel(self):
        self.code_panel.setVisible(self.btn_code.isChecked())

    # ═══════════════════════════════════════════════════════
    # CODE VIEWER  show-code functions
    # ═══════════════════════════════════════════════════════
    def show_current_noise_code(self):
        code = self.current_filter_code if self.current_filter_code else "Apply noise first to see code!"
        CodeViewerDialog("Noise Filter", code, self).exec()

    def show_current_denoise_code(self):
        code = self.current_denoise_code if self.current_denoise_code else "Apply denoise first to see code!"
        CodeViewerDialog("Denoise Filter", code, self).exec()

    def show_current_filter_code(self):
        code = self.current_freq_code if self.current_freq_code else "Apply frequency filter first!"
        CodeViewerDialog("Frequency Filter", code, self).exec()

    def show_hsi_code(self):
        hsi_code = (
            "# HSI Color Space Conversion\n"
            "def compute_hsi(rgb):\n"
            "    eps = 1e-8\n"
            "    R, G, B = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]\n"
            "\n"
            "    I = (R + G + B) / 3.0\n"
            "\n"
            "    min_rgb  = np.minimum(np.minimum(R, G), B)\n"
            "    sum_rgb  = R + G + B\n"
            "    S = 1.0 - (3.0 * min_rgb / (sum_rgb + eps))\n"
            "    S = np.clip(S, 0.0, 1.0)\n"
            "\n"
            "    num   = 0.5 * ((R - G) + (R - B))\n"
            "    den   = np.sqrt((R-G)**2 + (R-B)*(G-B)) + eps\n"
            "    theta = np.arccos(np.clip(num / den, -1.0, 1.0))\n"
            "    H     = np.degrees(theta)\n"
            "    H     = np.where(B > G, 360.0 - H, H)\n"
            "    H     = np.mod(H, 360.0)\n"
            "\n"
            "    return H, S, I"
        )
        CodeViewerDialog("HSI Computation", hsi_code, self).exec()

    # ═══════════════════════════════════════════════════════
    # DIALOG launchers
    # ═══════════════════════════════════════════════════════
    def show_noise_dialog(self, noise_type):
        dialog = FilterParamsDialog(f"{noise_type} Noise", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_noise(
                noise_type.lower().replace(" & ", "_&_").replace(" ", "_"),
                dialog.get_params()["strength"].value()
            )

    def show_denoise_dialog(self, method_name):
        dialog = FilterParamsDialog(f"{method_name} Denoise", self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_denoise(method_name.lower(), dialog.get_params()["strength"].value())

    def show_filter_dialog(self, filter_name):
        dialog = FilterParamsDialog(filter_name, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            params = dialog.get_params()
            cutoff = params["cutoff"].value() if "cutoff" in params else 30
            self.apply_frequency_filter(filter_name.lower(), cutoff)


# ═══════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageAnalyzer()
    window.show()
    sys.exit(app.exec_())
