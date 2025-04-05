# src/webcam_handler.py
import cv2
import sys

class WebcamHandler:
    """
    A class to manage webcam access using OpenCV.
    """
    def __init__(self, source=0):
        """
        Initializes the webcam connection.

        :param source: The index of the camera (0 is usually the default webcam).
        """
        self.source = source
        self.capture = cv2.VideoCapture(self.source)

        if not self.capture.isOpened():
            print(f"Error: Could not open webcam source {self.source}.")
            sys.exit(f"Application exiting, camera source {self.source} not found.")

        print(f"Webcam source {self.source} opened successfully.")

    def read_frame(self):
        """
        Reads a single frame from the webcam.

        :return: A tuple (success, frame), where success is a boolean
                 and frame is the image (numpy array) or None on error.
        """
        success, frame = self.capture.read()
        if success:
            frame = cv2.flip(frame, 1)
        return success, frame

    def release(self):
        """
        Releases the webcam resource.
        """
        if self.capture.isOpened():
            self.capture.release()
            print(f"Webcam source {self.source} released.")

    def is_opened(self):
        """
        Checks if the webcam connection is still open.

        :return: True if open, False otherwise.
        """
        return self.capture.isOpened()
