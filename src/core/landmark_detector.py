import mediapipe as mp

class LandmarkDetector:
    """
    Detects face landmarks using MediaPipe Face Mesh.
    """
    def __init__(self, static_mode=False, max_faces=1, refine_landmarks=False, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Initializes the MediaPipe Face Mesh model.

        :param static_mode: Whether to treat the input images as a batch of static
                            and possibly unrelated images, or a video stream.
        :param max_faces: Maximum number of faces to detect.
        :param refine_landmarks: Whether to further refine the landmark coordinates
                                 around the eyes and lips, and output additional landmarks
                                 around the irises. Default to False.
        :param min_detection_confidence: Minimum confidence value ([0.0, 1.0]) for face
                                         detection to be considered successful.
        :param min_tracking_confidence: Minimum confidence value ([0.0, 1.0]) for the
                                        face landmarks to be considered tracked successfully.
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=static_mode,
            max_num_faces=max_faces,
            refine_landmarks=refine_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence)
        print("MediaPipe Face Mesh initialized.")

    def detect_landmarks(self, frame_rgb):
        """
        Processes a frame and detects face landmarks.

        :param frame_rgb: The input frame in RGB format (numpy array).
        :return: The MediaPipe results object containing the landmark data.
        """
        results = self.face_mesh.process(frame_rgb)
        return results

    def close(self):
        """Releases the MediaPipe Face Mesh resources."""
        self.face_mesh.close()
        print("MediaPipe Face Mesh resources released.")