# Facial Gesture Control (Proof of Concept)

## Description

This Python application utilizes a standard webcam and MediaPipe's Face Mesh technology to detect facial expressions in real-time. It allows users to trigger configurable keyboard actions (single keys, hotkeys, text typing) based on detected gestures, such as opening the mouth, raising eyebrows, or smiling.

The primary goal is to provide an alternative input method for computers, serving as an accessibility tool for individuals with motor impairments.

This project is currently in a Proof of Concept stage (as of April 6, 2025).

## Features

* **Real-time Facial Landmark Detection:** Utilizes the webcam and MediaPipe Face Mesh to detect facial landmarks in real-time, enabling the recognition of various facial expressions.
* **Gesture Detection:**
    * **Mouth Open:** Detects when the user opens their mouth.
    * **Eyebrows Raised (Both):** Detects when the user raises both eyebrows simultaneously.
    * **Smile:** Detects a smile based on the mouth's width in comparison to the distance between the eyes.
* **Configurable Keyboard Actions:** Triggers keyboard actions using PyAutoGUI when a gesture is detected (specifically, on the transition from a gesture not being detected to being detected). Supported actions include:
    * `press`: Simulate pressing a single key (e.g., "enter", "space").
    * `hotkey`: Simulate pressing a combination of keys (e.g., "ctrl+c", "alt+tab").
    * `write`: Simulate typing text (e.g., ":)", "Hello!").
* **Graphical User Interface (GUI):** Built with PyQt6, the GUI provides a user-friendly interface for interacting with the application.
* **Live Webcam Feed with Overlays:** Displays the live webcam feed with visual overlays of detected facial landmarks, providing feedback on the detection process.
* **Expression Monitoring and Status:** Presents a list view showing the monitored expressions (Mouth Open, Eyebrows Raised, Smile), their currently configured actions, and live status indicators (green when detected, otherwise not).
* **GUI-Driven Calibration:** Includes a calibration routine accessible through the GUI. This allows users to set detection thresholds specific to their facial features and the lighting conditions of their environment, ensuring accurate and reliable gesture detection. The calibration covers Mouth Open, Eyebrows Raised, and Smile.
* **Action Configuration Dialog:** Offers a user-friendly dialog for configuring actions associated with each gesture. Users can select from a predefined list of common actions (keys, hotkeys, text strings).
* **Persistent Configuration:** Saves the calibrated thresholds and configured actions in a `config.json` file in the project's root directory, ensuring settings are retained between application runs.
* **Modular Code Structure:** The application is designed with a modular structure, separating the core logic (landmark detection, expression analysis, action triggering) from the GUI components. This enhances maintainability and potential future extensions.

## Requirements

* **MediaPipe:** This library provides the core face mesh functionality for landmark detection.
* **Python:** Version **3.11.x** is strongly recommended due to library compatibility issues encountered with newer versions during development.
* **Operating System:** Developed and tested primarily on Windows. PyAutoGUI behavior might differ on macOS/Linux.
* **Webcam:** A standard webcam accessible by OpenCV.
* **Python Packages:** See `requirements.txt` for a complete list of required packages. Key dependencies include:
    * `opencv-python`: For webcam access and image processing.
    * `mediapipe`: For face landmark detection.
    * `pyautogui`: For simulating keyboard actions.
    * `PyQt6`: For building the graphical user interface.
    * `numpy`: For numerical operations.
* **Windows Prerequisite:** You might need to install the latest **Microsoft Visual C++ Redistributable (x64)** for MediaPipe/OpenCV to work correctly. Download from Microsoft's official website and **restart your PC** after installation.

## Setup

1.  **Clone/Download:** Get the project files.
2.  **Install Python 3.11:** Ensure a compatible Python 3.11.x version is installed on your system.
3.  **Navigate:** Open your terminal or PowerShell in the project's root directory (where this README is located).
4.  **Create Virtual Environment:**
    ```bash
    # Replace C:\Path\To\Python311\ with the actual path to your Python 3.11 executable
    C:\Path\To\Python311\python.exe -m venv .venv
    ```
5.  **Activate Virtual Environment:**
    * Windows PowerShell: `.\.venv\Scripts\activate.ps1`
    * Windows CMD: `.\.venv\Scripts\activate.bat`
    * macOS/Linux: `source .venv/bin/activate`
    (You should see `(.venv)` at the beginning of your terminal prompt).
6.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

* Settings like detection thresholds and action mappings are stored in `config.json` in the project root directory.
* If `config.json` is missing, it will be created with default values on the first run (including entries for "smile"). *(Updated)*
* **Thresholds:** It is highly recommended to use the built-in calibration (`Calibrate` button) to set appropriate thresholds for your face and environment. These are saved automatically to `config.json`.
* **Actions:** Use the `Edit` button next to each expression in the running application's GUI to configure the desired action. Actions are selected from a predefined list in a dialog. The configuration (e.g., `{"type": "press", "value": "enter"}`) is saved automatically to `config.json`.

## Usage

1.  Ensure your virtual environment is activated.
2.  Run the application from the project root directory:
    ```bash
    python src/main_gui.py
    ```
3.  The main window appears. Click **"Start"** to begin webcam capture and detection.
4.  (Recommended First Step) Click **"Calibrate"** and carefully follow the instructions displayed (in the terminal or overlaid on the video) to calibrate the thresholds for "Mouth Open", "Eyebrows Raised", **and "Smile"**. The sequence is typically: Neutral -> Open Mouth -> Raise Brows -> Smile. *(Updated)*
5.  Click the **"Edit"** button next to an expression (e.g., "Smile").
6.  In the dialog window, select the desired action (e.g., "Type: :)") from the dropdown list.
7.  Click **"OK"** to save the selected action for that expression.
8.  Perform the calibrated facial gestures. The status indicators in the GUI should turn green when a gesture is detected, and the configured action should be triggered once per detection. Use another application (like a text editor) to observe the triggered actions.
9.  Click **"Stop"** to pause detection.
10. Close the window to exit the application. Resources will be released automatically.

### Future Work / TODO

* Add more expressions (Wink, Head Nod/Shake).
* Implement more robust trigger mechanisms (e.g., gesture hold time).
* Improve calibration routine (visual feedback, better statistics like median, single gesture recalibration).
* Enhance action configuration (custom text input via accessible means, custom hotkey capture - considering accessibility).
* Add mouse control actions.
* Improve GUI (layout, themes, help section).
* Packaging for distribution (PyInstaller).