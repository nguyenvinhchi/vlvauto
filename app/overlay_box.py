from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPainter, QColor, QBrush
import threading

class OverlayBox(QWidget):
    def __init__(self, x, y, width, height, duration=3000):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)  # Remove borders
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Make window background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)  # Ensure painting is opaque
        self.setGeometry(x, y, width, height)

        # To make it topmost
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)

        # Start auto close timer
        QTimer.singleShot(duration, self.close)  # Close the overlay after 'duration' ms

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set the brush color for the rectangle (Blue)
        painter.setBrush(QBrush(QColor(0, 0, 255)))
        painter.setPen(QColor(0, 0, 255))  # Blue color outline
        painter.drawRect(0, 0, self.width(), self.height())  # Draw a rectangle

    def start(self):
        self.show()

def show_overlay_box(x, y, width, height, duration=3000):
    def create_overlay():
        overlay = OverlayBox(x, y, width, height, duration)
        overlay.start()

    # Use a separate thread to run the overlay without blocking the main UI thread
    threading.Thread(target=create_overlay).start()
