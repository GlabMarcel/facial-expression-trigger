import numpy as np
import time
from .expression_analyzer import (get_mouth_open_ratio, get_eyebrows_raised_ratio,
                                  get_smile_ratio, get_left_ear, get_right_ear)

class Calibrator:
    WINK_THRESHOLD_FACTOR = 0.5

    GESTURES_WITH_ACTIVE_PHASE = {"mouth_open", "eyebrows_raised", "smile"}

    ACTIVE_PHASE_ORDER = ["mouth", "eyebrows", "smile"]
    PHASE_TO_KEY_MAP = {
        "mouth": "mouth_open",
        "eyebrows": "eyebrows_raised",
        "smile": "smile"
    }


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
            "neutral": {"mouth_ratios": [], "eyebrow_ratios": [], "smile_ratios": [], "left_ears": [], "right_ears": []},
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

        self.active_phases_in_run = [
            phase for phase in self.ACTIVE_PHASE_ORDER
            if self.PHASE_TO_KEY_MAP.get(phase) in self.enabled_keys_in_run
        ]
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
        if self.state == "done":
            return self.calculated_thresholds
        return None

    def get_error_message(self):
        return self.error_message

    def process_landmarks(self, face_landmarks):
        if not self.is_calibrating(): return
        if face_landmarks is None:
            self.current_instruction = self.current_instruction.split(" (")[0] + " (No face detected!)"
            return

        current_mouth_ratio = get_mouth_open_ratio(face_landmarks)
        current_eyebrow_ratio = get_eyebrows_raised_ratio(face_landmarks)
        current_smile_ratio = get_smile_ratio(face_landmarks)
        current_left_ear = get_left_ear(face_landmarks)
        current_right_ear = get_right_ear(face_landmarks)

        if any(v is None for v in [current_mouth_ratio, current_eyebrow_ratio, current_smile_ratio, current_left_ear, current_right_ear]):
            print("Warning: Skipping frame during calibration due to missing ratio/EAR.")
            self.current_instruction = self.current_instruction.split(" (")[0] + " (Ratio Error!)"
            return

        duration = self.frames_to_collect // 30
        progress = f"({self.frame_count + 1}/{self.frames_to_collect})"


        if self.state == "neutral":

            self.data["neutral"]["mouth_ratios"].append(current_mouth_ratio)
            self.data["neutral"]["eyebrow_ratios"].append(current_eyebrow_ratio)
            self.data["neutral"]["smile_ratios"].append(current_smile_ratio)
            self.data["neutral"]["left_ears"].append(current_left_ear)
            self.data["neutral"]["right_ears"].append(current_right_ear)
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

        elif self.state in self.PHASE_TO_KEY_MAP:
            current_phase_key = self.PHASE_TO_KEY_MAP[self.state]
            ratio_key = f"{self.state}_ratios"
            if ratio_key in self.data[self.state]:

                ratio_to_collect = None
                if self.state == "mouth": ratio_to_collect = current_mouth_ratio
                elif self.state == "eyebrows": ratio_to_collect = current_eyebrow_ratio
                elif self.state == "smile": ratio_to_collect = current_smile_ratio

                if ratio_to_collect is not None:
                    self.data[self.state][ratio_key].append(ratio_to_collect)
                    self.frame_count += 1

                    phase_display_name = self.state.replace('_', ' ').title()
                    if self.state == "mouth": phase_display_name = "Open Mouth Wide"
                    elif self.state == "eyebrows": phase_display_name = "Raise Eyebrows High"
                    elif self.state == "smile": phase_display_name = "Smile Naturally"
                    self.current_instruction = f"{phase_display_name} {progress}"

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

    def _calculate_thresholds(self):
        new_thresholds = {}
        try:
            min_samples = max(1, self.frames_to_collect // 4)
            neutral_data = self.data["neutral"]


            if len(neutral_data.get("mouth_ratios", [])) < min_samples or \
               len(neutral_data.get("eyebrow_ratios", [])) < min_samples or \
               len(neutral_data.get("smile_ratios", [])) < min_samples or \
               len(neutral_data.get("left_ears", [])) < min_samples or \
               len(neutral_data.get("right_ears", [])) < min_samples:
                raise ValueError("Not enough data collected during neutral phase.")


            for key in self.enabled_keys_in_run:
                if key == "mouth_open":
                    active_ratios = self.data["mouth"].get("mouth_ratios", [])
                    if len(active_ratios) < min_samples: raise ValueError("Not enough data collected for mouth open.")
                    neutral_val = np.mean(neutral_data["mouth_ratios"])
                    active_val = np.mean(active_ratios)
                    if active_val <= neutral_val: raise ValueError("Active mouth ratio not higher than neutral.")
                    threshold = neutral_val + self.threshold_factor * (active_val - neutral_val)
                    new_thresholds[key] = round(threshold, 4)

                elif key == "eyebrows_raised":
                    active_ratios = self.data["eyebrows"].get("eyebrow_ratios", [])
                    if len(active_ratios) < min_samples: raise ValueError("Not enough data collected for eyebrows raised.")
                    neutral_val = np.mean(neutral_data["eyebrow_ratios"])
                    active_val = np.mean(active_ratios)
                    if active_val <= neutral_val: raise ValueError("Active eyebrow ratio not higher than neutral.")
                    threshold = neutral_val + self.threshold_factor * (active_val - neutral_val)
                    new_thresholds[key] = round(threshold, 4)

                elif key == "smile":
                    active_ratios = self.data["smile"].get("smile_ratios", [])
                    if len(active_ratios) < min_samples: raise ValueError("Not enough data collected for smile.")
                    neutral_val = np.mean(neutral_data["smile_ratios"])
                    active_val = np.mean(active_ratios)
                    if active_val <= neutral_val: raise ValueError("Active smile ratio not higher than neutral.")
                    threshold = neutral_val + self.threshold_factor * (active_val - neutral_val)
                    new_thresholds[key] = round(threshold, 4)

                elif key == "left_wink" or key == "right_wink":

                    avg_neutral_left_ear = np.mean(neutral_data["left_ears"])
                    avg_neutral_right_ear = np.mean(neutral_data["right_ears"])
                    if avg_neutral_left_ear < 0.1 or avg_neutral_right_ear < 0.1:
                        print(f"Warning: Neutral EAR too low, skipping wink threshold calculation for {key}.")
                        continue
                    if key == "left_wink":
                        threshold = avg_neutral_left_ear * self.WINK_THRESHOLD_FACTOR
                        new_thresholds[key] = round(threshold, 4)
                    elif key == "right_wink":
                        threshold = avg_neutral_right_ear * self.WINK_THRESHOLD_FACTOR
                        new_thresholds[key] = round(threshold, 4)

            if not new_thresholds:
                raise ValueError("No thresholds could be calculated for enabled gestures.")

            self.calculated_thresholds = new_thresholds
            self.state = "done"; summary = ", ".join([f"{k.replace('_',' ').title()}: {v}" for k,v in self.calculated_thresholds.items()]); self.current_instruction = f"Calibration Complete! {summary}"; print(f"Thresholds calculated: {self.calculated_thresholds}")

        except ValueError as ve: self.state = "error"; self.error_message = f"Calc Error: {ve}."; self.current_instruction = f"Error: {ve}"; self.calculated_thresholds = {}; print(f"Calibration Error: {ve}")
        except Exception as e: self.state = "error"; self.error_message = f"Unexpected calc error: {e}"; self.current_instruction = "Error during calculation."; self.calculated_thresholds = {}; print(f"Unexpected Calibration Error: {e}")