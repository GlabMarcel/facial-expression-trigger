import cv2
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QMessageBox,
                             QSizePolicy, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

def convert_cv_qt(cv_img):
    if cv_img is None: return None
    try:
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        scaled_img = convert_to_Qt_format.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return QPixmap.fromImage(scaled_img)
    except Exception as e:
        print(f"Error converting image for Qt: {e}")
        return None

class MainWindow(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    calibrate_requested = pyqtSignal()
    edit_action_requested = pyqtSignal(str)
    gesture_enabled_changed = pyqtSignal(str, bool)
    window_closed = pyqtSignal()

    def __init__(self, monitored_expressions):
        super().__init__()
        self.setWindowTitle("Facial Gesture Control")
        self.monitored_expressions = monitored_expressions
        self.action_display_labels = {}
        self.edit_action_buttons = {}
        self.status_indicators = {}
        self.enabled_checkboxes = {}
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.video_label = QLabel("Click 'Start' to begin")
        self.video_label.setObjectName("VideoLabel")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.video_label.setMinimumSize(640, 480); self.video_label.setStyleSheet("border: 1px solid #555; background-color: #333; color: white;")
        main_layout.addWidget(self.video_label, stretch=1)
        expression_frame = QFrame(); expression_frame.setFrameShape(QFrame.Shape.StyledPanel); self.expressions_layout = QVBoxLayout(expression_frame); self.expressions_layout.setContentsMargins(5, 5, 5, 5)
        header_layout = QHBoxLayout(); header_layout.addWidget(QLabel("<b>Enabled</b>"), stretch=1); header_layout.addWidget(QLabel("<b>Expression</b>"), stretch=2); header_layout.addWidget(QLabel("<b>Configured Action</b>"), stretch=3); header_layout.addWidget(QLabel("<b>Status</b>"), stretch=1); header_layout.addWidget(QLabel("<b>Edit</b>"), stretch=1); self.expressions_layout.addLayout(header_layout)
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken); self.expressions_layout.addWidget(line)
        self._setup_expression_widgets()
        main_layout.addWidget(expression_frame)
        hbox_buttons = QHBoxLayout(); self.start_button = QPushButton("Start"); self.stop_button = QPushButton("Stop"); self.calibrate_button = QPushButton("Calibrate"); self.stop_button.setEnabled(False); self.calibrate_button.setEnabled(False)
        hbox_buttons.addWidget(self.start_button); hbox_buttons.addWidget(self.stop_button); hbox_buttons.addWidget(self.calibrate_button); main_layout.addLayout(hbox_buttons)
        self.setLayout(main_layout)
        self.start_button.clicked.connect(self.start_requested.emit)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.calibrate_button.clicked.connect(self.calibrate_requested.emit)

    def _setup_expression_widgets(self):
        while self.expressions_layout.count() > 2: item = self.expressions_layout.takeAt(2); layout = item.layout();
        self.action_display_labels.clear(); self.status_indicators.clear(); self.edit_action_buttons.clear(); self.enabled_checkboxes.clear()
        for expr_key in self.monitored_expressions:
            row_layout = QHBoxLayout(); enabled_checkbox = QCheckBox(); enabled_checkbox.setEnabled(False); enabled_checkbox.stateChanged.connect(lambda state, key=expr_key: self.gesture_enabled_changed.emit(key, state == Qt.CheckState.Checked.value)); self.enabled_checkboxes[expr_key] = enabled_checkbox
            expr_name_label = QLabel(expr_key.replace("_", " ").title()); action_display_label = QLabel("N/A"); self.action_display_labels[expr_key] = action_display_label
            status_indicator = QLabel("●"); status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter); status_indicator.setMinimumWidth(30); self.status_indicators[expr_key] = status_indicator; self._update_indicator_style(expr_key, False, False)
            edit_button = QPushButton("Edit"); edit_button.setEnabled(False); edit_button.clicked.connect(lambda checked=False, key=expr_key: self.edit_action_requested.emit(key)); self.edit_action_buttons[expr_key] = edit_button
            row_layout.addWidget(enabled_checkbox, stretch=1); row_layout.addWidget(expr_name_label, stretch=2); row_layout.addWidget(action_display_label, stretch=3); row_layout.addWidget(status_indicator, stretch=1); row_layout.addWidget(edit_button, stretch=1)
            self.expressions_layout.addLayout(row_layout)

    def _format_action_for_display(self, action_config):
        if action_config is None:
            return "None"

        action_type = action_config.get("type", "N/A")
        action_value = action_config.get("value", "")

        if not action_value:
            return f"{action_type.title()}: -" if action_type != "N/A" else "None"

        if action_type == "press":
            return f"Press: {action_value}"
        elif action_type == "hotkey":
            keys = action_value.split(',')

            return f"Hotkey: {'+'.join(k.strip().title() for k in keys if k.strip())}"
        elif action_type == "write":
            display_value = action_value if len(action_value) < 20 else action_value[:17] + "..."
            return f"Type: '{display_value}'"
        else:

            return f"Invalid Type ({action_type}): {action_value}"

    def update_video_display(self, cv_frame):
        if cv_frame is None: self.video_label.setText("No Frame / Error"); return
        qt_pixmap = convert_cv_qt(cv_frame)
        if qt_pixmap: self.video_label.setPixmap(qt_pixmap)
        else: self.video_label.setText("Error displaying frame")

    def update_action_displays(self, actions_config):
        print("View: Updating action displays...")
        for expr_key, label in self.action_display_labels.items():
            action_config = actions_config.get(expr_key, None); display_text = self._format_action_for_display(action_config); label.setText(display_text)

    def _update_indicator_style(self, expression_key, is_active, is_enabled):
        if expression_key in self.status_indicators: label = self.status_indicators[expression_key]; color = "#666666" if not is_enabled else ("#4CAF50" if is_active else "#AAAAAA"); label.setStyleSheet(f"color: {color}; font-size: 18pt; font-weight: bold;"); label.setEnabled(is_enabled)

    def update_expression_status(self, expression_states, enabled_states):
        for key in self.monitored_expressions: is_active = expression_states.get(key, False); is_enabled = enabled_states.get(key, True); self._update_indicator_style(key, is_active, is_enabled)

    def set_capture_controls_state(self, is_capturing, enabled_gestures):
        self.start_button.setEnabled(not is_capturing); self.stop_button.setEnabled(is_capturing); self.calibrate_button.setEnabled(is_capturing)
        for key in self.monitored_expressions:
            gesture_is_enabled_in_config = enabled_gestures.get(key, True)
            if key in self.enabled_checkboxes: self.enabled_checkboxes[key].setEnabled(is_capturing); self.enabled_checkboxes[key].setChecked(gesture_is_enabled_in_config)
            if key in self.edit_action_buttons: self.edit_action_buttons[key].setEnabled(is_capturing and gesture_is_enabled_in_config)

    def set_calibration_controls_state(self, is_calibrating):
        self.calibrate_button.setEnabled(not is_calibrating); self.start_button.setEnabled(not is_calibrating); self.stop_button.setEnabled(not is_calibrating)
        for chk in self.enabled_checkboxes.values(): chk.setEnabled(not is_calibrating)
        for btn in self.edit_action_buttons.values(): btn.setEnabled(not is_calibrating)

    def show_calibration_instruction(self, text):
        print(f"View Instruction Received: {text}")

    def show_message(self, title, text, type='info'):
        if type == 'info': QMessageBox.information(self, title, text)
        elif type == 'warning': QMessageBox.warning(self, title, text)
        elif type == 'critical': QMessageBox.critical(self, title, text)

    def closeEvent(self, event):
        print("View: Close event detected, emitting signal.")
        self.window_closed.emit()
        event.accept()