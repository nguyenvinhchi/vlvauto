from PyQt6.QtWidgets import (
    QPushButton
)

class DraggableButton(QPushButton):
    def mousePressEvent(self, event):
        self.parent().mousePressEvent(event)
        super().mousePressEvent(event)  # ensure button still registers click

    def mouseMoveEvent(self, event):
        self.parent().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.parent().mouseReleaseEvent(event)
        super().mouseReleaseEvent(event)  # finalize button click