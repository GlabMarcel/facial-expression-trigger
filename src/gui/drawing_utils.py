
def draw_landmarks_on_image(bgr_image, detection_result,
                            mp_drawing, mp_face_mesh, mp_drawing_styles):
    """
    Draws the detected face landmarks onto the image.
    Uses the passed MediaPipe drawing functions and constants.

    :param bgr_image: The BGR image (numpy array) to draw upon.
    :param detection_result: The 'results' object from MediaPipe Face Mesh process().
    :param mp_drawing: The mediapipe.solutions.drawing_utils module.
    :param mp_face_mesh: The mediapipe.solutions.face_mesh module.
    :param mp_drawing_styles: The mediapipe.solutions.drawing_styles module.
    :return: A new image (numpy array) with the landmarks drawn.
    """
    annotated_image = bgr_image.copy()
    if detection_result.multi_face_landmarks:
        for face_landmarks in detection_result.multi_face_landmarks:
            mp_drawing.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())
            mp_drawing.draw_landmarks(
                image=annotated_image,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style())
    return annotated_image