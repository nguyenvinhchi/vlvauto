import os
import shutil
import sys
import win32api

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QPushButton
from PyQt6.QtGui import QIcon, QAction, QCursor
from PyQt6.QtCore import QThread, Qt, pyqtSignal, QTimer, pyqtSlot, QMetaObject, QSettings, QDateTime

from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QHBoxLayout
)

from app.detection_worker import DetectionWorker
from app.flow_layout import FlowLayout
from app.log_factory import create_logger
from app.pattern.create_pattern_dialog import PatternCreatorDialog
from app.resource_util import resource_path
from app.send_window_event import focus_window, simulate_click, simulate_mouse_move_around


# Disable Qt High DPI scaling
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_SCALE_FACTOR"] = "1"
QApplication.setAttribute(Qt.ApplicationAttribute.AA_Use96Dpi)

LOGGER = create_logger(name='MainWindow')

def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

def get_bundled_data_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'data')
    return os.path.join(get_exe_dir(), 'data')

def ensure_data_dir_exists():
    exe_dir = get_exe_dir()
    target_data_dir = os.path.join(exe_dir, 'data')

    if not os.path.exists(target_data_dir):
        print("📁 First-time run: copying bundled data...")
        bundled_data_dir = get_bundled_data_path()
        shutil.copytree(bundled_data_dir, target_data_dir)
        print(f"✅ Data directory created at: {target_data_dir}")
    else:
        print(f"📂 Data directory already exists at: {target_data_dir}")

    return target_data_dir

class DraggableButton(QPushButton):
    def mousePressEvent(self, event):
        self.parent().mousePressEvent(event)
        super().mousePressEvent(event)  # ensure button still registers click

    def mouseMoveEvent(self, event):
        self.parent().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.parent().mouseReleaseEvent(event)
        super().mouseReleaseEvent(event)  # finalize button click

WINDOW_W = 120
WINDOW_H = 70
START_POS_X = 10
START_POS_Y = 10

class AutoMainWindow(QWidget):
    start_detection_signal = pyqtSignal()
    stop_detection_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = False
        self._drag_pos = None  # For dragging window

        self.settings = QSettings("data/config.ini", QSettings.Format.IniFormat)
        self.INACTIVITY_DURATION = self.settings.value("Detection/InactivityDurationAutoStartSeconds", 60, type=int)
        self._last_mouse_pos = win32api.GetCursorPos()
        self._last_activity = QDateTime.currentDateTime() # app start is the user activity
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.inactivity_timer.start(10000)

        self.init_ui()
        
        self.start_detect_worker()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(WINDOW_W, WINDOW_H)
        self.move(START_POS_X, START_POS_Y)

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

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.apply_dark_theme()
        self.setup_tray_icon()
        self.setWindowTitle("VLV Auto")
        self.setMouseTracking(True)

        central_widget.mousePressEvent = self.child_mousePressEvent
        central_widget.mouseMoveEvent = self.child_mouseMoveEvent
        central_widget.mouseReleaseEvent = self.child_mouseReleaseEvent

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


    def start_detect_worker(self):
        self.thread = QThread()
        self.detect_worker = DetectionWorker(settings=self.settings)
        self.detect_worker.moveToThread(self.thread)
        self.detect_worker.solve_action_requested.connect(self.resolve_scenario)
        # Ensure setup runs inside the worker thread
        self.thread.started.connect(lambda: QTimer.singleShot(0, self.detect_worker.setup))
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.detect_worker.deleteLater)


        # Wire UI signals to worker slots
        self.start_detection_signal.connect(self.detect_worker.start)
        self.stop_detection_signal.connect(self.detect_worker.stop)
        
        self.thread.start()

    @pyqtSlot(str, int, tuple)
    def resolve_scenario(self, resolve_action: str, window_handle: int, points: tuple):
        LOGGER.info(f"Received resolve action request: {resolve_action}")
        focus_window(window_handle)
        if resolve_action in ('close_medicine_bag', 'close_medicine_shop'):
            x, y = points
            simulate_click(x, y)
        elif resolve_action == 'move_around_abit':
            x, y = points
            simulate_mouse_move_around(x, y)
        elif resolve_action == 'auto_login':
            self.do_login(points)
        elif resolve_action == 'close_login_warning':
            self.close_login_warning_dialog(points)
        else:
            LOGGER.info(f"{resolve_action} is not supported yet")

    def do_login(self, points: tuple):
        self._click_login_button(points)
    
    def close_login_warning_dialog(self, points: tuple):
        # 4rd point is confirm button which will close the warning
        simulate_click(*points[3])

    def _click_login_button(self, points: tuple, delay=7000):
        # Step 1: Click Login button
        simulate_click(*points[0])
        LOGGER.info("Clicked login button")
        # Step 2: After 3 seconds, click server icon
        QTimer.singleShot(delay, lambda: self._click_server_icon(points))

    def _click_server_icon(self, points: tuple, delay=5000):
        simulate_click(*points[1])
        LOGGER.info("Clicked server icon")

        # Step 3: After another 3 seconds, double-click avatar
        QTimer.singleShot(delay, lambda: self._double_click_avatar(points))

    def _double_click_avatar(self, points: tuple):
        simulate_click(*points[2], action='double_click')
        LOGGER.info("Double-clicked character avatar")

    def on_start(self):
        LOGGER.info("Start button clicked")
        self.running = not self.running

        if self.running:
            self.start_auto()
        else:
            LOGGER.info("pause auto detect")
            self.stop_detection_signal.emit()
            self.start_button.setText("▶️")

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

    def on_show_pattern_creator_dialog(self):
        dlg = PatternCreatorDialog(self)
        dlg.exec()

    def setup_tray_icon(self):
        tray_icon = QSystemTrayIcon(QIcon(resource_path("app/images/vlvauto-icon.png")))
        tray_menu = QMenu()
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(show_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        exit_action.triggered.connect(self.close)

        tray_menu.addAction(exit_action)

        tray_icon.setContextMenu(tray_menu)
        tray_icon.setToolTip("Game Auto Tool")
        tray_icon.show()
        self.tray_icon = tray_icon

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(43, 43, 43, 220);
                color: #f0f0f0;
                font-family: Arial;
                font-size: 10pt;
                border-radius: 10px;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #5a5a5a;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)


if __name__ == "__main__":
    ensure_data_dir_exists()
    app = QApplication(sys.argv)
    window = AutoMainWindow()
    window.show()
    sys.exit(app.exec())
