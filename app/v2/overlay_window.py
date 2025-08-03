from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen

class OverlayWindow(QWidget):
    """
    A transparent, frameless, always-on-top window used to draw debug overlays.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set window flags for frameless, always on top, and transparent background
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool # Tool hint makes it not appear in taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        # Allow clicks to pass through to the underlying window
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # self.setAttribute(Qt.WidgetAttribute.WA_TransparentForInput)
        
        # Set initial geometry to cover the entire screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self.points_to_draw = []
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide) # Hide after timeout

    def set_points(self, target_rect, points_data):
        """
        Sets the points to be drawn on the overlay.
        points_data is a list of tuples: [(screen_x, screen_y, r, g, b), ...]
        """
        self.points_to_draw = points_data
        self.target_rect = target_rect
        self.update() # Trigger a repaint
        self.show()
        self.timer.start(5000) # Show for 2 seconds

    def paintEvent(self, event):
        """
        Draws circles at the specified points.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.target_rect:
            x, y, w, h = self.target_rect

            rect_color = QColor(255, 144, 30, 220)
            pen = QPen(rect_color)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)

        # Optional: draw cross marks
        cross_color = QColor(250, 50, 0, 180)
        cross_pen = QPen(cross_color)
        cross_pen.setWidth(3)
        painter.setPen(cross_pen)

        for x, y in self.points_to_draw:
            radius = 8
            painter.drawLine(x - radius, y - radius, x + radius, y + radius)
            painter.drawLine(x - radius, y + radius, x + radius, y - radius)

        painter.end()