from PyQt6.QtWidgets import (
    QApplication, QLabel, QVBoxLayout, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor

class OverlayWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0);")

        self.label = QLabel("Initializing...", self)
        self.label.setStyleSheet("color: lime; font-family: Consolas; font-size: 12pt; background-color: transparent;")
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.resize(500, 40)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(100)

    def update_status(self):
        pos = QCursor.pos()
        parent = self.parent()
        if parent:
            text = f"Mouse: ({pos.x()}, {pos.y()}) | {parent.status_text}"
            self.label.setText(text)
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - 500) // 2, screen.height() - 50)