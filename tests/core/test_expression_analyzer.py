import pytest
import math
from src.core.expression_analyzer import (
    calculate_distance,
    get_mouth_open_ratio,
    get_eyebrows_raised_ratio,
    get_smile_ratio,
    LIP_TOP_INDEX, LIP_BOTTOM_INDEX,
    LEFT_EYE_CORNER_INDEX, RIGHT_EYE_CORNER_INDEX,
    LEFT_EYEBROW_TOP_INDEX, LEFT_EYE_TOP_INDEX,
    RIGHT_EYEBROW_TOP_INDEX, RIGHT_EYE_TOP_INDEX,
    MOUTH_CORNER_LEFT, MOUTH_CORNER_RIGHT
)


class MockLandmark:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class MockFaceLandmarks:
    def __init__(self, num_landmarks=478):
        self.landmark = {i: MockLandmark() for i in range(num_landmarks)}

    def set_landmark(self, index, x, y, z=0.0):
        if index in self.landmark:
            self.landmark[index].x = x
            self.landmark[index].y = y
            self.landmark[index].z = z
        else:
            print(f"Warning: Landmark index {index} out of range.")


def test_calculate_distance():
    p1 = MockLandmark(x=1, y=2)
    p2 = MockLandmark(x=4, y=6)

    assert calculate_distance(p1, p2) == pytest.approx(5.0)

def test_calculate_distance_zero():
    p1 = MockLandmark(x=1, y=2)
    p2 = MockLandmark(x=1, y=2)
    assert calculate_distance(p1, p2) == pytest.approx(0.0)


EYE_X_LEFT = 0.2
EYE_X_RIGHT = 0.8
EYE_Y = 0.4
EXPECTED_EYE_DISTANCE_X = abs(EYE_X_LEFT - EYE_X_RIGHT)

@pytest.fixture
def neutral_face_landmarks():
    face = MockFaceLandmarks()

    face.set_landmark(LEFT_EYE_CORNER_INDEX, EYE_X_LEFT, EYE_Y)
    face.set_landmark(RIGHT_EYE_CORNER_INDEX, EYE_X_RIGHT, EYE_Y)

    face.set_landmark(LIP_TOP_INDEX, 0.5, 0.70)
    face.set_landmark(LIP_BOTTOM_INDEX, 0.5, 0.72)

    face.set_landmark(LEFT_EYEBROW_TOP_INDEX, 0.3, 0.30)
    face.set_landmark(LEFT_EYE_TOP_INDEX, 0.3, 0.38)
    face.set_landmark(RIGHT_EYEBROW_TOP_INDEX, 0.7, 0.30)
    face.set_landmark(RIGHT_EYE_TOP_INDEX, 0.7, 0.38)

    face.set_landmark(MOUTH_CORNER_LEFT, 0.35, 0.75)
    face.set_landmark(MOUTH_CORNER_RIGHT, 0.65, 0.75)
    return face


def test_get_mouth_open_ratio_neutral(neutral_face_landmarks):
    ratio = get_mouth_open_ratio(neutral_face_landmarks)
    expected_neutral_ratio = abs(0.70 - 0.72) / EXPECTED_EYE_DISTANCE_X
    assert ratio is not None
    assert ratio == pytest.approx(expected_neutral_ratio)
    assert ratio < 0.3

def test_get_mouth_open_ratio_open(neutral_face_landmarks):
    neutral_face_landmarks.set_landmark(LIP_BOTTOM_INDEX, 0.5, 0.80)
    ratio = get_mouth_open_ratio(neutral_face_landmarks)
    expected_open_ratio = abs(0.70 - 0.80) / EXPECTED_EYE_DISTANCE_X
    assert ratio is not None
    assert ratio == pytest.approx(expected_open_ratio)
    assert ratio > 0.15

def test_get_eyebrows_raised_ratio_neutral(neutral_face_landmarks):
    ratio = get_eyebrows_raised_ratio(neutral_face_landmarks)
    expected_neutral_ratio_left = abs(0.30 - 0.38) / EXPECTED_EYE_DISTANCE_X
    expected_neutral_ratio_right = abs(0.30 - 0.38) / EXPECTED_EYE_DISTANCE_X
    expected_avg = (expected_neutral_ratio_left + expected_neutral_ratio_right) / 2.0
    assert ratio is not None
    assert ratio == pytest.approx(expected_avg)
    assert ratio < 0.2

def test_get_eyebrows_raised_ratio_raised(neutral_face_landmarks):
    neutral_face_landmarks.set_landmark(LEFT_EYEBROW_TOP_INDEX, 0.3, 0.25)
    neutral_face_landmarks.set_landmark(RIGHT_EYEBROW_TOP_INDEX, 0.7, 0.25)
    ratio = get_eyebrows_raised_ratio(neutral_face_landmarks)
    expected_raised_ratio_left = abs(0.25 - 0.38) / EXPECTED_EYE_DISTANCE_X
    expected_raised_ratio_right = abs(0.25 - 0.38) / EXPECTED_EYE_DISTANCE_X
    expected_avg = (expected_raised_ratio_left + expected_raised_ratio_right) / 2.0
    assert ratio is not None
    assert ratio == pytest.approx(expected_avg)
    assert ratio > 0.2

def test_get_smile_ratio_neutral(neutral_face_landmarks):
    ratio = get_smile_ratio(neutral_face_landmarks)

    p_left = neutral_face_landmarks.landmark[MOUTH_CORNER_LEFT]
    p_right = neutral_face_landmarks.landmark[MOUTH_CORNER_RIGHT]
    expected_mouth_width = calculate_distance(p_left, p_right)
    expected_neutral_ratio = expected_mouth_width / EXPECTED_EYE_DISTANCE_X
    assert ratio is not None
    assert ratio == pytest.approx(expected_neutral_ratio)

    assert ratio < 0.6

def test_get_smile_ratio_smiling(neutral_face_landmarks):
    neutral_face_landmarks.set_landmark(MOUTH_CORNER_LEFT, 0.30, 0.74)
    neutral_face_landmarks.set_landmark(MOUTH_CORNER_RIGHT, 0.70, 0.74)
    ratio = get_smile_ratio(neutral_face_landmarks)

    p_left = neutral_face_landmarks.landmark[MOUTH_CORNER_LEFT]
    p_right = neutral_face_landmarks.landmark[MOUTH_CORNER_RIGHT]
    expected_mouth_width = calculate_distance(p_left, p_right)
    expected_smile_ratio = expected_mouth_width / EXPECTED_EYE_DISTANCE_X
    assert ratio is not None
    assert ratio == pytest.approx(expected_smile_ratio)
    assert ratio > 0.6

def test_ratio_functions_return_none_on_index_error():
    face = MockFaceLandmarks(num_landmarks=50)
    assert get_mouth_open_ratio(face) is None
    assert get_eyebrows_raised_ratio(face) is None
    assert get_smile_ratio(face) is None