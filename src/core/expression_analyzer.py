# src/core/expression_analyzer.py
import math
import numpy as np

LIP_TOP_INDEX = 13
LIP_BOTTOM_INDEX = 14
LEFT_EYE_CORNER_INDEX = 33
RIGHT_EYE_CORNER_INDEX = 263
LEFT_EYEBROW_TOP_INDEX = 105
LEFT_EYE_TOP_INDEX = 159
RIGHT_EYEBROW_TOP_INDEX = 334
RIGHT_EYE_TOP_INDEX = 386
MOUTH_CORNER_LEFT = 61
MOUTH_CORNER_RIGHT = 291

def calculate_distance(p1, p2):
    if p1 is None or p2 is None: return 0.0
    if hasattr(p1, 'x') and hasattr(p1, 'y') and hasattr(p2, 'x') and hasattr(p2, 'y'):
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    else:
        return 0.0

def get_mouth_open_ratio(face_landmarks):
    try:
        lip_top = face_landmarks.landmark[LIP_TOP_INDEX]
        lip_bottom = face_landmarks.landmark[LIP_BOTTOM_INDEX]
        left_eye_corner = face_landmarks.landmark[LEFT_EYE_CORNER_INDEX]
        right_eye_corner = face_landmarks.landmark[RIGHT_EYE_CORNER_INDEX]
        lip_distance_y = abs(lip_top.y - lip_bottom.y)
        eye_distance_x = abs(left_eye_corner.x - right_eye_corner.x)
        if eye_distance_x == 0: return 0.0
        return lip_distance_y / eye_distance_x
    except (IndexError, AttributeError): return None
    except Exception as e: return None

def get_eyebrows_raised_ratio(face_landmarks):
    try:
        left_eyebrow_top = face_landmarks.landmark[LEFT_EYEBROW_TOP_INDEX]
        left_eye_top = face_landmarks.landmark[LEFT_EYE_TOP_INDEX]
        right_eyebrow_top = face_landmarks.landmark[RIGHT_EYEBROW_TOP_INDEX]
        right_eye_top = face_landmarks.landmark[RIGHT_EYE_TOP_INDEX]
        left_eye_corner = face_landmarks.landmark[LEFT_EYE_CORNER_INDEX]
        right_eye_corner = face_landmarks.landmark[RIGHT_EYE_CORNER_INDEX]
        vertical_distance_left = abs(left_eyebrow_top.y - left_eye_top.y)
        vertical_distance_right = abs(right_eyebrow_top.y - right_eye_top.y)
        eye_distance_x = abs(left_eye_corner.x - right_eye_corner.x)
        if eye_distance_x == 0: return 0.0
        ratio_left = vertical_distance_left / eye_distance_x
        ratio_right = vertical_distance_right / eye_distance_x
        average_ratio = (ratio_left + ratio_right) / 2.0
        return average_ratio
    except (IndexError, AttributeError): return None
    except Exception as e: return None

def get_smile_ratio(face_landmarks):
    try:
        mouth_left = face_landmarks.landmark[MOUTH_CORNER_LEFT]
        mouth_right = face_landmarks.landmark[MOUTH_CORNER_RIGHT]
        left_eye_corner = face_landmarks.landmark[LEFT_EYE_CORNER_INDEX]
        right_eye_corner = face_landmarks.landmark[RIGHT_EYE_CORNER_INDEX]
        mouth_width = calculate_distance(mouth_left, mouth_right)
        eye_distance_x = abs(left_eye_corner.x - right_eye_corner.x)
        if eye_distance_x == 0: return 0.0
        ratio = mouth_width / eye_distance_x
        return ratio
    except (IndexError, AttributeError): return None
    except Exception as e: return None