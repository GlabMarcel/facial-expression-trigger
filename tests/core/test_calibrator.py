import pytest
import numpy as np
from src.core.calibrator import Calibrator
from src.core import calibrator as calibrator_module
import src.core.expression_analyzer as expression_analyzer

class MockLandmark:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x; self.y = y; self.z = z

class MockFaceLandmarks:
    def __init__(self, num_landmarks=478):
        self.landmark = {i: MockLandmark() for i in range(num_landmarks)}

    def set_landmark(self, index, x, y, z=0.0):
        if index in self.landmark:
            self.landmark[index].x = x; self.landmark[index].y = y; self.landmark[index].z = z


def test_calibrator_initialization():
    calibrator = Calibrator(frames_to_collect=50, threshold_factor=0.7)

    assert calibrator.state == "idle"
    assert calibrator.frames_to_collect == 50
    assert calibrator.threshold_factor == 0.7
    assert not calibrator.is_calibrating()
    assert calibrator.get_calculated_thresholds() is None
    assert calibrator.data["neutral"]["mouth_ratios"] == []
    assert calibrator.frame_count == 0

def test_calibrator_start():
    calibrator = Calibrator(frames_to_collect=60)
    calibrator.state = "done"
    calibrator.frame_count = 10
    calibrator.calculated_thresholds = {"test": 1}
    calibrator.data["neutral"]["mouth_ratios"].append(0.1)

    start_success = calibrator.start()

    assert start_success == True
    assert calibrator.state == "neutral"
    assert calibrator.is_calibrating() == True
    assert calibrator.frame_count == 0
    assert calibrator.calculated_thresholds == {}
    assert calibrator.data["neutral"]["mouth_ratios"] == []
    assert "look Neutral" in calibrator.get_current_instruction()

def test_calibration_neutral_phase_collects_data_and_transitions(mocker):
    frames = 3
    calibrator_instance = Calibrator(frames_to_collect=frames)
    mock_landmarks = MockFaceLandmarks()

    mock_landmarks.set_landmark(33, 0.8, 0.4)
    mock_landmarks.set_landmark(263, 0.2, 0.4)


    mock_mouth = mocker.patch.object(calibrator_module, 'get_mouth_open_ratio', return_value=0.1)
    mock_brows = mocker.patch.object(calibrator_module, 'get_eyebrows_raised_ratio', return_value=0.2)
    mock_smile = mocker.patch.object(calibrator_module, 'get_smile_ratio', return_value=0.5)


    calibrator_instance.start()

    for i in range(frames):
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

    assert mock_mouth.call_count == frames
    assert mock_brows.call_count == frames
    assert mock_smile.call_count == frames

def test_calculate_thresholds_success(mocker):
    calibrator = Calibrator(frames_to_collect=10, threshold_factor=0.6)

    calibrator.data["neutral"]["mouth_ratios"] = [0.1] * 10
    calibrator.data["neutral"]["eyebrow_ratios"] = [0.2] * 10
    calibrator.data["neutral"]["smile_ratios"] = [0.5] * 10
    calibrator.data["mouth"]["mouth_ratios"] = [0.7] * 10
    calibrator.data["eyebrows"]["eyebrow_ratios"] = [0.4] * 10
    calibrator.data["smile"]["smile_ratios"] = [0.8] * 10

    calibrator._calculate_thresholds()

    assert calibrator.state == "done"
    assert calibrator.error_message == ""
    expected_thresholds = {
        "mouth_open": round(0.1 + 0.6 * (0.7 - 0.1), 4),
        "eyebrows_raised": round(0.2 + 0.6 * (0.4 - 0.2), 4),
        "smile": round(0.5 + 0.6 * (0.8 - 0.5), 4)
    }
    assert calibrator.calculated_thresholds == pytest.approx(expected_thresholds)
    assert "Complete" in calibrator.current_instruction

def test_calculate_thresholds_error_active_not_higher(mocker):
    calibrator = Calibrator(frames_to_collect=10, threshold_factor=0.6)

    calibrator.data["neutral"]["mouth_ratios"] = [0.1] * 10
    calibrator.data["neutral"]["eyebrow_ratios"] = [0.2] * 10
    calibrator.data["neutral"]["smile_ratios"] = [0.5] * 10
    calibrator.data["mouth"]["mouth_ratios"] = [0.7] * 10
    calibrator.data["eyebrows"]["eyebrow_ratios"] = [0.4] * 10
    calibrator.data["smile"]["smile_ratios"] = [0.4] * 10

    calibrator._calculate_thresholds()

    assert calibrator.state == "error"
    assert calibrator.calculated_thresholds == {}
    assert "Calculation Error" in calibrator.error_message
    assert "smile ratio not higher" in calibrator.error_message

def test_calibration_mouth_phase(mocker):
    frames = 3
    calibrator_instance = Calibrator(frames_to_collect=frames)
    mock_landmarks = MockFaceLandmarks()
    mock_landmarks.set_landmark(33, 0.8, 0.4); mock_landmarks.set_landmark(263, 0.2, 0.4)

    calibrator_instance.state = "mouth"
    calibrator_instance.frame_count = 0

    mock_mouth = mocker.patch.object(calibrator_module, 'get_mouth_open_ratio', return_value=0.7)

    mocker.patch.object(calibrator_module, 'get_eyebrows_raised_ratio', return_value=0.2)
    mocker.patch.object(calibrator_module, 'get_smile_ratio', return_value=0.5)


    for _ in range(frames):
        assert calibrator_instance.state == "mouth"
        calibrator_instance.process_landmarks(mock_landmarks)

    assert calibrator_instance.state == "eyebrows"
    assert calibrator_instance.frame_count == 0
    assert "Raise Eyebrows High" in calibrator_instance.get_current_instruction()
    assert len(calibrator_instance.data["mouth"]["mouth_ratios"]) == frames
    assert calibrator_instance.data["mouth"]["mouth_ratios"] == [0.7] * frames
    assert mock_mouth.call_count == frames

def test_calibration_eyebrows_phase(mocker):
    frames = 3
    calibrator_instance = Calibrator(frames_to_collect=frames)
    mock_landmarks = MockFaceLandmarks()
    mock_landmarks.set_landmark(33, 0.8, 0.4); mock_landmarks.set_landmark(263, 0.2, 0.4)

    calibrator_instance.state = "eyebrows"
    calibrator_instance.frame_count = 0
    mock_brows = mocker.patch.object(calibrator_module, 'get_eyebrows_raised_ratio', return_value=0.4)
    mocker.patch.object(calibrator_module, 'get_mouth_open_ratio', return_value=0.1)
    mocker.patch.object(calibrator_module, 'get_smile_ratio', return_value=0.5)

    for _ in range(frames):
        assert calibrator_instance.state == "eyebrows"
        calibrator_instance.process_landmarks(mock_landmarks)

    assert calibrator_instance.state == "smile"
    assert calibrator_instance.frame_count == 0
    assert "Smile Naturally" in calibrator_instance.get_current_instruction()
    assert len(calibrator_instance.data["eyebrows"]["eyebrow_ratios"]) == frames
    assert calibrator_instance.data["eyebrows"]["eyebrow_ratios"] == [0.4] * frames
    assert mock_brows.call_count == frames

def test_calibration_smile_phase(mocker):
    frames = 3
    calibrator_instance = Calibrator(frames_to_collect=frames)
    mock_landmarks = MockFaceLandmarks()
    mock_landmarks.set_landmark(33, 0.8, 0.4); mock_landmarks.set_landmark(263, 0.2, 0.4)

    calibrator_instance.state = "smile"
    calibrator_instance.frame_count = 0
    calibrator_instance.data["neutral"]["mouth_ratios"] = [0.1] * frames
    calibrator_instance.data["neutral"]["eyebrow_ratios"] = [0.2] * frames
    calibrator_instance.data["neutral"]["smile_ratios"] = [0.5] * frames
    calibrator_instance.data["mouth"]["mouth_ratios"] = [0.7] * frames
    calibrator_instance.data["eyebrows"]["eyebrow_ratios"] = [0.4] * frames
    mock_smile = mocker.patch.object(calibrator_module, 'get_smile_ratio', return_value=0.8)
    mocker.patch.object(calibrator_module, 'get_mouth_open_ratio', return_value=0.1)
    mocker.patch.object(calibrator_module, 'get_eyebrows_raised_ratio', return_value=0.2)
    spy_calculate = mocker.spy(calibrator_instance, '_calculate_thresholds')

    for _ in range(frames):
        assert calibrator_instance.state == "smile"
        calibrator_instance.process_landmarks(mock_landmarks)

    assert "Complete" in calibrator_instance.get_current_instruction()
    assert len(calibrator_instance.data["smile"]["smile_ratios"]) == frames
    assert calibrator_instance.data["smile"]["smile_ratios"] == [0.8] * frames
    assert mock_smile.call_count == frames
    spy_calculate.assert_called_once()
    assert "smile" in calibrator_instance.calculated_thresholds

def test_process_landmarks_no_face(mocker):
    calibrator_instance = Calibrator()
    calibrator_instance.start()
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

    calibrator_instance.start()
    initial_instruction = calibrator_instance.get_current_instruction()

    calibrator_instance.process_landmarks(mock_landmarks)

    assert calibrator_instance.state == "neutral"
    assert calibrator_instance.frame_count == 0
    assert calibrator_instance.data["neutral"]["mouth_ratios"] == []

    assert "(Ratio Error!)" in calibrator_instance.get_current_instruction()

def test_calculate_thresholds_error_insufficient_data(mocker):
    calibrator_instance = Calibrator(frames_to_collect=10)

    calibrator_instance.data["neutral"]["mouth_ratios"] = [0.1] * 5
    calibrator_instance.data["neutral"]["eyebrow_ratios"] = [0.2] * 5
    calibrator_instance.data["neutral"]["smile_ratios"] = [0.5] * 5
    calibrator_instance.data["mouth"]["mouth_ratios"] = [0.7]
    calibrator_instance.data["eyebrows"]["eyebrow_ratios"] = [0.4] * 5
    calibrator_instance.data["smile"]["smile_ratios"] = [0.8] * 5

    calibrator_instance._calculate_thresholds()

    assert calibrator_instance.state == "error"
    assert calibrator_instance.calculated_thresholds == {}
    assert "Calculation Error" in calibrator_instance.error_message
    assert "Not enough data collected for mouth open" in calibrator_instance.error_message