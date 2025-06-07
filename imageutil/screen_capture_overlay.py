import os
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QGuiApplication, QColor, QPixmap

class ScreenCaptureOverlay(QWidget):
    capture_done = pyqtSignal(QPixmap)
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self.temp_img_path = 'tmp/captured.png'
        os.makedirs(os.path.dirname(self.temp_img_path), exist_ok=True)
        # ✅ Capture desktop before showing overlay
        self.screen_pixmap = QApplication.primaryScreen().grabWindow(0)

        self.start_point = None
        self.end_point = None
        self.selection_rect = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            self.update()

    def mouseMoveEvent(self, event):
        if self.start_point:
            self.end_point = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.start_point:
            print("released")
            self.end_point = event.position().toPoint()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.capture_area()
            self.close()  # triggers destroyed and exits event loop

    def paintEvent(self, event):
        if self.screen_pixmap:
            painter = QPainter(self)
            painter.drawPixmap(self.rect(), self.screen_pixmap)
            if self.start_point and self.end_point:
                rect = QRect(self.start_point, self.end_point).normalized()
                painter.setPen(QPen(QColor(0, 120, 215), 2, Qt.PenStyle.SolidLine))
                painter.drawRect(rect)

    def capture_area(self):
        screen = QGuiApplication.primaryScreen()
        if screen and self.selection_rect:
            captured_pixmap = screen.grabWindow(0,
                                                self.selection_rect.x(),
                                                self.selection_rect.y(),
                                                self.selection_rect.width(),
                                                self.selection_rect.height())
            captured_pixmap.save(self.temp_img_path, 'PNG')

