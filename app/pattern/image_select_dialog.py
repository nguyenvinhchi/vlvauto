

import os
from PyQt6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout,
    QMessageBox, QSizePolicy, QScrollArea
)
from PyQt6.QtGui import QPixmap, QMouseEvent
from PyQt6.QtCore import Qt
import cv2

TMP_DIR = "data/tmp"
os.makedirs(TMP_DIR, exist_ok=True)

class ImageSelectDialog(QDialog):
    def __init__(self, parent, image_path, on_point_selected):
        super().__init__(parent)
        self.setWindowTitle("Select Points")
        self.image_path = image_path
        self.on_point_selected = on_point_selected
        self.points = []

        self.image_label = QLabel(self)
        self.pixmap = QPixmap(image_path)

        # Set fixed size and policies
        self.image_label.setPixmap(self.pixmap)
        print(self.pixmap.size())
        self.image_label.setScaledContents(False)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.image_label.setFixedSize(self.pixmap.size())
        self.image_label.mousePressEvent = self.on_mouse_click

        # Wrap label in a scroll area so dialog is still usable if image is large
        scroll = QScrollArea()
        scroll.setWidget(self.image_label)
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        layout = QVBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)

        # Optionally size dialog to image or constrain it
        self.resize(self.pixmap.width() + 20, self.pixmap.height() + 20)


    def on_mouse_click(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            x, y = pos.x(), pos.y()
            img = cv2.imread(self.image_path)
            b, g, r = img[y, x][:3]
            self.on_point_selected((x, y), (r, g, b))
            QMessageBox.information(self, "Point Added", f"Point at ({x}, {y}) with color RGB({r},{g},{b}) added.")