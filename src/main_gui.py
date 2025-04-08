import sys
import os
from PyQt6.QtWidgets import QApplication
from controller.app_controller import AppController
import multiprocessing as mp

def load_stylesheet():
    """Loads the QSS stylesheet from file."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    qss_path = os.path.join(script_dir, "gui", "style.qss")
    if os.path.exists(qss_path):
        print(f"Loading stylesheet from: {qss_path}")
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            return ""
    else:
        print(f"Stylesheet not found at: {qss_path}")
        return ""

if __name__ == "__main__":
    try:
        mp.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
    app = QApplication(sys.argv)
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    controller = AppController(app)
    controller.show_view()
    sys.exit(app.exec())