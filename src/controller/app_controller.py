import sys
import cv2
import pyautogui
import mediapipe as mp
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QDialog, QMessageBox

from core.config_manager import ConfigManager
from core.webcam_handler import WebcamHandler
from core.calibrator import Calibrator
from core.expression_analyzer import get_mouth_open_ratio, get_eyebrows_raised_ratio, get_smile_ratio

from gui.main_window import MainWindow
from gui.set_action_dialog import SetActionDialog
from gui import drawing_utils
import os

class AppController(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        print("Initializing Controller (Single Process)...")

        script_dir = os.path.dirname(os.path.realpath(__file__))
        config_file_path = os.path.abspath(os.path.join(script_dir, "..", "..", "config.json"))
        self.config_manager = ConfigManager(config_file_path=config_file_path)

        self.calibrator = Calibrator()
        self.webcam = None
        self.detector = None
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self._load_settings()

        self.monitored_expressions = list(self.config_manager.get_thresholds().keys())
        if not self.monitored_expressions:
            self.monitored_expressions = list(self.config_manager.DEFAULT_CONFIG.get("thresholds",{}).keys())
            print("Warning: No thresholds found in config, using default expression keys.")

        self.is_capturing = False
        self.current_expression_states = {expr: False for expr in self.monitored_expressions}
        self.active_frame_counts = {expr: 0 for expr in self.monitored_expressions}

        self.view = MainWindow(self.monitored_expressions)
        self._update_view_action_displays()

        self.timer = QTimer()
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._process_frame)

        self._connect_signals()
        self._print_initial_config()

    def _load_settings(self):
        print("Controller: Loading settings...")
        self.thresholds = self.config_manager.get_thresholds()
        self.enabled_gestures = self.config_manager.get_enabled_gestures()
        self.hold_frames = self.config_manager.get_setting("hold_frames", 5)

    def _update_view_action_displays(self):
        actions = self.config_manager.get_actions()
        if hasattr(self.view, 'update_action_combos'):
             self.view.update_action_combos(actions)
        elif hasattr(self.view, 'update_action_displays'):
             self.view.update_action_displays(actions)


    def _print_initial_config(self):
        print("--- Initial Configuration (Controller) ---")
        actions = self.config_manager.get_actions()
        print(f"Hold Frames Required: {self.hold_frames}")
        for key in self.monitored_expressions:
             print(f"{key.replace('_',' ').title()} Threshold: {self.thresholds.get(key)}")
             action_display = self.view._format_action_for_display(actions.get(key))
             print(f"{key.replace('_',' ').title()} Action: {action_display}")
             print(f"{key.replace('_',' ').title()} Enabled: {self.enabled_gestures.get(key, True)}")
        print("-----------------------------------------")

    def _connect_signals(self):
        print("Connecting View signals to Controller slots...")
        self.view.start_requested.connect(self.start_capture)
        self.view.stop_requested.connect(self.stop_capture)
        self.view.calibrate_requested.connect(self.start_calibration)
        if hasattr(self.view, 'action_config_changed'): 
            self.view.action_config_changed.connect(self._handle_action_change)
        elif hasattr(self.view, 'edit_action_requested'):
             self.view.edit_action_requested.connect(self.open_set_action_dialog)
        self.view.gesture_enabled_changed.connect(self._handle_enabled_change)
        self.view.window_closed.connect(self.cleanup)

    def show_view(self):
        self.view.show()

    def start_capture(self):
        print("Controller: Start Capture Requested")
        if not self.is_capturing:
            try:
                if self.webcam is None:
                    print("Initializing WebcamHandler...")
                    self.webcam = WebcamHandler(source=0)
                if self.detector is None:
                    print("Importing and Initializing LandmarkDetector...")
                    from core.landmark_detector import LandmarkDetector
                    self.detector = LandmarkDetector(max_faces=1)
            except SystemExit as e:
                 self.view.show_message("Error", f"Could not open webcam: {e}", type='critical'); return
            except ImportError as e_imp:
                 self.view.show_message("Error", f"Failed to import detection component: {e_imp}", type='critical'); return
            except Exception as e:
                 self.view.show_message("Error", f"Failed to initialize components: {e}", type='critical'); self.webcam = None; self.detector = None; return

            self._load_settings()
            self.active_frame_counts = {expr: 0 for expr in self.monitored_expressions}
            self.is_capturing = True
            self.timer.start()
            self.enabled_gestures = self.config_manager.get_enabled_gestures()
            self.view.set_capture_controls_state(True, self.enabled_gestures)
            print("Detection started by Controller.")

    def stop_capture(self):
        print("Controller: Stop Capture Received")
        if self.is_capturing:
            if self.calibrator.is_calibrating():
                 print("Controller: Stopping calibration due to capture stop.")
                 self.calibrator.state = "idle"
                 self.view.set_calibration_controls_state(False)

            self.is_capturing = False
            self.timer.stop()
            enabled_gestures = self.config_manager.get_enabled_gestures()
            self.view.set_capture_controls_state(False, enabled_gestures)
            self.active_frame_counts = {expr: 0 for expr in self.monitored_expressions}
            print("Detection stopped by Controller.")

    def start_calibration(self):
        print("Controller: Calibration Requested")
        if not self.is_capturing or not self.webcam or not self.detector:
             self.view.show_message("Calibration", "Please start capture before calibrating.", type='warning'); return
        if self.calibrator.is_calibrating(): return

        enabled_gestures_keys = [ k for k, v in self.config_manager.get_enabled_gestures().items() if v and k in self.monitored_expressions ]
        if not enabled_gestures_keys:
             self.view.show_message("Calibration", "No gestures enabled for calibration...", type='warning'); return

        if self.calibrator.start(enabled_gestures_keys):
            print("Controller: Starting calibration process...")
            self.view.set_calibration_controls_state(True)
        else:
             self.view.show_message("Calibration", "Failed to start calibration.", type='warning')

    def _handle_action_change(self, expression_key, new_action_config):
         print(f"Controller: Action change received for '{expression_key}': {new_action_config}")
         current_action = self.config_manager.get_action(expression_key)
         if new_action_config != current_action:
             if self.config_manager.update_action(expression_key, new_action_config):
                 if hasattr(self.view, 'update_action_displays'): self._update_view_action_displays()
                 elif hasattr(self.view, 'update_action_combos'): self.view.update_action_combos(self.config_manager.get_actions())

                 print(f"Action for '{expression_key}' updated and saved.")
             else:
                 self.view.show_message("Config Error", f"Failed to save action for {expression_key}.", 'warning')
         else:
             print("Controller: Action configuration not changed.")

    def open_set_action_dialog(self, expression_key):
        print(f"Controller: Edit Action Requested for {expression_key} (using dialog)")
        current_action = self.config_manager.get_action(expression_key)
        dialog = SetActionDialog(expression_key, current_action, self.view)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_action = dialog.get_selected_action()
            if new_action != current_action:
                print(f"Controller: Updating action for '{expression_key}'...")
                if self.config_manager.update_action(expression_key, new_action):
                    if hasattr(self.view, 'update_action_displays'): self._update_view_action_displays()
                    elif hasattr(self.view, 'update_action_combos'): self.view.update_action_combos(self.config_manager.get_actions())
                    self.view.show_message("Configuration", f"Action for '{expression_key}' updated.", type='info')
                else:
                    self.view.show_message("Config Error", f"Failed to save updated action for '{expression_key}'.", type='warning')
            else: print("Controller: Action configuration not changed.")
        else: print(f"Controller: Setting action for '{expression_key}' cancelled.")

    def _handle_enabled_change(self, expression_key, is_enabled):
        print(f"Controller: Enabled state change received for '{expression_key}': {is_enabled}")
        if self.config_manager.update_gesture_enabled(expression_key, is_enabled):
             self.enabled_gestures = self.config_manager.get_enabled_gestures()
             # Update UI state for edit button/combo box if needed
             if hasattr(self.view, 'edit_action_buttons') and expression_key in self.view.edit_action_buttons:
                  self.view.edit_action_buttons[expression_key].setEnabled(is_enabled and self.is_capturing)
             elif hasattr(self.view, 'action_combos') and expression_key in self.view.action_combos:
                  self.view.action_combos[expression_key].setEnabled(is_enabled and self.is_capturing)

             if not is_enabled:
                 if expression_key in self.active_frame_counts: self.active_frame_counts[expression_key] = 0
                 if expression_key in self.current_expression_states: self.current_expression_states[expression_key] = False
             self.view.update_expression_status(self.current_expression_states, self.enabled_gestures)
        else:
             self.view.show_message("Config Error", f"Failed to save enabled state for '{expression_key}'.", type='warning')

    def _process_frame(self):
        if not self.is_capturing or not self.webcam or not self.detector: return

        success, frame = self.webcam.read_frame()
        if not success or frame is None: self.view.update_video_display(None); return

        processing_frame = frame.copy()
        frame_rgb = cv2.cvtColor(processing_frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.detector.detect_landmarks(frame_rgb)
        annotated_frame = processing_frame
        face_landmarks = results.multi_face_landmarks[0] if results.multi_face_landmarks else None

        current_enabled_status = self.config_manager.get_enabled_gestures()

        if self.calibrator.is_calibrating():
            self.calibrator.process_landmarks(face_landmarks)
            instruction = self.calibrator.get_current_instruction()
            if face_landmarks:
                 annotated_frame = drawing_utils.draw_landmarks_on_image(processing_frame, results, self.mp_drawing, self.mp_face_mesh, self.mp_drawing_styles)
                 cv2.putText(annotated_frame, f"CALIBRATING: {instruction}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
            else:
                 cv2.putText(annotated_frame, f"CALIBRATING: {instruction}\n(Look at camera)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)

            self.view.update_expression_status({}, current_enabled_status)

            if self.calibrator.state == "done" or self.calibrator.state == "error":
                 self.view.set_calibration_controls_state(False)
                 if self.calibrator.state == "done":
                     new_thresholds = self.calibrator.get_calculated_thresholds()
                     if new_thresholds:
                         print("Controller: Calibration finished, saving config...")
                         if self.config_manager.update_thresholds(new_thresholds):
                             self._load_settings()
                             self.view.show_message("Calibration", f"Calibration Complete!\nNew thresholds saved:\n{new_thresholds}", type='info')
                         else: self.view.show_message("Calibration Error", "Failed to save calibrated thresholds.", type='warning')
                     else: self.view.show_message("Calibration", "Calibration finished, but failed to retrieve thresholds.", type='warning')
                 else:
                     error_msg = self.calibrator.get_error_message(); self.view.show_message("Calibration Error", f"Calibration failed:\n{error_msg}", type='critical')
                 self.calibrator.state = "idle"

        else:
            for key in self.monitored_expressions: self.current_expression_states[key] = False
            if face_landmarks:
                mouth_ratio = get_mouth_open_ratio(face_landmarks) if current_enabled_status.get("mouth_open", True) else None
                eyebrow_ratio = get_eyebrows_raised_ratio(face_landmarks) if current_enabled_status.get("eyebrows_raised", True) else None
                smile_ratio = get_smile_ratio(face_landmarks) if current_enabled_status.get("smile", True) else None

                if current_enabled_status.get("mouth_open", True) and mouth_ratio is not None: self.current_expression_states["mouth_open"] = mouth_ratio > self.thresholds.get("mouth_open", 0.35)
                if current_enabled_status.get("eyebrows_raised", True) and eyebrow_ratio is not None: self.current_expression_states["eyebrows_raised"] = eyebrow_ratio > self.thresholds.get("eyebrows_raised", 0.28)
                if current_enabled_status.get("smile", True) and smile_ratio is not None: self.current_expression_states["smile"] = smile_ratio > self.thresholds.get("smile", 0.35)

                annotated_frame = drawing_utils.draw_landmarks_on_image(processing_frame, results, self.mp_drawing, self.mp_face_mesh, self.mp_drawing_styles)
                self._handle_triggers()

            self.view.update_expression_status(self.current_expression_states, current_enabled_status)

        self.view.update_video_display(annotated_frame)


    def _handle_triggers(self):
        actions_config = self.config_manager.get_actions()
        enabled_status = self.config_manager.get_enabled_gestures()
        hold_frames_required = self.hold_frames

        for expr_key in self.monitored_expressions:
            current_state = self.current_expression_states.get(expr_key, False)

            if current_state and enabled_status.get(expr_key, True):
                self.active_frame_counts[expr_key] = self.active_frame_counts.get(expr_key, 0) + 1
            else:
                self.active_frame_counts[expr_key] = 0

            if self.active_frame_counts.get(expr_key, 0) == hold_frames_required:
                action_config = actions_config.get(expr_key, None)
                if action_config:
                    action_type = action_config.get("type"); action_value = action_config.get("value")
                    if not action_type or action_value is None: print(f"Warn: Incomplete action {expr_key}"); continue
                    print(f"****** Triggered ({hold_frames_required} frames): {expr_key} (Action: {action_config}) ******")
                    try:
                        if action_type == "press": pyautogui.press(action_value)
                        elif action_type == "hotkey": keys = [k.strip() for k in action_value.split(',') if k.strip()]; pyautogui.hotkey(*keys)
                        elif action_type == "write": pyautogui.typewrite(action_value, interval=0.01)
                        else: print(f"Warn: Unknown action type '{action_type}' for {expr_key}.")
                    except Exception as e: print(f"Error pyautogui action {action_config} for {expr_key}: {e}")

    def cleanup(self):
        print("Controller: Cleaning up resources...")
        if self.is_capturing: self.stop_capture()
        if hasattr(self, 'webcam') and self.webcam: self.webcam.release()
        if hasattr(self, 'detector') and self.detector: self.detector.close()
        print("Controller: Resources released.")
        self.app.quit()