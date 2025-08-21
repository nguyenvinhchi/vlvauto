import os
import sys
import win32api

from PyQt6.QtCore import QThread, Qt, pyqtSignal, QTimer, QMetaObject, QSettings, QDateTime
from PyQt6.QtGui import QCursor, QGuiApplication, QColor

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout, QLabel
)

from app.flow_layout import FlowLayout
from app.game_scenario import CrashDialogScenario
from app.log_factory import create_logger
from app.pattern.create_pattern_dialog import PatternCreatorDialog
from app.v2.base_app import BaseApp
from app.v2.detection_worker_v2 import DetectionWorkerV2
from app.v2.draggable_button import DraggableButton
from app.v2.window_util import WindowUtil

# Disable Qt High DPI scaling
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
QApplication.setAttribute(Qt.ApplicationAttribute.AA_Use96Dpi)

LOGGER = create_logger(name='MainWindow')

WINDOW_W = 220
WINDOW_H = 120
START_POS_X = 10
START_POS_Y = 10


class AutoMainWindow(BaseApp):
    start_detection_signal = pyqtSignal()
    stop_detection_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.running = False
        self._drag_pos = None  # For dragging window
        self.settings = QSettings("data/config_v2.ini", QSettings.Format.IniFormat)
        self.INACTIVITY_DURATION = self.settings.value("Detection/InactivityDurationAutoStartSeconds", 60, type=int)
        self._last_mouse_pos = win32api.GetCursorPos()
        self._last_activity = QDateTime.currentDateTime() # app start is the user activity
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.inactivity_timer.start(10000)

        self.crash_report_timer = QTimer(self)
        self.crash_report_timer.timeout.connect(self.check_crash_report)
        self.crash_report_timer.start(60000)

        self.mouse_timer = QTimer(self)
        self.mouse_timer.timeout.connect(self.update_mouse_position)
        self.mouse_timer.start(1000)

        self.init_ui()
        
        self.start_detect_worker()
    
    def init_ui(self):

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(WINDOW_W, WINDOW_H)
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        screen_height = screen_geometry.height()
        screen_x = screen_geometry.x()
        screen_y = screen_geometry.y()
        # Position at bottom-left
        pos_x = screen_x + 10  # 10px from left
        pos_y = screen_y + screen_height - WINDOW_H - 10  # 10px from bottom
        self.move(pos_x, pos_y)

        central_widget = QWidget(self)
        central_widget.setObjectName("central_widget")
        central_widget.setStyleSheet("#central_widget { background-color: transparent; }")
        # layout = QHBoxLayout(self)
        layout = FlowLayout(central_widget)

        self.move_button = DraggableButton("🖱️", self)
        self.move_button.setToolTip("Drag to move the tool window")
        self.move_button.pressed.connect(self.on_start_drag)
        layout.addWidget(self.move_button)

        self.start_button = QPushButton(" ▶️ ", self)
        self.start_button.clicked.connect(self.on_start)
        layout.addWidget(self.start_button)

        self.pattern_button = QPushButton("✏️", self)
        self.pattern_button.setToolTip('create image pattern for detection')
        self.pattern_button.clicked.connect(self.on_show_pattern_creator_dialog)
        layout.addWidget(self.pattern_button)

        self.exit_button = QPushButton("❌", self)
        self.exit_button.clicked.connect(self.close)
        layout.addWidget(self.exit_button)

        self.status_label = QLabel("x,y: 0,0", self)
        layout.addWidget(self.status_label)

        self.color_label = QLabel("Curren color", self)
        layout.addWidget(self.color_label)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.apply_dark_theme()
        self.setup_tray_icon()
        self.setWindowTitle("vlv v2")
        self.setMouseTracking(True)


    def on_start(self):
        LOGGER.info("Start button clicked")
        self.running = not self.running

        if self.running:
            self.start_auto()
        else:
            LOGGER.info("pause auto detect")
            self.stop_detection_signal.emit()
            self.start_button.setText("▶️")

    def check_inactivity(self):
        current_pos = win32api.GetCursorPos()

        if current_pos != self._last_mouse_pos:
            self._last_mouse_pos = current_pos
            self._last_activity = QDateTime.currentDateTime()
            return
        if self.running or self._last_activity is None:
            return
        
        elapsed = self._last_activity.secsTo(QDateTime.currentDateTime())
        
        if elapsed >= self.INACTIVITY_DURATION:
            LOGGER.info(f"Auto-start due to {self.INACTIVITY_DURATION} inactivity.")
            self._last_activity = None  # reset to prevent repeated triggers
            self.running = True
            self.start_auto()

    def check_crash_report(self):
        crash_title = "MuMuPlayerCrashReporter"
        crash_windows = WindowUtil.find_game_windows(crash_title)
        crash_window = None
        if crash_windows is not None:
            crash_window = crash_windows[0]

        if crash_windows is not None:
            crash_detector = CrashDialogScenario(self.settings, self)
            crash_detector.resolve_crash(crash_window)

    def on_show_pattern_creator_dialog(self):
        dlg = PatternCreatorDialog(self)
        dlg.exec()
    
    def start_detect_worker(self):
        self.thread = QThread()
        self.detect_worker = DetectionWorkerV2(settings=self.settings)
        self.detect_worker.moveToThread(self.thread)

        # Ensure setup runs inside the worker thread
        self.thread.started.connect(lambda: QTimer.singleShot(0, self.detect_worker.setup))
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.detect_worker.deleteLater)

        # Wire UI signals to worker slots
        self.start_detection_signal.connect(self.detect_worker.start)
        self.stop_detection_signal.connect(self.detect_worker.stop)
        
        self.thread.start()

    def update_mouse_position(self):
        """
        Slot to be called by the QTimer.
        It gets the global mouse position and updates the status label.
        """
        # Get the global position of the cursor
        global_pos = QCursor.pos()
        x, y = global_pos.x(), global_pos.y()
        
        # Capture pixel color under mouse
        screen = QGuiApplication.primaryScreen()
        if screen:
            img = screen.grabWindow(0, x, y, 1, 1).toImage()
            pixel_color = QColor(img.pixel(0, 0))
            r, g, b = pixel_color.red(), pixel_color.green(), pixel_color.blue()
            rgb_str = f"({r},{g},{b})"

            # Show position and color
            self.status_label.setText(f'{x},{y}|{rgb_str}')

            # Apply tiny square + background color via CSS
            self.status_label.setStyleSheet(f"""
                background-color: black;
                color: white;
                padding: 10px;
                border: 2px solid white;
                border-radius: 6px;
            """)

            self.color_label.setStyleSheet(f"""
                background-color: {rgb_str};
            """)

    def start_auto(self):
        LOGGER.info("start auto detect")
        self.start_detection_signal.emit()
        self.start_button.setText("⏸️")

    def on_start_drag(self):
        self._drag_pos = QCursor.pos() - self.frameGeometry().topLeft()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def child_mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def child_mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def child_mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()
        
    def closeEvent(self, event):
        LOGGER.info("Closing window...")
        self.stop_detection_signal.emit()

        try:
            QMetaObject.invokeMethod(self.detect_worker, "cleanup", Qt.ConnectionType.BlockingQueuedConnection)
        except Exception as e:
            LOGGER.error(str(e))

        self.thread.quit()
        self.thread.wait()
        LOGGER.info("Finish closing")
        event.accept()
        QApplication.quit()
        LOGGER.info("App exit")


if __name__ == "__main__":
    AutoMainWindow.ensure_data_dir_exists()
    app = QApplication(sys.argv)
    window = AutoMainWindow()
    window.show()
    sys.exit(app.exec())