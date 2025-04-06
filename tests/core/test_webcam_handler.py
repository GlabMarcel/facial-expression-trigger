import pytest
import numpy as np
import cv2
import sys

from src.core import webcam_handler
from src.core.webcam_handler import WebcamHandler


def test_webcamhandler_init_success(mocker):
    mock_capture = mocker.Mock(spec=cv2.VideoCapture)
    mock_capture.isOpened.return_value = True
    mock_videocapture_class = mocker.patch('cv2.VideoCapture', return_value=mock_capture)
    mocker.patch('cv2.flip')

    handler = WebcamHandler(source=5)

    mock_videocapture_class.assert_called_once_with(5)
    mock_capture.isOpened.assert_called_once()
    assert handler.capture == mock_capture

def test_webcamhandler_init_failure_raises_sysexit(mocker):
    mock_capture = mocker.Mock(spec=cv2.VideoCapture)
    mock_capture.isOpened.return_value = False
    mocker.patch('cv2.VideoCapture', return_value=mock_capture)
    mock_exit = mocker.patch('sys.exit')

    try:
        WebcamHandler(source=0)
    except SystemExit:
        pass

    mock_exit.assert_called_once()

def test_webcamhandler_read_frame_success(mocker):
    mock_capture = mocker.Mock(spec=cv2.VideoCapture)
    mock_capture.isOpened.return_value = True
    fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    flipped_frame = np.ones((100, 100, 3), dtype=np.uint8)
    mock_capture.read.return_value = (True, fake_frame)
    mocker.patch('cv2.VideoCapture', return_value=mock_capture)
    mock_flip = mocker.patch('cv2.flip', return_value=flipped_frame)

    handler = WebcamHandler()

    success, frame = handler.read_frame()

    mock_capture.read.assert_called_once()
    mock_flip.assert_called_once_with(fake_frame, 1)
    assert success == True
    assert frame is flipped_frame

def test_webcamhandler_read_frame_failure(mocker):
    mock_capture = mocker.Mock(spec=cv2.VideoCapture)
    mock_capture.isOpened.return_value = True
    mock_capture.read.return_value = (False, None)
    mocker.patch('cv2.VideoCapture', return_value=mock_capture)
    mock_flip = mocker.patch('cv2.flip')

    handler = WebcamHandler()

    success, frame = handler.read_frame()

    mock_capture.read.assert_called_once()
    mock_flip.assert_not_called()
    assert success == False
    assert frame is None

def test_webcamhandler_release(mocker):
    mock_capture = mocker.Mock(spec=cv2.VideoCapture)
    mock_capture.isOpened.return_value = True
    mocker.patch('cv2.VideoCapture', return_value=mock_capture)
    mocker.patch('cv2.flip')
    handler = WebcamHandler()

    handler.release()

    mock_capture.release.assert_called_once()

def test_webcamhandler_is_opened(mocker):
    mock_capture = mocker.Mock(spec=cv2.VideoCapture)
    mocker.patch('cv2.VideoCapture', return_value=mock_capture)
    mocker.patch('cv2.flip')
    handler = WebcamHandler()


    mock_capture.isOpened.return_value = True
    assert handler.is_opened() == True
    mock_capture.isOpened.assert_called_with()


    mock_capture.isOpened.return_value = False
    assert handler.is_opened() == False
    assert mock_capture.isOpened.call_count == 3