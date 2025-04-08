# src/core/calibrator.py
import numpy as np
import time
from .expression_analyzer import (get_mouth_open_ratio, get_eyebrows_raised_ratio, get_smile_ratio)

class Calibrator:
    GESTURES_WITH_ACTIVE_PHASE = {"mouth_open", "eyebrows_raised", "smile"}
    ACTIVE_PHASE_ORDER = ["mouth", "eyebrows", "smile"]
    PHASE_TO_KEY_MAP = {"mouth": "mouth_open", "eyebrows": "eyebrows_raised", "smile": "smile"}

    def __init__(self, frames_to_collect=60, threshold_factor=0.6):
        self.frames_to_collect = frames_to_collect
        self.threshold_factor = threshold_factor
        self.state = "idle"
        self.frame_count = 0
        self.calculated_thresholds = {}
        self.current_instruction = ""
        self.error_message = ""
        self.data = {}
        self._reset_data()
        self.enabled_keys_in_run = set()
        self.active_phases_in_run = []
        self.current_phase_index = -1

    def _reset_data(self):
        self.data = {
            "neutral": {"mouth_ratios": [], "eyebrow_ratios": [], "smile_ratios": []},
            "mouth": {"mouth_ratios": []},
            "eyebrows": {"eyebrow_ratios": []},
            "smile": {"smile_ratios": []}
        }
        self.frame_count = 0
        self.calculated_thresholds = {}
        self.error_message = ""
        self.enabled_keys_in_run = set()
        self.active_phases_in_run = []
        self.current_phase_index = -1

    def start(self, enabled_gestures_keys):
        print(f"Starting calibration for: {enabled_gestures_keys}")
        self._reset_data()
        self.enabled_keys_in_run = set(enabled_gestures_keys)
        self.active_phases_in_run = [ p for p in self.ACTIVE_PHASE_ORDER if self.PHASE_TO_KEY_MAP.get(p) in self.enabled_keys_in_run ]
        print(f"Active calibration phases: {self.active_phases_in_run}")
        self.state = "neutral"
        self.frame_count = 0
        self.current_phase_index = -1
        duration = self.frames_to_collect // 30
        self.current_instruction = f"Look Neutral (Gathering base data for {duration} sec...)"
        return True

    def is_calibrating(self):
        return self.state not in ["idle", "done", "error"]

    def get_current_instruction(self):
        return self.current_instruction

    def get_calculated_thresholds(self):
        return self.calculated_thresholds if self.state == "done" else None

    def get_error_message(self):
        return self.error_message

    def process_landmarks(self, face_landmarks):
        if not self.is_calibrating(): return
        if face_landmarks is None:
             base_instruction = self.current_instruction.split(" (")[0]
             self.current_instruction = f"{base_instruction} (No face detected!)"
             return

        current_mouth_ratio = get_mouth_open_ratio(face_landmarks)
        current_eyebrow_ratio = get_eyebrows_raised_ratio(face_landmarks)
        current_smile_ratio = get_smile_ratio(face_landmarks)

        print(f"DEBUG - Ratios Calculated -> Mouth: {current_mouth_ratio}, Brows: {current_eyebrow_ratio}, Smile: {current_smile_ratio}")

        if any(v is None for v in [current_mouth_ratio, current_eyebrow_ratio, current_smile_ratio]):
            print("Warning: Skipping frame during calibration due to missing ratio.")
            base_instruction = self.current_instruction.split(" (")[0]
            self.current_instruction = f"{base_instruction} (Ratio Error!)"
            return

        duration = self.frames_to_collect // 30
        progress = f"({self.frame_count + 1}/{self.frames_to_collect})"

        print(f"DEBUG - Entering state check with self.state = '{self.state}'")

        if self.state == "neutral":
            self.data["neutral"]["mouth_ratios"].append(current_mouth_ratio)
            self.data["neutral"]["eyebrow_ratios"].append(current_eyebrow_ratio)
            self.data["neutral"]["smile_ratios"].append(current_smile_ratio)
            self.frame_count += 1
            self.current_instruction = f"Look Neutral {progress}"
            if self.frame_count >= self.frames_to_collect:
                print("Neutral phase complete.")
                self.current_phase_index = 0
                if self.current_phase_index < len(self.active_phases_in_run):
                    next_phase = self.active_phases_in_run[self.current_phase_index]
                    self.state = next_phase
                    self.frame_count = 0
                    phase_display_name = next_phase.replace('_', ' ').title()
                    if next_phase == "mouth": phase_display_name = "Open Mouth Wide"
                    elif next_phase == "eyebrows": phase_display_name = "Raise Eyebrows High"
                    elif next_phase == "smile": phase_display_name = "Smile Naturally"
                    self.current_instruction = f"{phase_display_name} for {duration} sec..."
                    print(f"Starting {next_phase} phase.")
                else:
                    self.state = "calculating"
                    self.current_instruction = "Calculating thresholds..."
                    print("No active phases required. Calculating...")
                    self._calculate_thresholds()

        elif self.state == "mouth":
            self.data["mouth"]["mouth_ratios"].append(current_mouth_ratio)
            self.frame_count += 1
            self.current_instruction = f"Open Mouth Wide {progress}"
            if self.frame_count >= self.frames_to_collect:
                 print(f"{self.state.title()} phase complete.")
                 self.current_phase_index += 1
                 if self.current_phase_index < len(self.active_phases_in_run):
                     next_phase = self.active_phases_in_run[self.current_phase_index]
                     self.state = next_phase
                     self.frame_count = 0
                     next_phase_display_name = next_phase.replace('_', ' ').title()
                     if next_phase == "mouth": next_phase_display_name = "Open Mouth Wide"
                     elif next_phase == "eyebrows": next_phase_display_name = "Raise Eyebrows High"
                     elif next_phase == "smile": next_phase_display_name = "Smile Naturally"
                     self.current_instruction = f"{next_phase_display_name} for {duration} sec..."
                     print(f"Starting {next_phase} phase.")
                 else:
                     self.state = "calculating"
                     self.current_instruction = "Calculating thresholds..."
                     print("All active phases complete. Calculating...")
                     self._calculate_thresholds()

        elif self.state == "eyebrows":
             self.data["eyebrows"]["eyebrow_ratios"].append(current_eyebrow_ratio)
             self.frame_count += 1
             progress = f"({self.frame_count}/{self.frames_to_collect})"
             self.current_instruction = f"Raise Eyebrows High {progress}"
             print(f"DEBUG [Eyebrows Phase]: Frame Count = {self.frame_count}, Target = {self.frames_to_collect}")
             if self.frame_count >= self.frames_to_collect:
                 print(f"DEBUG: Eyebrows phase complete check passed.")
                 print(f"DEBUG: Old Phase Index: {self.current_phase_index}")
                 self.current_phase_index += 1
                 print(f"DEBUG: New Phase Index: {self.current_phase_index}, Active Phases Length: {len(self.active_phases_in_run)}")
                 if self.current_phase_index < len(self.active_phases_in_run):
                     next_phase = self.active_phases_in_run[self.current_phase_index]
                     print(f"DEBUG: Next phase determined: {next_phase}")
                     self.state = next_phase
                     self.frame_count = 0
                     next_phase_display_name = next_phase.replace('_', ' ').title()
                     if next_phase == "mouth": next_phase_display_name = "Open Mouth Wide"
                     elif next_phase == "eyebrows": next_phase_display_name = "Raise Eyebrows High"
                     elif next_phase == "smile": next_phase_display_name = "Smile Naturally"
                     self.current_instruction = f"{next_phase_display_name} for {duration} sec..."
                     print(f"DEBUG: State changed to '{self.state}'. Starting next phase.")
                 else:
                     print("DEBUG: Last active phase (eyebrows) complete. Changing state to calculating.")
                     self.state = "calculating"
                     self.current_instruction = "Calculating thresholds..."
                     self._calculate_thresholds()
             print(f"DEBUG [End of Eyebrows Logic]: State is now {self.state}, Frame Count is {self.frame_count}")

        elif self.state == "smile":
             self.data["smile"]["smile_ratios"].append(current_smile_ratio)
             self.frame_count += 1
             self.current_instruction = f"Smile Naturally {progress}"
             if self.frame_count >= self.frames_to_collect:
                 print(f"{self.state.title()} phase complete.")
                 self.current_phase_index += 1
                 if self.current_phase_index < len(self.active_phases_in_run):
                     next_phase = self.active_phases_in_run[self.current_phase_index]
                     self.state = next_phase; self.frame_count = 0
                     print(f"Starting {next_phase} phase.")
                 else:
                     self.state = "calculating"; self.current_instruction = "Calculating thresholds..."
                     print("All active phases complete. Calculating...")
                     self._calculate_thresholds()

    def _calculate_thresholds(self):
        new_thresholds = {}
        try:
            min_samples = max(1, self.frames_to_collect // 4)
            neutral_data = self.data["neutral"]

            if len(neutral_data.get("mouth_ratios", [])) < min_samples or \
               len(neutral_data.get("eyebrow_ratios", [])) < min_samples or \
               len(neutral_data.get("smile_ratios", [])) < min_samples:
                 raise ValueError("Not enough data collected during neutral phase.")

            gestures_calculated = set()
            for key in self.enabled_keys_in_run:
                if key == "mouth_open" and "mouth" in self.active_phases_in_run:
                    active_ratios = self.data["mouth"].get("mouth_ratios", [])
                    if len(active_ratios) < min_samples: raise ValueError(f"Not enough data collected for {key}.")
                    neutral_val = np.mean(neutral_data["mouth_ratios"]); active_val = np.mean(active_ratios)
                    if active_val <= neutral_val: raise ValueError(f"Active ratio not higher than neutral for {key}.")
                    threshold = neutral_val + self.threshold_factor * (active_val - neutral_val); new_thresholds[key] = round(threshold, 4)
                    gestures_calculated.add(key)
                elif key == "eyebrows_raised" and "eyebrows" in self.active_phases_in_run:
                    active_ratios = self.data["eyebrows"].get("eyebrow_ratios", [])
                    if len(active_ratios) < min_samples: raise ValueError(f"Not enough data collected for {key}.")
                    neutral_val = np.mean(neutral_data["eyebrow_ratios"]); active_val = np.mean(active_ratios)
                    if active_val <= neutral_val: raise ValueError(f"Active ratio not higher than neutral for {key}.")
                    threshold = neutral_val + self.threshold_factor * (active_val - neutral_val); new_thresholds[key] = round(threshold, 4)
                    gestures_calculated.add(key)
                elif key == "smile" and "smile" in self.active_phases_in_run:
                    active_ratios = self.data["smile"].get("smile_ratios", [])
                    if len(active_ratios) < min_samples: raise ValueError(f"Not enough data collected for {key}.")
                    neutral_val = np.mean(neutral_data["smile_ratios"]); active_val = np.mean(active_ratios)
                    if active_val <= neutral_val: raise ValueError(f"Active ratio not higher than neutral for {key}.")
                    threshold = neutral_val + self.threshold_factor * (active_val - neutral_val); new_thresholds[key] = round(threshold, 4)
                    gestures_calculated.add(key)

            # Check if any enabled gesture requiring an active phase was actually calculated
            enabled_active_gestures = {k for k,v in self.PHASE_TO_KEY_MAP.items() if v in self.enabled_keys_in_run}
            if not new_thresholds and enabled_active_gestures:
                 raise ValueError("No thresholds could be calculated for enabled active gestures.")

            self.calculated_thresholds = new_thresholds
            self.state = "done"
            summary = ", ".join([f"{k.replace('_',' ').title()}: {v}" for k,v in self.calculated_thresholds.items()]) if new_thresholds else "No thresholds calculated (check enabled gestures)."
            self.current_instruction = f"Calibration Complete! {summary}"
            print(f"Thresholds calculated: {self.calculated_thresholds}")

        except ValueError as ve:
            self.state = "error"; self.error_message = f"Calc Error: {ve}."; self.current_instruction = f"Error: {ve}"; self.calculated_thresholds = {}; print(f"Calibration Error: {ve}")
        except Exception as e:
            self.state = "error"; self.error_message = f"Unexpected calc error: {e}"; self.current_instruction = "Error during calculation."; self.calculated_thresholds = {}; print(f"Unexpected Calibration Error: {e}")