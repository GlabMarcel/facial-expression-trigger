import pytest
import mediapipe as mp
import numpy as np

from src.core import landmark_detector
from src.core.landmark_detector import LandmarkDetector


def test_landmarkdetector_init(mocker):
    mock_facemesh_class = mocker.patch('mediapipe.solutions.face_mesh.FaceMesh')
    mock_mesh_instance = mocker.Mock()
    mock_facemesh_class.return_value = mock_mesh_instance

    detector = LandmarkDetector(
        static_mode=True,
        max_faces=3,
        refine_landmarks=True,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.7
    )

    mock_facemesh_class.assert_called_once_with(
        static_image_mode=True,
        max_num_faces=3,
        refine_landmarks=True,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.7
    )
    assert detector.face_mesh == mock_mesh_instance

def test_landmarkdetector_detect_landmarks(mocker):
    mock_facemesh_class = mocker.patch('mediapipe.solutions.face_mesh.FaceMesh')
    mock_mesh_instance = mocker.Mock()
    mock_facemesh_class.return_value = mock_mesh_instance

    mock_results = mocker.Mock()
    mock_results.multi_face_landmarks = ["dummy_landmark_data"]
    mock_mesh_instance.process.return_value = mock_results

    detector = LandmarkDetector()
    dummy_rgb_frame = np.zeros((100, 100, 3), dtype=np.uint8)

    results = detector.detect_landmarks(dummy_rgb_frame)

    mock_mesh_instance.process.assert_called_once_with(dummy_rgb_frame)
    assert results == mock_results

def test_landmarkdetector_close(mocker):
    mock_facemesh_class = mocker.patch('mediapipe.solutions.face_mesh.FaceMesh')
    mock_mesh_instance = mocker.Mock()
    mock_facemesh_class.return_value = mock_mesh_instance

    detector = LandmarkDetector()

    detector.close()

    mock_mesh_instance.close.assert_called_once()