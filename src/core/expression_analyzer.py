import math

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
LEFT_EYE_P1 = 33
LEFT_EYE_P2 = 160
LEFT_EYE_P3 = 158
LEFT_EYE_P4 = 133
LEFT_EYE_P5 = 153
LEFT_EYE_P6 = 144
LEFT_EYE_INDICES = [LEFT_EYE_P1, LEFT_EYE_P2, LEFT_EYE_P3, LEFT_EYE_P4, LEFT_EYE_P5, LEFT_EYE_P6]
RIGHT_EYE_P1 = 263
RIGHT_EYE_P2 = 387
RIGHT_EYE_P3 = 385
RIGHT_EYE_P4 = 362
RIGHT_EYE_P5 = 380
RIGHT_EYE_P6 = 373
RIGHT_EYE_INDICES = [RIGHT_EYE_P1, RIGHT_EYE_P2, RIGHT_EYE_P3, RIGHT_EYE_P4, RIGHT_EYE_P5, RIGHT_EYE_P6]

def calculate_ear(eye_points):
    try:
        ver1 = calculate_distance(eye_points[1], eye_points[5])
        ver2 = calculate_distance(eye_points[2], eye_points[4])
        hor = calculate_distance(eye_points[0], eye_points[3])

        if hor == 0:
            return None

        ear = (ver1 + ver2) / (2.0 * hor)
        return ear
    except (IndexError, TypeError):
        return None

def get_left_ear(face_landmarks):
    try:
        eye_points = [face_landmarks.landmark[i] for i in LEFT_EYE_INDICES]
        return calculate_ear(eye_points)
    except (IndexError, AttributeError, TypeError):
        return None

def get_right_ear(face_landmarks):
    try:
        eye_points = [face_landmarks.landmark[i] for i in RIGHT_EYE_INDICES]
        return calculate_ear(eye_points)
    except (IndexError, AttributeError, TypeError):
        return None

def calculate_distance(p1, p2):
    if p1 is None or p2 is None: return 0
    if hasattr(p1, 'x') and hasattr(p1, 'y') and hasattr(p2, 'x') and hasattr(p2, 'y'):
        return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
    else:
        return 0

def get_mouth_open_ratio(face_landmarks):
    try:
        lip_top = face_landmarks.landmark[LIP_TOP_INDEX]
        lip_bottom = face_landmarks.landmark[LIP_BOTTOM_INDEX]
        left_eye_corner = face_landmarks.landmark[LEFT_EYE_CORNER_INDEX]
        right_eye_corner = face_landmarks.landmark[RIGHT_EYE_CORNER_INDEX]

        lip_distance_y = abs(lip_top.y - lip_bottom.y)
        eye_distance = calculate_distance(left_eye_corner, right_eye_corner)

        if eye_distance == 0: return 0.0

        return lip_distance_y / eye_distance
    except IndexError:
        return None
    except Exception as e:
        return None

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
        eye_distance = calculate_distance(left_eye_corner, right_eye_corner)

        if eye_distance == 0: return 0.0

        ratio_left = vertical_distance_left / eye_distance
        ratio_right = vertical_distance_right / eye_distance
        average_ratio = (ratio_left + ratio_right) / 2.0

        return average_ratio
    except IndexError:
        return None
    except Exception as e:
        return None

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
    except (IndexError, AttributeError):
        return None
    except Exception as e:
        return None