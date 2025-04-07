import sys
from PyQt6.QtWidgets import QApplication
from controller.app_controller import AppController
import multiprocessing as mp

if __name__ == "__main__":
    try:
        mp.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
    app = QApplication(sys.argv)
    controller = AppController(app)
    controller.show_view()
    sys.exit(app.exec())