from PyQt6.QtWidgets import (
    QWidget, QLabel, QSlider, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QApplication, QGridLayout, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
import numpy as np
import cv2
import sys

class ImagePreview(QWidget):
    def __init__(self, pixmap: QPixmap):
        super().__init__()
        self.setWindowTitle("HSV Color transform")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
         # Convert pixmap to OpenCV image
        self.image = self.qpixmap_to_cv(pixmap)
        self.hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        self.filtered_image = None

        self.lower = [38, 206, 0]
        self.upper = [94, 255, 165]

        self.init_ui()
        self.update_preview()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Tabs for original & processed
        self.tab_widget = QTabWidget()
        self.original_label = QLabel()
        self.processed_label = QLabel()

        self.tab_widget.addTab(self.original_label, "Original")
        self.tab_widget.addTab(self.processed_label, "Processed")
        layout.addWidget(self.tab_widget)

        self.set_image_label(self.original_label, self.image)

        # HSV sliders
        self.sliders = {}
        grid = QGridLayout()
        labels = ["H_low", "S_low", "V_low", "H_high", "S_high", "V_high"]
        for i, label in enumerate(labels):
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(self.lower[i] if i < 3 else self.upper[i - 3])
            slider.valueChanged.connect(self.update_preview)
            self.sliders[label] = slider
            grid.addWidget(QLabel(label), i, 0)
            grid.addWidget(slider, i, 1)
        layout.addLayout(grid)

        # Save button
        save_button = QPushButton("💾 Save Transformed Image")
        save_button.clicked.connect(self.save_result)
        layout.addWidget(save_button)

    def set_image_label(self, label: QLabel, image: np.ndarray):
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_preview(self):
        self.lower = [self.sliders["H_low"].value(),
                      self.sliders["S_low"].value(),
                      self.sliders["V_low"].value()]
        self.upper = [self.sliders["H_high"].value(),
                      self.sliders["S_high"].value(),
                      self.sliders["V_high"].value()]

        mask = cv2.inRange(self.hsv, np.array(self.lower), np.array(self.upper))
        mask_inv = cv2.bitwise_not(mask)
        black_bg = np.zeros_like(self.image)
        result = cv2.bitwise_and(self.image, self.image, mask=mask) + \
                 cv2.bitwise_and(black_bg, black_bg, mask=mask_inv)

        self.filtered_image = result
        self.set_image_label(self.processed_label, result)

    def save_result(self):
        if self.filtered_image is not None:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Transformed Image", "", "PNG Files (*.png);;All Files (*)")
            if path:
                cv2.imwrite(path, self.filtered_image)

    def qpixmap_to_cv(self, pixmap: QPixmap) -> np.ndarray:
        """Convert QPixmap to OpenCV BGR image."""
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
        width = image.width()
        height = image.height()
        ptr = image.bits()
        ptr.setsize(image.sizeInBytes())
        arr = np.array(ptr, dtype=np.uint8).reshape((height, width, 4))
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    
# # For testing
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     img = cv2.imread("your_image_file.png")  # Replace with your test image
#     window = ImagePreview(img)
#     window.show()
#     sys.exit(app.exec())
