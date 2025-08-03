import os
import sys

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QSettings

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QMainWindow, QVBoxLayout, QLabel
)

from app.log_factory import create_logger
from app.v22.worker import Worker


# Disable Qt High DPI scaling
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
QApplication.setAttribute(Qt.ApplicationAttribute.AA_Use96Dpi)

LOGGER = create_logger(name='MainWindow')

class MainWindow(QMainWindow):
    """
    The main application window for the game automation tool.
    Handles UI elements and manages the overall state of the automation.
    """
    # Define states for the automation process
    NOT_RUNNING = "Not Running"
    RUNNING = "Running"
    PAUSED = "Paused"
    
    # Signal to tell the worker thread to start a task
    #start_worker_task = pyqtSignal(str)

    start_detection_signal = pyqtSignal()
    stop_detection_signal = pyqtSignal()

    def __init__(self):
        """
        Initializes the MainWindow.
        Sets up the UI, connects signals, and defines initial state.
        """
        super().__init__()
        self.setWindowTitle("Game Automation Tool")
        self.setGeometry(100, 100, 250, 200) # x, y, width, height
        self.settings = QSettings("data/config_v22.ini", QSettings.Format.IniFormat)
        self.INACTIVITY_DURATION = self.settings.value("Detection/InactivityDurationAutoStartSeconds", 60, type=int)

        self.running = False
        self.worker = Worker(self.settings)

        self._setup_ui()
        self._connect_signals()
        self.start_detect_worker()

    def _setup_ui(self):
        """
        Sets up the graphical user interface elements.
        """
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Status Label
        self.status_label = QLabel("Status: " + self.current_state)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.status_label)

        # Task Status Label (for worker messages)
        self.task_status_label = QLabel("Task Status: Idle")
        self.task_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.task_status_label.setStyleSheet("font-size: 14px; color: #555;")
        layout.addWidget(self.task_status_label)

        # Start/Pause Button
        self.start_button = QPushButton(" ▶️ ", self)
        self.start_button.clicked.connect(self.on_start)
        layout.addWidget(self.start_button)

        self.close_button = QPushButton("❌", self)
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button)


    def _connect_signals(self):
        """
        Connects signals from the worker thread and timer to slots in the main window.
        """
        self.start_button.clicked.connect(self.on_start)
        self.close_button.clicked.connect(self.close)


        # Connect the main window's signal to the worker's slot
        # This connection ensures that _do_task runs in the worker's thread
        self.start_worker_task.connect(self.worker.start_loop)


    def _update_ui_state(self):
        """
        Updates the text of the buttons and status label based on the current state.
        """
        self.status_label.setText("Status: " + self.current_state)

    def on_start(self):
        LOGGER.info("Start button clicked")
        self.running = not self.running

        if self.running:
            self.start_auto()
        else:
            LOGGER.info("pause auto detect")
            self.stop_detection_signal.emit();
            self.start_button.setText("▶️")

    def closeEvent(self, event):
        """
        Overrides the close event to ensure the worker thread is properly terminated.
        """
        print("Closing application. Stopping worker thread...")
        self.worker.stop_worker() # Tell the worker to stop its loop
        self.worker.wait() # Wait for the worker thread to finish
        print("Worker thread stopped.")
        self.overlay_window.hide() # Hide the overlay window
        event.accept() # Accept the close event
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

