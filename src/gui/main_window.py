import sys
import cv2
import mediapipe as mp
import pyautogui
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QMessageBox, QDialog,
                             QSizePolicy, QFrame, QCheckBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap

from core.webcam_handler import WebcamHandler
from core.landmark_detector import LandmarkDetector
from . import drawing_utils
from core.expression_analyzer import get_mouth_open_ratio, get_eyebrows_raised_ratio, get_smile_ratio
from core.calibrator import Calibrator
from core.config_manager import ConfigManager
from .set_action_dialog import SetActionDialog

def convert_cv_qt(cv_img):
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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Facial Gesture Control")
        self.config_manager = ConfigManager()

        try:
            self.webcam = WebcamHandler(source=0)
        except SystemExit as e:
             QMessageBox.critical(self, "Error", f"Could not open webcam: {e}")
             sys.exit(1)

        self.detector = LandmarkDetector(max_faces=1)
        self.calibrator = Calibrator()

        config_thresholds = self.config_manager.get_thresholds()
        self.monitored_expressions = list(config_thresholds.keys())
        if not self.monitored_expressions:
            self.monitored_expressions = list(self.config_manager.DEFAULT_CONFIG.get("thresholds",{}).keys())
            print("Warning: No thresholds found in config, using default expression keys.")

        self._load_settings_from_manager()

        self.is_capturing = False
        self.prev_expression_states = {expr: False for expr in self.monitored_expressions}
        self.current_expression_states = {expr: False for expr in self.monitored_expressions}

        self.action_display_labels = {}
        self.edit_action_buttons = {}
        self.status_indicators = {}
        self.enabled_checkboxes = {}

        self._init_ui()
        self._update_action_displays()

        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.update_frame)

        self._print_initial_config()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        self.video_label = QLabel("Click 'Start' to begin")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("border: 1px solid #555; background-color: #333; color: white;")
        main_layout.addWidget(self.video_label, stretch=1)

        expression_frame = QFrame()
        expression_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.expressions_layout = QVBoxLayout(expression_frame)
        self.expressions_layout.setContentsMargins(5, 5, 5, 5)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>Enabled</b>"), stretch=1)
        header_layout.addWidget(QLabel("<b>Expression</b>"), stretch=2)
        header_layout.addWidget(QLabel("<b>Configured Action</b>"), stretch=3)
        header_layout.addWidget(QLabel("<b>Status</b>"), stretch=1)
        header_layout.addWidget(QLabel("<b>Edit</b>"), stretch=1)
        self.expressions_layout.addLayout(header_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.expressions_layout.addWidget(line)

        self._setup_expression_widgets()

        main_layout.addWidget(expression_frame)

        hbox_buttons = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.calibrate_button = QPushButton("Calibrate")
        self.stop_button.setEnabled(False)
        self.calibrate_button.setEnabled(False)

        hbox_buttons.addWidget(self.start_button)
        hbox_buttons.addWidget(self.stop_button)
        hbox_buttons.addWidget(self.calibrate_button)
        main_layout.addLayout(hbox_buttons)

        self.setLayout(main_layout)

        self.start_button.clicked.connect(self.start_capture)
        self.stop_button.clicked.connect(self.stop_capture)
        self.calibrate_button.clicked.connect(self.start_calibration)

    def _setup_expression_widgets(self):
        while self.expressions_layout.count() > 2:
            item = self.expressions_layout.takeAt(2)
            if item is not None:
                layout = item.layout()
                if layout is not None:
                    while layout.count() > 0:
                        widget_item = layout.takeAt(0)
                        if widget_item.widget():
                            widget_item.widget().deleteLater()
                    layout.deleteLater()
                elif item.widget():
                     item.widget().deleteLater()

        self.action_display_labels.clear()
        self.status_indicators.clear()
        self.edit_action_buttons.clear()
        self.enabled_checkboxes.clear()

        enabled_states = self.config_manager.get_enabled_gestures()

        for expr_key in self.monitored_expressions:
            row_layout = QHBoxLayout()

            enabled_checkbox = QCheckBox()
            is_enabled = enabled_states.get(expr_key, True)
            enabled_checkbox.setChecked(is_enabled)
            enabled_checkbox.stateChanged.connect(
                lambda state, key=expr_key: self._gesture_enabled_changed(key, state == Qt.CheckState.Checked.value)
            )
            self.enabled_checkboxes[expr_key] = enabled_checkbox

            expr_name_label = QLabel(expr_key.replace("_", " ").title())
            action_display_label = QLabel("N/A")
            self.action_display_labels[expr_key] = action_display_label
            status_indicator = QLabel("●")
            status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_indicator.setMinimumWidth(30)
            self.status_indicators[expr_key] = status_indicator
            self._update_indicator_style(expr_key, False, is_enabled)

            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(lambda checked=False, key=expr_key: self.open_set_action_dialog(key))
            edit_button.setEnabled(is_enabled)
            self.edit_action_buttons[expr_key] = edit_button

            row_layout.addWidget(enabled_checkbox, stretch=1)
            row_layout.addWidget(expr_name_label, stretch=2)
            row_layout.addWidget(action_display_label, stretch=3)
            row_layout.addWidget(status_indicator, stretch=1)
            row_layout.addWidget(edit_button, stretch=1)
            self.expressions_layout.addLayout(row_layout)

        self._update_action_displays()

    def _format_action_for_display(self, action_config):
        if action_config is None: return "None"
        action_type = action_config.get("type", "N/A"); action_value = action_config.get("value", "")
        if not action_value: return f"{action_type.title()}: -" if action_type != "N/A" else "None"
        if action_type == "press": return f"Press: {action_value}"
        elif action_type == "hotkey": keys = action_value.split(','); return f"Hotkey: {'+'.join(k.strip().title() for k in keys)}"
        elif action_type == "write": display_value = action_value if len(action_value) < 20 else action_value[:17] + "..."; return f"Type: '{display_value}'"
        else: return "Invalid/Unknown Action"

    def _update_action_displays(self):
        print("Updating action displays in UI...")
        actions_config = self.config_manager.get_actions();
        for expr_key, label in self.action_display_labels.items():
            action_config = actions_config.get(expr_key, None); display_text = self._format_action_for_display(action_config); label.setText(display_text)

    def _update_indicator_style(self, expression_key, is_active, is_enabled=True):
        if expression_key in self.status_indicators:
            label = self.status_indicators[expression_key]
            color = "#666666" if not is_enabled else ("#4CAF50" if is_active else "#AAAAAA")
            label.setStyleSheet(f"color: {color}; font-size: 18pt; font-weight: bold;")
            label.setEnabled(is_enabled)

    def _print_initial_config(self):
        print("--- Initial Configuration ---")
        print(f"Mouth Open Threshold: {self.MOUTH_OPEN_THRESHOLD}")
        print(f"Eyebrows Raised Threshold: {self.EYEBROWS_RAISED_THRESHOLD}")
        print(f"Smile Threshold: {self.SMILE_THRESHOLD}")
        actions_config = self.config_manager.get_actions()
        print(f"Mouth Action: {self._format_action_for_display(actions_config.get('mouth_open'))}")
        print(f"Eyebrows Action: {self._format_action_for_display(actions_config.get('eyebrows_raised'))}")
        print(f"Smile Action: {self._format_action_for_display(actions_config.get('smile'))}")
        print("---------------------------")

    def _load_settings_from_manager(self):
        print("Loading settings from ConfigManager...")
        self.MOUTH_OPEN_THRESHOLD = self.config_manager.get_threshold("mouth_open", 0.35)
        self.EYEBROWS_RAISED_THRESHOLD = self.config_manager.get_threshold("eyebrows_raised", 0.28)
        self.SMILE_THRESHOLD = self.config_manager.get_threshold("smile", 0.35)

    def _gesture_enabled_changed(self, expression_key, is_enabled):
        print(f"Gesture '{expression_key}' enabled state changed to: {is_enabled}")
        self.config_manager.update_gesture_enabled(expression_key, is_enabled)
        current_active_state = self.current_expression_states.get(expression_key, False)
        self._update_indicator_style(expression_key, current_active_state, is_enabled)
        if expression_key in self.edit_action_buttons:
             self.edit_action_buttons[expression_key].setEnabled(is_enabled)
        if not is_enabled:
            self.current_expression_states[expression_key] = False
            self.prev_expression_states[expression_key] = False

    def start_capture(self):
        if not self.is_capturing:
            self._load_settings_from_manager()
            enabled_states = self.config_manager.get_enabled_gestures()
            for key, btn in self.edit_action_buttons.items():
                btn.setEnabled(enabled_states.get(key, True))
            for key, chk in self.enabled_checkboxes.items():
                chk.setEnabled(True)

            self.is_capturing = True
            self.timer.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.calibrate_button.setEnabled(True)
            print("Detection started.")

    def stop_capture(self):
        if self.is_capturing:
            if self.calibrator.is_calibrating():
                 print("Stopping calibration due to capture stop.")
                 self.calibrator.state = "idle"
                 self.calibrate_button.setEnabled(True)

            self.is_capturing = False
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.calibrate_button.setEnabled(False)
            for btn in self.edit_action_buttons.values(): btn.setEnabled(False)
            for chk in self.enabled_checkboxes.values(): chk.setEnabled(False)
            self.video_label.setText("Stopped. Click Start to begin.")
            for key in self.monitored_expressions: self._update_indicator_style(key, False, False)
            print("Detection stopped.")

    def start_calibration(self):
        if not self.is_capturing:
            QMessageBox.warning(self, "Calibration", "Please start capture before calibrating.")
            return
        if self.calibrator.is_calibrating():
            return

        enabled_gestures_for_cal = [
            key for key in self.monitored_expressions
            if self.config_manager.get_enabled_gestures().get(key, True)
        ]
        if not enabled_gestures_for_cal:
             QMessageBox.warning(self, "Calibration", "No gestures are enabled for calibration.\nPlease enable at least one gesture using the checkbox.")
             return

        if self.calibrator.start():
            print("Starting calibration process...")
            self.calibrate_button.setEnabled(False)
            for chk in self.enabled_checkboxes.values(): chk.setEnabled(False)
            for btn in self.edit_action_buttons.values(): btn.setEnabled(False)
        else:
             QMessageBox.warning(self, "Calibration", "Failed to start calibration.")

    def open_set_action_dialog(self, expression_key):
        current_action = self.config_manager.get_action(expression_key)
        dialog = SetActionDialog(expression_key, current_action, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_action = dialog.get_selected_action()
            if new_action != current_action:
                print(f"Updating action for '{expression_key}'...")
                if self.config_manager.update_action(expression_key, new_action):
                    self._update_action_displays()
                    QMessageBox.information(self, "Configuration", f"Action for '{expression_key}' updated.")
                else:
                    QMessageBox.warning(self, "Config Error", f"Failed to save updated action for '{expression_key}'.")
            else:
                 print("Action configuration not changed.")
        else:
            print(f"Setting action for '{expression_key}' cancelled.")

    def update_frame(self):
        if not self.is_capturing: return

        for key in self.monitored_expressions: self.current_expression_states[key] = False

        success, frame = self.webcam.read_frame()
        if not success or frame is None: self.video_label.setText("Status: Error reading frame!"); return

        processing_frame = frame.copy(); frame_rgb = cv2.cvtColor(processing_frame, cv2.COLOR_BGR2RGB); frame_rgb.flags.writeable = False
        results = self.detector.detect_landmarks(frame_rgb); annotated_frame = processing_frame
        face_landmarks = results.multi_face_landmarks[0] if results.multi_face_landmarks else None

        enabled_status = self.config_manager.get_enabled_gestures()

        if self.calibrator.is_calibrating():
            self.calibrator.process_landmarks(face_landmarks)
            instruction = self.calibrator.get_current_instruction()
            if face_landmarks:
                 annotated_frame = drawing_utils.draw_landmarks_on_image(processing_frame, results)
                 cv2.putText(annotated_frame, f"CALIBRATING: {instruction}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
            else:
                 cv2.putText(annotated_frame, f"CALIBRATING: {instruction}\n(Please look at camera)", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)

            for key in self.monitored_expressions: self._update_indicator_style(key, False, enabled_status.get(key, True))

            if self.calibrator.state == "done" or self.calibrator.state == "error":
                 for key, chk in self.enabled_checkboxes.items(): chk.setEnabled(True)
                 for key, btn in self.edit_action_buttons.items(): btn.setEnabled(enabled_status.get(key, True))
                 self.calibrate_button.setEnabled(True)

                 if self.calibrator.state == "done":
                      new_thresholds = self.calibrator.get_calculated_thresholds()
                      if new_thresholds:
                          print("Calibration finished, updating and saving config...")
                          if self.config_manager.update_thresholds(new_thresholds):
                              self._load_settings_from_manager()
                              QMessageBox.information(self, "Calibration", f"Calibration Complete!\nNew thresholds saved:\n{new_thresholds}")
                          else:
                              QMessageBox.warning(self, "Calibration Error", "Failed to save calibrated thresholds.")
                      else:
                          QMessageBox.warning(self, "Calibration", "Calibration finished, but failed to retrieve thresholds.")
                 else:
                      error_msg = self.calibrator.get_error_message()
                      QMessageBox.critical(self, "Calibration Error", f"Calibration failed:\n{error_msg}")

                 self.calibrator.state = "idle"

        else: # Not calibrating
            if face_landmarks:
                mouth_ratio = get_mouth_open_ratio(face_landmarks) if enabled_status.get("mouth_open", True) else None
                eyebrow_ratio = get_eyebrows_raised_ratio(face_landmarks) if enabled_status.get("eyebrows_raised", True) else None
                smile_ratio = get_smile_ratio(face_landmarks) if enabled_status.get("smile", True) else None

                if enabled_status.get("mouth_open", True) and mouth_ratio is not None:
                    self.current_expression_states["mouth_open"] = mouth_ratio > self.MOUTH_OPEN_THRESHOLD
                if enabled_status.get("eyebrows_raised", True) and eyebrow_ratio is not None:
                    self.current_expression_states["eyebrows_raised"] = eyebrow_ratio > self.EYEBROWS_RAISED_THRESHOLD
                if enabled_status.get("smile", True) and smile_ratio is not None:
                    self.current_expression_states["smile"] = smile_ratio > self.SMILE_THRESHOLD

                annotated_frame = drawing_utils.draw_landmarks_on_image(processing_frame, results)
                self._handle_triggers(enabled_status)

                for key in self.monitored_expressions:
                    is_enabled = enabled_status.get(key, True)
                    current_state = self.current_expression_states.get(key, False) if is_enabled else False
                    self._update_indicator_style(key, current_state, is_enabled)

            else: # No face detected
                 for key in self.monitored_expressions:
                      is_enabled = enabled_status.get(key, True)
                      self._update_indicator_style(key, False, is_enabled)

        qt_pixmap = convert_cv_qt(annotated_frame)
        if qt_pixmap:
            self.video_label.setPixmap(qt_pixmap)
        else:
            self.video_label.setText("Error displaying frame")

    def _handle_triggers(self, enabled_status):
        actions_config = self.config_manager.get_actions()

        for expr_key in self.monitored_expressions:
            if not enabled_status.get(expr_key, True):
                self.prev_expression_states[expr_key] = False
                continue

            current_state = self.current_expression_states.get(expr_key, False)
            prev_state = self.prev_expression_states.get(expr_key, False)
            action_config = actions_config.get(expr_key, None)

            if current_state and not prev_state and action_config:
                 action_type = action_config.get("type")
                 action_value = action_config.get("value")
                 if not action_type or action_value is None:
                      print(f"Warning: Incomplete action config for {expr_key}: {action_config}")
                      continue

                 print(f"****** Triggered: {expr_key} (Action: {action_config}) ******")
                 try:
                     if action_type == "press":
                         pyautogui.press(action_value)
                     elif action_type == "hotkey":
                         keys = [k.strip() for k in action_value.split(',') if k.strip()]
                         if keys:
                            pyautogui.hotkey(*keys)
                         else:
                             print(f"Warning: Invalid keys found for hotkey action {expr_key}: {action_value}")
                     elif action_type == "write":
                         pyautogui.typewrite(action_value, interval=0.01)
                     else:
                         print(f"Warning: Unknown action type '{action_type}' for {expr_key}.")

                 except Exception as e:
                     print(f"Error executing pyautogui action {action_config} for {expr_key}: {e}")

        self.prev_expression_states = self.current_expression_states.copy()

    def closeEvent(self, event):
        print("Closing application...")
        self.stop_capture()
        if hasattr(self, 'webcam') and self.webcam:
            self.webcam.release()
        if hasattr(self, 'detector') and self.detector:
            self.detector.close()
        print("Resources released.")
        event.accept()