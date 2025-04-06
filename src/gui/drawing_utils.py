import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def draw_landmarks_on_image(bgr_image, detection_result):
    """
    Draws the detected face landmarks onto the image.
    Uses the default MediaPipe drawing functions.

    :param bgr_image: The BGR image (numpy array) to draw upon.
                      Note: This function works on a copy, the original is not modified.
    :param detection_result: The 'results' object from MediaPipe Face Mesh process().
    :return: A new image (numpy array) with the landmarks drawn.
    """
    annotated_image = bgr_image.copy()
    if detection_result.multi_face_landmarks:
        for face_landmarks in detection_result.multi_face_landmarks:
            mp_drawing.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks,
                connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())
            mp_drawing.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks,
                connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style())
    return annotated_image