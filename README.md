# Facial Gesture Control (Proof of Concept)

## Description

This Python application utilizes a standard webcam and MediaPipe's Face Mesh technology to detect facial expressions in real-time. It allows users to trigger configurable keyboard actions (single keys, hotkeys, text typing) based on detected gestures, such as opening the mouth, raising eyebrows, or smiling.

The primary goal is to provide an alternative input method for computers, serving as an accessibility tool for individuals with motor impairments.

This project is currently in a Proof of Concept stage (as of April 6, 2025).

## Features

* Real-time face landmark detection via webcam using MediaPipe Face Mesh.
* Detection of gestures:
    * Mouth Open
    * Eyebrows Raised (Both)
    * **Smile** *(New)*
* Triggers keyboard actions (`press`, `hotkey`, `write`) via PyAutoGUI upon gesture detection (on state change False -> True).
* Graphical User Interface (GUI) built with PyQt6.
* Displays live webcam feed with landmark overlays.
* Provides a list view showing monitored expressions, their configured actions, and live status indicators.
* Includes a GUI-driven calibration routine to set detection thresholds specific to the user and lighting conditions (for Mouth, Eyebrows, **and Smile**).
* Allows configuration of actions per gesture via a user-friendly dialog (selecting from predefined common actions).
* Persistently saves calibrated thresholds and configured actions in `config.json` file.
* Modular code structure (`core` logic separated from `gui`).

## Requirements

* **Python:** Version **3.11.x** is strongly recommended due to library compatibility issues encountered with newer versions during development.
* **Operating System:** Developed and tested primarily on Windows. PyAutoGUI behavior might differ on macOS/Linux.
* **Webcam:** A standard webcam accessible by OpenCV.
* **Python Packages:** See `requirements.txt` (includes `opencv-python`, `mediapipe`, `pyautogui`, `PyQt6`, `numpy`).
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