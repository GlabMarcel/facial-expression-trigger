import pytest
import numpy as np
from src.core.calibrator import Calibrator
from src.core import calibrator as calibrator_module

import src.core.expression_analyzer as expression_analyzer


class MockLandmark:
    def __init__(self, x=0.0, y=0.0, z=0.0): self.x = x; self.y = y; self.z = z

class MockFaceLandmarks:
    def __init__(self, num_landmarks=478): self.landmark = {i: MockLandmark() for i in range(num_landmarks)}
    def set_landmark(self, index, x, y, z=0.0):
        if index in self.landmark: self.landmark[index].x = x; self.landmark[index].y = y; self.landmark[index].z = z


DEFAULT_ENABLED_KEYS = ["mouth_open", "eyebrows_raised", "smile", "left_wink", "right_wink"]



def test_calibrator_initialization():
    calibrator = Calibrator(frames_to_collect=50, threshold_factor=0.7)
    assert calibrator.state == "idle"
    assert calibrator.frames_to_collect == 50
    assert calibrator.threshold_factor == 0.7
    assert not calibrator.is_calibrating()
    assert calibrator.get_calculated_thresholds() is None
    assert "neutral" in calibrator.data and "mouth_ratios" in calibrator.data["neutral"]
    assert calibrator.frame_count == 0
    assert calibrator.enabled_keys_in_run == set()
    assert calibrator.active_phases_in_run == []

def test_calibrator_start():
    calibrator = Calibrator(frames_to_collect=60)

    calibrator.state = "done"; calibrator.frame_count = 10; calibrator.calculated_thresholds = {"test": 1}
    calibrator.data["neutral"]["mouth_ratios"].append(0.1)
    calibrator.enabled_keys_in_run = {"previous_run"}
    calibrator.active_phases_in_run = ["mouth"]


    start_success = calibrator.start(DEFAULT_ENABLED_KEYS)


    assert start_success == True
    assert calibrator.state == "neutral"
    assert calibrator.is_calibrating() == True
    assert calibrator.frame_count == 0
    assert calibrator.calculated_thresholds == {}
    assert calibrator.data["neutral"]["mouth_ratios"] == []
    assert calibrator.enabled_keys_in_run == set(DEFAULT_ENABLED_KEYS)
    assert calibrator.active_phases_in_run == ["mouth", "eyebrows", "smile"]
    assert "Look Neutral" in calibrator.get_current_instruction()

def test_calibration_neutral_phase_collects_data_and_transitions(mocker):
    frames = 3
    calibrator_instance = Calibrator(frames_to_collect=frames)
    mock_landmarks = MockFaceLandmarks()
    mock_landmarks.set_landmark(33, 0.8, 0.4); mock_landmarks.set_landmark(263, 0.2, 0.4)


    mock_mouth = mocker.patch.object(calibrator_module, 'get_mouth_open_ratio', return_value=0.1)
    mock_brows = mocker.patch.object(calibrator_module, 'get_eyebrows_raised_ratio', return_value=0.2)
    mock_smile = mocker.patch.object(calibrator_module, 'get_smile_ratio', return_value=0.5)
    mock_l_ear = mocker.patch.object(calibrator_module, 'get_left_ear', return_value=0.35)
    mock_r_ear = mocker.patch.object(calibrator_module, 'get_right_ear', return_value=0.36)


    calibrator_instance.start(DEFAULT_ENABLED_KEYS)
    for _ in range(frames):
        assert calibrator_instance.state == "neutral"
        calibrator_instance.process_landmarks(mock_landmarks)


    assert calibrator_instance.state == "mouth"
    assert calibrator_instance.frame_count == 0
    assert "Open Mouth Wide" in calibrator_instance.get_current_instruction()
    assert len(calibrator_instance.data["neutral"]["mouth_ratios"]) == frames
    assert calibrator_instance.data["neutral"]["mouth_ratios"] == [0.1] * frames
    assert len(calibrator_instance.data["neutral"]["eyebrow_ratios"]) == frames
    assert calibrator_instance.data["neutral"]["eyebrow_ratios"] == [0.2] * frames
    assert len(calibrator_instance.data["neutral"]["smile_ratios"]) == frames
    assert calibrator_instance.data["neutral"]["smile_ratios"] == [0.5] * frames
    assert len(calibrator_instance.data["neutral"]["left_ears"]) == frames
    assert calibrator_instance.data["neutral"]["left_ears"] == [0.35] * frames
    assert len(calibrator_instance.data["neutral"]["right_ears"]) == frames
    assert calibrator_instance.data["neutral"]["right_ears"] == [0.36] * frames
    assert mock_mouth.call_count == frames
    assert mock_brows.call_count == frames
    assert mock_smile.call_count == frames
    assert mock_l_ear.call_count == frames
    assert mock_r_ear.call_count == frames

def test_calculate_thresholds_success(mocker):
    frames = 10
    calibrator = Calibrator(frames_to_collect=frames, threshold_factor=0.6)

    calibrator.data["neutral"]["mouth_ratios"] = [0.1] * frames
    calibrator.data["neutral"]["eyebrow_ratios"] = [0.2] * frames
    calibrator.data["neutral"]["smile_ratios"] = [0.5] * frames
    calibrator.data["neutral"]["left_ears"] = [0.35] * frames
    calibrator.data["neutral"]["right_ears"] = [0.36] * frames
    calibrator.data["mouth"]["mouth_ratios"] = [0.7] * frames
    calibrator.data["eyebrows"]["eyebrow_ratios"] = [0.4] * frames
    calibrator.data["smile"]["smile_ratios"] = [0.8] * frames

    calibrator.enabled_keys_in_run = {"mouth_open", "eyebrows_raised", "smile", "left_wink", "right_wink"}


    calibrator._calculate_thresholds()


    assert calibrator.state == "done"
    assert calibrator.error_message == ""

    expected_thresholds = {
        "mouth_open": round(0.1 + 0.6 * (0.7 - 0.1), 4),
        "eyebrows_raised": round(0.2 + 0.6 * (0.4 - 0.2), 4),
        "smile": round(0.5 + 0.6 * (0.8 - 0.5), 4),
        "left_wink": round(0.35 * Calibrator.WINK_THRESHOLD_FACTOR, 4),
        "right_wink": round(0.36 * Calibrator.WINK_THRESHOLD_FACTOR, 4)
    }

    assert calibrator.calculated_thresholds == pytest.approx(expected_thresholds)
    assert "Complete" in calibrator.current_instruction

def test_calculate_thresholds_error_active_not_higher(mocker):
    frames = 10
    min_samples = max(1, frames // 4)
    calibrator = Calibrator(frames_to_collect=frames, threshold_factor=0.6)
    calibrator.data["neutral"]["mouth_ratios"] = [0.1] * frames
    calibrator.data["neutral"]["eyebrow_ratios"] = [0.2] * frames
    calibrator.data["neutral"]["smile_ratios"] = [0.5] * frames
    calibrator.data["neutral"]["left_ears"] = [0.35] * frames
    calibrator.data["neutral"]["right_ears"] = [0.36] * frames
    calibrator.data["mouth"]["mouth_ratios"] = [0.7] * frames
    calibrator.data["eyebrows"]["eyebrow_ratios"] = [0.4] * frames
    calibrator.data["smile"]["smile_ratios"] = [0.4] * frames
    calibrator.enabled_keys_in_run = {"mouth_open", "eyebrows_raised", "smile"}

    calibrator._calculate_thresholds()

    assert calibrator.state == "error"
    assert calibrator.calculated_thresholds == {}
    assert "Active smile ratio not higher than neutral" in calibrator.error_message

def test_calibration_mouth_phase(mocker):
    frames = 3
    calibrator_instance = Calibrator(frames_to_collect=frames)
    mock_landmarks = MockFaceLandmarks()
    mock_landmarks.set_landmark(33, 0.8, 0.4); mock_landmarks.set_landmark(263, 0.2, 0.4)

    mocker.patch.object(calibrator_module, 'get_mouth_open_ratio', return_value=0.7)
    mocker.patch.object(calibrator_module, 'get_eyebrows_raised_ratio', return_value=0.2)
    mocker.patch.object(calibrator_module, 'get_smile_ratio', return_value=0.5)
    mocker.patch.object(calibrator_module, 'get_left_ear', return_value=0.35)
    mocker.patch.object(calibrator_module, 'get_right_ear', return_value=0.36)


    calibrator_instance.start(["mouth_open", "eyebrows_raised"])
    for _ in range(frames): calibrator_instance.process_landmarks(mock_landmarks)
    assert calibrator_instance.state == "mouth"
    for _ in range(frames): calibrator_instance.process_landmarks(mock_landmarks)


    assert calibrator_instance.state == "eyebrows"
    assert calibrator_instance.frame_count == 0
    assert "Raise Eyebrows High" in calibrator_instance.get_current_instruction()
    assert len(calibrator_instance.data["mouth"]["mouth_ratios"]) == frames

def test_calibration_eyebrows_phase(mocker):
    frames = 3
    calibrator_instance = Calibrator(frames_to_collect=frames)
    mock_landmarks = MockFaceLandmarks()
    mock_landmarks.set_landmark(33, 0.8, 0.4); mock_landmarks.set_landmark(263, 0.2, 0.4)
    mocker.patch.object(calibrator_module, 'get_mouth_open_ratio', return_value=0.7)
    mocker.patch.object(calibrator_module, 'get_eyebrows_raised_ratio', return_value=0.4)
    mocker.patch.object(calibrator_module, 'get_smile_ratio', return_value=0.5)
    mocker.patch.object(calibrator_module, 'get_left_ear', return_value=0.35)
    mocker.patch.object(calibrator_module, 'get_right_ear', return_value=0.36)

    enabled_keys = ["mouth_open", "eyebrows_raised", "smile"]
    calibrator_instance.start(enabled_keys)
    for _ in range(frames): calibrator_instance.process_landmarks(mock_landmarks)
    for _ in range(frames): calibrator_instance.process_landmarks(mock_landmarks)
    assert calibrator_instance.state == "eyebrows"
    for i in range(frames):
         calibrator_instance.process_landmarks(mock_landmarks)
         if i < frames - 1:
              assert calibrator_instance.state == "eyebrows"

    assert calibrator_instance.state == "smile"
    assert calibrator_instance.frame_count == 0
    assert "Smile Naturally" in calibrator_instance.get_current_instruction()
    assert len(calibrator_instance.data["eyebrows"]["eyebrow_ratios"]) == frames

def test_calibration_smile_phase_ends_in_calc(mocker):
    """Test data collection in smile phase and transition to calculating/done."""
    frames = 3
    calibrator_instance = Calibrator(frames_to_collect=frames)
    mock_landmarks = MockFaceLandmarks()
    mock_landmarks.set_landmark(33, 0.8, 0.4); mock_landmarks.set_landmark(263, 0.2, 0.4)
    calibrator_instance.data["neutral"]["mouth_ratios"] = [0.1] * frames
    calibrator_instance.data["neutral"]["eyebrow_ratios"] = [0.2] * frames
    calibrator_instance.data["neutral"]["smile_ratios"] = [0.5] * frames
    calibrator_instance.data["neutral"]["left_ears"] = [0.35] * frames
    calibrator_instance.data["neutral"]["right_ears"] = [0.36] * frames
    calibrator_instance.data["mouth"]["mouth_ratios"] = [0.7] * frames
    calibrator_instance.data["eyebrows"]["eyebrow_ratios"] = [0.4] * frames
    calibrator_instance.state = "smile"
    calibrator_instance.frame_count = 0
    calibrator_instance.active_phases_in_run = ["mouth", "eyebrows", "smile"]
    calibrator_instance.current_phase_index = 2
    calibrator_instance.enabled_keys_in_run = {"mouth_open", "eyebrows_raised", "smile"}

    mocker.patch.object(calibrator_module, 'get_mouth_open_ratio', return_value=0.1)
    mocker.patch.object(calibrator_module, 'get_eyebrows_raised_ratio', return_value=0.2)
    mock_smile = mocker.patch.object(calibrator_module, 'get_smile_ratio', return_value=0.8)
    mocker.patch.object(calibrator_module, 'get_left_ear', return_value=0.35)
    mocker.patch.object(calibrator_module, 'get_right_ear', return_value=0.36)
    spy_calculate = mocker.spy(calibrator_instance, '_calculate_thresholds')

    for i in range(frames):
        assert calibrator_instance.state == "smile"
        calibrator_instance.process_landmarks(mock_landmarks)

    spy_calculate.assert_called_once()
    assert calibrator_instance.state == "done"
    assert "Complete" in calibrator_instance.get_current_instruction()
    assert len(calibrator_instance.data["smile"]["smile_ratios"]) == frames
    assert calibrator_instance.data["smile"]["smile_ratios"] == [0.8] * frames
    assert mock_smile.call_count == frames
    assert "smile" in calibrator_instance.calculated_thresholds
    assert calibrator_instance.calculated_thresholds["smile"] == pytest.approx(0.5 + 0.6 * (0.8 - 0.5))

def test_process_landmarks_no_face(mocker):
    calibrator_instance = Calibrator()

    calibrator_instance.start(DEFAULT_ENABLED_KEYS)
    initial_instruction = calibrator_instance.get_current_instruction()
    calibrator_instance.process_landmarks(None)


    assert calibrator_instance.state == "neutral"
    assert calibrator_instance.frame_count == 0
    assert calibrator_instance.data["neutral"]["mouth_ratios"] == []
    assert "(No face detected!)" in calibrator_instance.get_current_instruction()

def test_process_landmarks_ratio_none(mocker):
    calibrator_instance = Calibrator()
    mock_landmarks = MockFaceLandmarks()
    mock_landmarks.set_landmark(33, 0.8, 0.4); mock_landmarks.set_landmark(263, 0.2, 0.4)

    mocker.patch.object(calibrator_module, 'get_mouth_open_ratio', return_value=None)
    mocker.patch.object(calibrator_module, 'get_eyebrows_raised_ratio', return_value=0.2)
    mocker.patch.object(calibrator_module, 'get_smile_ratio', return_value=0.5)
    mocker.patch.object(calibrator_module, 'get_left_ear', return_value=0.35)
    mocker.patch.object(calibrator_module, 'get_right_ear', return_value=0.36)


    calibrator_instance.start(DEFAULT_ENABLED_KEYS)
    initial_instruction = calibrator_instance.get_current_instruction()
    calibrator_instance.process_landmarks(mock_landmarks)


    assert calibrator_instance.state == "neutral"
    assert calibrator_instance.frame_count == 0
    assert calibrator_instance.data["neutral"]["mouth_ratios"] == []
    assert "(Ratio Error!)" in calibrator_instance.get_current_instruction()

def test_calculate_thresholds_error_insufficient_data(mocker):
    frames_needed = 10
    min_samples = max(1, frames_needed // 4)
    calibrator_instance = Calibrator(frames_to_collect=frames_needed)
    calibrator_instance.data["neutral"]["mouth_ratios"] = [0.1] * frames_needed
    calibrator_instance.data["neutral"]["eyebrow_ratios"] = [0.2] * frames_needed
    calibrator_instance.data["neutral"]["smile_ratios"] = [0.5] * frames_needed
    calibrator_instance.data["neutral"]["left_ears"] = [0.35] * frames_needed
    calibrator_instance.data["neutral"]["right_ears"] = [0.36] * frames_needed
    calibrator_instance.data["mouth"]["mouth_ratios"] = [0.7] * (min_samples - 1)
    calibrator_instance.data["eyebrows"]["eyebrow_ratios"] = [0.4] * frames_needed
    calibrator_instance.data["smile"]["smile_ratios"] = [0.8] * frames_needed
    calibrator_instance.enabled_keys_in_run = {"mouth_open", "eyebrows_raised", "smile"}

    calibrator_instance._calculate_thresholds()

    assert calibrator_instance.state == "error"
    assert calibrator_instance.calculated_thresholds == {}
    assert "Not enough data collected for mouth open" in calibrator_instance.error_message