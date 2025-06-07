from PyQt6.QtWidgets import QDialog, QLabel, QSlider, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
import cv2
import numpy as np
from PIL import Image
import io

class TransformColorDialog(QDialog):
    def __init__(self, image_path, lower, upper, save_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HSV Color Picker")
        self.image_path = image_path
        self.save_path = save_path
        self.lower = lower.copy()
        self.upper = upper.copy()

        self.image = cv2.imread(image_path)
        self.hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        self.filtered_image = None

        self.init_ui()
        self.update_preview()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.image_label = QLabel()
        layout.addWidget(self.image_label)

        grid = QGridLayout()
        self.sliders = {}

        labels = ["H_low", "S_low", "V_low", "H_high", "S_high", "V_high"]
        ranges = [(0, 179), (0, 255), (0, 255)] * 2  # HSV valid ranges
        values = self.lower + self.upper

        for i, (label, (rmin, rmax), val) in enumerate(zip(labels, ranges, values)):
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(rmin)
            slider.setMaximum(rmax)
            slider.setValue(val)
            slider.valueChanged.connect(self.update_preview)
            self.sliders[label] = slider

            grid.addWidget(QLabel(label), i // 3, (i % 3) * 2)
            grid.addWidget(slider, i // 3, (i % 3) * 2 + 1)

        layout.addLayout(grid)

        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_result)
        layout.addWidget(save_btn)

    def update_preview(self):
        self.lower = [self.sliders["H_low"].value(), self.sliders["S_low"].value(), self.sliders["V_low"].value()]
        self.upper = [self.sliders["H_high"].value(), self.sliders["S_high"].value(), self.sliders["V_high"].value()]

        mask = cv2.inRange(self.hsv, np.array(self.lower), np.array(self.upper))
        result = cv2.bitwise_and(self.image, self.image, mask=mask)

        # Convert BGR to RGB and show using QPixmap
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        self.filtered_image = result_rgb
        height, width, channel = result_rgb.shape
        bytes_per_line = 3 * width
        qimg = QImage(result_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(pixmap)

    def save_result(self):
        if self.filtered_image is not None:
            cv2.imwrite(self.save_path, cv2.cvtColor(self.filtered_image, cv2.COLOR_RGB2BGR))
            self.accept()
