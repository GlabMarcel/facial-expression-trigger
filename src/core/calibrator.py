import numpy as np
from .expression_analyzer import (get_mouth_open_ratio, get_eyebrows_raised_ratio, get_smile_ratio)

class Calibrator:
    """Manages the calibration process for expression thresholds."""

    def __init__(self, frames_to_collect=60, threshold_factor=0.6):
        """
        Initializes the Calibrator.

        :param frames_to_collect: Number of frames to collect data for each phase.
        :param threshold_factor: Percentage between neutral and active mean to set threshold
                                  (e.g., 0.6 means 60% of the way from neutral to active).
        """
        self.frames_to_collect = frames_to_collect
        self.threshold_factor = threshold_factor

        self.state = "idle"
        self.data = {}
        self.frame_count = 0
        self.calculated_thresholds = {}
        self.current_instruction = ""
        self.error_message = ""
        self._reset_data()

    def _reset_data(self):
        """Resets collected data."""
        self.data = {
            "neutral": {"mouth_ratios": [], "eyebrow_ratios": [], "smile_ratios": []},
            "mouth": {"mouth_ratios": []},
            "eyebrows": {"eyebrow_ratios": []},
            "smile": {"smile_ratios": []}
        }
        self.frame_count = 0
        self.calculated_thresholds = {}
        self.error_message = ""


    def start(self):
        """Starts the calibration process."""
        print("Starting calibration...")
        self._reset_data()
        self.state = "neutral"
        self.frame_count = 0
        duration = self.frames_to_collect // 30
        self.current_instruction = f"Please look Neutral for {duration} sec..."
        return True

    def is_calibrating(self):
        """Returns True if calibration is currently active."""
        return self.state not in ["idle", "done", "error"]

    def get_current_instruction(self):
        """Returns the instruction text for the current calibration phase."""
        return self.current_instruction

    def get_calculated_thresholds(self):
        """Returns the calculated thresholds after successful calibration."""
        if self.state == "done":
            return self.calculated_thresholds
        return None

    def get_error_message(self):
        """Returns an error message if calibration failed."""
        return self.error_message

    def process_landmarks(self, face_landmarks):
        """Processes landmarks during an active calibration phase."""
        if not self.is_calibrating():
            return

        if face_landmarks is None:
             self.current_instruction = self.current_instruction.split(" (")[0] + " (No face detected!)"
             return

        current_mouth_ratio = get_mouth_open_ratio(face_landmarks)
        current_eyebrow_ratio = get_eyebrows_raised_ratio(face_landmarks)
        current_smile_ratio = get_smile_ratio(face_landmarks)

        if current_mouth_ratio is None or current_eyebrow_ratio is None or current_smile_ratio is None:
            print("Warning: Skipping frame during calibration due to missing ratio(s).")
            self.current_instruction = self.current_instruction.split(" (")[0] + " (Ratio Error!)"
            return

        duration = self.frames_to_collect // 30
        progress = f"({self.frame_count + 1}/{self.frames_to_collect})"

        if self.state == "neutral":
            self.data["neutral"]["mouth_ratios"].append(current_mouth_ratio)
            self.data["neutral"]["eyebrow_ratios"].append(current_eyebrow_ratio)
            self.data["neutral"]["smile_ratios"].append(current_smile_ratio)
            self.frame_count += 1
            self.current_instruction = f"Look Neutral {progress}"
            if self.frame_count >= self.frames_to_collect:
                self.state = "mouth"
                self.frame_count = 0
                self.current_instruction = f"Open Mouth Wide for {duration} sec..."
                print("Neutral phase complete. Starting Mouth phase.")

        elif self.state == "mouth":
            self.data["mouth"]["mouth_ratios"].append(current_mouth_ratio)
            self.frame_count += 1
            self.current_instruction = f"Open Mouth Wide {progress}"
            if self.frame_count >= self.frames_to_collect:
                self.state = "eyebrows"
                self.frame_count = 0
                self.current_instruction = f"Raise Eyebrows High for {duration} sec..."
                print("Mouth phase complete. Starting Eyebrows phase.")

        elif self.state == "eyebrows":
            self.data["eyebrows"]["eyebrow_ratios"].append(current_eyebrow_ratio)
            self.frame_count += 1
            self.current_instruction = f"Raise Eyebrows High {progress}"
            if self.frame_count >= self.frames_to_collect:
                self.state = "smile"
                self.frame_count = 0
                self.current_instruction = f"Smile Naturally for {duration} sec..."
                print("Eyebrows phase complete. Starting Smile phase.")

        elif self.state == "smile":
            self.data["smile"]["smile_ratios"].append(current_smile_ratio)
            self.frame_count += 1
            self.current_instruction = f"Smile Naturally {progress}"
            if self.frame_count >= self.frames_to_collect:
                self.state = "calculating"
                self.current_instruction = "Calculating thresholds..."
                print("Smile phase complete. Calculating...")
                self._calculate_thresholds()

    def _calculate_thresholds(self):
        """Calculates thresholds based on collected data."""
        try:
            neutral_mouth = np.mean(self.data["neutral"]["mouth_ratios"])
            active_mouth = np.mean(self.data["mouth"]["mouth_ratios"])
            if active_mouth <= neutral_mouth:
                 raise ValueError("Active mouth ratio not higher than neutral.")
            mouth_threshold = neutral_mouth + self.threshold_factor * (active_mouth - neutral_mouth)
            self.calculated_thresholds["mouth_open"] = round(mouth_threshold, 4)

            neutral_eyebrows = np.mean(self.data["neutral"]["eyebrow_ratios"])
            active_eyebrows = np.mean(self.data["eyebrows"]["eyebrow_ratios"])
            if active_eyebrows <= neutral_eyebrows:
                 raise ValueError("Active eyebrow ratio not higher than neutral.")
            eyebrow_threshold = neutral_eyebrows + self.threshold_factor * (active_eyebrows - neutral_eyebrows)
            self.calculated_thresholds["eyebrows_raised"] = round(eyebrow_threshold, 4)

            neutral_smile = np.mean(self.data["neutral"]["smile_ratios"])
            if len(self.data["smile"]["smile_ratios"]) < self.frames_to_collect // 2:
                 raise ValueError("Not enough data collected for smile.")
            active_smile = np.mean(self.data["smile"]["smile_ratios"])
            if active_smile <= neutral_smile: raise ValueError("Active smile ratio not higher than neutral.")
            smile_threshold = neutral_smile + self.threshold_factor * (active_smile - neutral_smile)
            self.calculated_thresholds["smile"] = round(smile_threshold, 4)

            self.state = "done"
            summary = ", ".join([f"{k.replace('_', ' ').title()}: {v}" for k,v in self.calculated_thresholds.items()])
            self.current_instruction = f"Calibration Complete! {summary}"
            print(f"Thresholds calculated: {self.calculated_thresholds}")

        except ValueError as ve:
            self.state = "error"
            self.error_message = f"Calculation Error: {ve}. Please ensure clear gestures during calibration."
            self.current_instruction = f"Error: {ve}"
            print(f"Calibration Error: {ve}")
        except Exception as e:
            self.state = "error"
            self.error_message = f"Unexpected calculation error: {e}"
            self.current_instruction = "Error during calculation."
            print(f"Unexpected Calibration Error: {e}")
